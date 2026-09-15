"""Explicit HTTP adapters. Credentials are environment values, never evidence.

Registry v2 separates a service identity from an optional local weight artifact.
The runner currently permits local engineering only; cloud budgeting is pending.
"""

import base64
from dataclasses import dataclass
import os
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from .common import canonical, fingerprint, read_json, require, sha256, timestamp

LIVE_BACKEND = "http-backends/1"
LIVE_PARSER = "http-chat/3"
LIVE_PARSERS = {"http-chat/1", "http-chat/2", LIVE_PARSER}
LIVE_DATA_CLASS = "local_engineering_inference_not_research_campaign"
OLLAMA_OPTIONS = {"num_ctx", "num_predict", "temperature", "top_p", "top_k", "min_p",
                  "repeat_penalty", "repeat_last_n", "presence_penalty", "frequency_penalty"}
CHAT_PARAMETERS = {"temperature", "top_p", "max_tokens", "max_completion_tokens", "presence_penalty",
                   "frequency_penalty", "stop", "reasoning_effort", "reasoning", "provider"}
LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def native_controls(row):
    return row["backend"] == "ollama" or row["backend"] == "webui" and row["artifact"] is not None


def mtplx_controls(row):
    return row["backend"] in ("mtplx", "webui-mtplx")


def ollama_context_controls(row):
    return row["backend"] == "ollama" and isinstance(row.get("artifact"), dict) and "qualification" in row["artifact"]


def validate_endpoint(url):
    require(isinstance(url, str), "Endpoint must be a URL")
    p = urlsplit(url)
    require(p.scheme in ("http", "https") and p.hostname and not p.username and not p.password
            and not p.query and not p.fragment, "Endpoint must not contain credentials or query parameters")
    require(p.scheme == "https" or p.hostname in LOOPBACK, "HTTP is supported only on loopback")
    return p


def validate_model(row):
    from .protocol import HEX
    required = {"label", "tag", "digest", "backend", "endpoint", "location", "auth_env",
                "capabilities", "reported_models", "server_version", "artifact"}
    require(set(row) == required, "Unexpected or missing service identity fields")
    require(row["backend"] in ("ollama", "openai", "webui", "mtplx", "webui-mtplx"), "Unknown backend")
    p = validate_endpoint(row["endpoint"])
    require(row["location"] in ("local", "remote"), "Unknown service location")
    if row["location"] == "local":
        require(p.hostname in LOOPBACK, "Local engineering requires a loopback service")
    require(row["auth_env"] is None or bool(re.fullmatch(r"[A-Z][A-Z0-9_]*", row["auth_env"])),
            "Use an environment variable name for authentication")
    require(isinstance(row["server_version"], str) and row["server_version"], "Record server version or explicitly 'unknown'")
    require(isinstance(row["reported_models"], list) and row["reported_models"] and
            all(isinstance(x, str) and x for x in row["reported_models"]), "Declare accepted response model IDs")
    allowed = OLLAMA_OPTIONS | {"think", "keep_alive", "seed"} if native_controls(row) else CHAT_PARAMETERS | {"seed"}
    if row["backend"] == "ollama":
        allowed |= {"truncate", "shift"}
    if mtplx_controls(row):
        from .mtplx import PARAMETERS
        allowed = PARAMETERS | {"seed"}
    caps = row["capabilities"]
    require(isinstance(caps, list) and len(set(caps)) == len(caps) and set(caps) <= allowed,
            "Unknown or duplicate adapter capabilities")
    artifact = row["artifact"]
    if mtplx_controls(row):
        from .mtplx import validate_artifact
        validate_artifact(row)
        return
    if artifact is not None:
        fields = {"endpoint", "tag", "template", "template_sha256", "parameters_sha256", "server_version"}
        require(set(artifact) == fields or row["backend"] == "ollama" and set(artifact) == fields | {"qualification"},
                "Invalid artifact provenance fields")
        require(validate_endpoint(artifact["endpoint"]).hostname in LOOPBACK, "Artifact verification must be local")
        require(isinstance(row["digest"], str) and bool(HEX.fullmatch(row["digest"])), "Local artifact requires its actual digest")
        require(isinstance(artifact["template"], str) and sha256(artifact["template"].encode()) == artifact["template_sha256"],
                "Archived template hash mismatch")
        require(bool(HEX.fullmatch(artifact["parameters_sha256"])), "Missing model defaults fingerprint")
    else:
        require(row["digest"] is None, "Unobserved weight digests must be null")
    if row["backend"] == "ollama":
        require(artifact is not None and artifact["tag"] == row["tag"] and
                artifact["endpoint"] == row["endpoint"], "Native Ollama requires verifiable artifact provenance")
    if ollama_context_controls(row):
        from .ollama_context import validate_artifact
        validate_artifact(row)


def validate_settings(settings, registry):
    from .protocol import Protocol
    require(set(settings) == {"by_model"} and set(settings["by_model"]) == {m.label for m in registry.models},
            "Declare request parameters for every model")
    for model in registry.models:
        row = read_json(model.metadata_json)
        require(row["location"] == "local", "Cloud execution requires a future explicitly budgeted protocol")
        s = settings["by_model"][model.label]
        require(isinstance(s, dict), "Invalid model settings")
        caps = set(row["capabilities"])
        if mtplx_controls(row):
            from .mtplx import validate_settings as validate_mtplx_settings
            validate_mtplx_settings(s, row)
        elif native_controls(row):
            extra = set(s) & {"truncate", "shift"}
            Protocol.validate_ollama_settings({k: v for k, v in s.items() if k not in extra})
            require(set(s["options"]) | {"think", "keep_alive", "seed"} | extra <= caps, "Unsupported native control")
            require(not extra or row["backend"] == "ollama" and all(s[k] is False for k in extra),
                    "Only explicit native truncation/shift disable is qualified")
            if ollama_context_controls(row):
                require(extra == {"truncate", "shift"} and s["think"] is False,
                        "Qualified Ollama requires thinking, truncation and context shifting disabled")
        else:
            require(set(s) <= CHAT_PARAMETERS and set(s) <= caps, "Unsupported chat control; no silent dropping")
            limits = set(s) & {"max_tokens", "max_completion_tokens"}
            require(len(limits) == 1, "Specify exactly one output token limit")
            require(type(s[next(iter(limits))]) is int and 1 <= s[next(iter(limits))] <= 100000,
                    "Invalid output token limit")
            for key in ("temperature", "top_p", "presence_penalty", "frequency_penalty"):
                if key in s:
                    require(type(s[key]) in (int, float), "Invalid sampling number")
            require(s.get("temperature", 0) >= 0 and 0 <= s.get("top_p", 1) <= 1, "Invalid sampling range")
            if "stop" in s:
                require(isinstance(s["stop"], list) and all(isinstance(x, str) and x for x in s["stop"]), "Invalid stops")
            if "reasoning_effort" in s:
                require(s["reasoning_effort"] in ("none", "minimal", "low", "medium", "high"), "Unknown reasoning control")
            if "reasoning" in s:
                require(s["reasoning"] == {"enabled": False}, "Only explicit reasoning disable is implemented here")
            if "provider" in s:
                p = s["provider"]
                require(set(p) == {"only", "allow_fallbacks", "require_parameters"} and
                        isinstance(p["only"], list) and len(p["only"]) == 1 and isinstance(p["only"][0], str) and
                        p["allow_fallbacks"] is False and p["require_parameters"] is True,
                        "Provider routing must name one provider, forbid fallback, and require parameter support")
    canonical(settings)  # rejects non-finite numbers


def prepare_request(model, settings, messages, seed):
    row = read_json(model.metadata_json)
    payload = read_json(canonical(settings))
    payload.update(model=model.tag, messages=messages, stream=False)
    if native_controls(row):
        payload["options"]["seed"] = seed
    elif "seed" in row["capabilities"]:
        payload["seed"] = seed
    if row["backend"] in ("webui", "webui-mtplx"):
        if native_controls(row):
            payload["options"]["think"] = payload.pop("think")
            payload["options"]["keep_alive"] = payload.pop("keep_alive")
        payload.update(features={"memory": False, "web_search": False, "code_interpreter": False},
                       background_tasks={"title_generation": False, "tags_generation": False,
                                         "follow_up_generation": False})
    return payload


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class WireResponse:
    raw: str
    evidence: dict


def http_request(endpoint, path, payload=None, token=None, timeout=120):
    """Return HTTP errors as evidence too. Never follow redirects with credentials."""
    validate_endpoint(endpoint)
    require(path.startswith("/") and not path.startswith("//"), "Invalid API path")
    headers = {"Accept": "application/json", "Accept-Encoding": "identity"}
    body = None
    if payload is not None:
        body = canonical(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        require("\n" not in token and "\r" not in token, "Invalid credential")
        headers["Authorization"] = "Bearer " + token
    request = Request(endpoint.rstrip("/") + path, data=body, headers=headers)
    start = timestamp()
    clock = time.monotonic()
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(request, timeout=timeout)
    except HTTPError as exc:
        response = exc
    with response:
        data = response.read()
        evidence = {"http_status": response.status, "started_at": start, "finished_at": timestamp(),
                    "elapsed_seconds": time.monotonic()-clock,
                    "timeout_seconds": timeout,
                    "response_sha256": sha256(data), "response_bytes_base64": base64.b64encode(data).decode(),
                    "headers": {k.lower(): v for k, v in response.headers.items()
                                if k.lower() in ("content-type", "x-request-id", "request-id", "date")}}
    return WireResponse(data.decode("utf-8", errors="replace"), evidence)


def json_request(endpoint, path, payload=None, token=None):
    response = http_request(endpoint, path, payload, token)
    require(response.evidence["http_status"] == 200, "API returned HTTP " + str(response.evidence["http_status"]))
    return read_json(response.raw)


class HTTPBackend:
    identity = LIVE_BACKEND

    def __init__(self, request_timeout=120):
        require(type(request_timeout) in (int, float) and 0 < request_timeout <= 3600,
                "HTTP request timeout must be between zero and 3600 seconds")
        self.request_timeout = request_timeout
        self._artifact_cache = {}
        self._preflight = {}

    def preflight(self, payload, model):
        row = read_json(model.metadata_json)
        if ollama_context_controls(row):
            from .ollama_context import preflight
        elif mtplx_controls(row):
            from .mtplx import preflight
        else:
            return None
        evidence = preflight(payload, model)
        self._preflight[fingerprint(payload)] = evidence
        return evidence

    def token(self, row):
        name = row["auth_env"]
        if name:
            require(bool(os.environ.get(name)), "Set credential environment variable " + name)
            return os.environ[name]
        return None

    def verify(self, model):
        row = read_json(model.metadata_json)
        observation = {"observed_at": timestamp(), "endpoint": row["endpoint"], "backend": row["backend"],
                       "weight_digest": None, "effective_provider_request": "not_observed",
                       "http_timeout_seconds": self.request_timeout}
        artifact = row["artifact"]
        if mtplx_controls(row):
            from .mtplx import verify
            observation["mtplx"] = verify(model, self._artifact_cache)
            observation["weight_digest"] = model.digest
        elif artifact:
            if ollama_context_controls(row):
                from .ollama_context import verify_files
                observation["ollama_files"] = verify_files(model, self._artifact_cache)
            tags = json_request(artifact["endpoint"], "/api/tags")["models"]
            matches = [r for r in tags if r["name"] == artifact["tag"]]
            require(len(matches) == 1 and matches[0]["digest"] == model.digest, "Model artifact drift")
            show = json_request(artifact["endpoint"], "/api/show", {"model": artifact["tag"]})
            require(sha256(show.get("template", "").encode()) == artifact["template_sha256"], "Model template drift")
            observed_parameters_hash = sha256(show.get("parameters", "").encode())
            if ollama_context_controls(row):
                from .ollama_context import parameter_values
                values = parameter_values(show.get("parameters", ""))
                require(values == artifact["qualification"]["parameters"], "Model defaults drift")
                observation.update(parameters_text=show.get("parameters", ""),
                                   parameters_values_sha256=fingerprint(values))
            else:
                require(observed_parameters_hash == artifact["parameters_sha256"], "Model defaults drift")
            version = json_request(artifact["endpoint"], "/api/version")["version"]
            require(version == artifact["server_version"], "Ollama server version drift")
            observation.update(weight_digest=model.digest, template_sha256=artifact["template_sha256"],
                               parameters_sha256=observed_parameters_hash, artifact_server_version=version)
        if row["backend"] in ("webui", "webui-mtplx"):
            version = json_request(row["endpoint"], "/api/version")["version"]
            require(version == row["server_version"], "WebUI server version drift")
            models = json_request(row["endpoint"], "/api/models", token=self.token(row))["data"]
            selected = [r for r in models if r["id"] == model.tag]
            require(len(selected) == 1, "Model absent or ambiguous in authenticated WebUI catalog")
            selected = selected[0]
            require(not selected.get("pipe") and not selected.get("filters"), "Function/filter route is not qualified")
            if row["backend"] == "webui-mtplx":
                require(selected.get("owned_by") == "openai" and selected.get("urlIdx") is not None,
                        "MTPLX must be an ordinary connected OpenAI-compatible model")
                # Read configuration only to resolve this route. Never retain
                # keys, headers or the complete configuration in evidence.
                config = json_request(row["endpoint"], "/openai/config", token=self.token(row))
                upstream = config["OPENAI_API_BASE_URLS"][selected["urlIdx"]]
                actual, expected = validate_endpoint(upstream), validate_endpoint(artifact["endpoint"])
                require(actual.hostname in LOOPBACK and expected.hostname in LOOPBACK and
                        actual.scheme == expected.scheme and actual.port == expected.port and
                        actual.path.rstrip("/") == expected.path.rstrip("/") + "/v1",
                        "WebUI MTPLX route differs from the verified local engine")
                observation["gateway_upstream"] = upstream
            elif row["location"] == "local":
                require(artifact is not None and selected.get("owned_by") == "ollama" and
                        selected.get("ollama", {}).get("digest") == model.digest,
                        "Local gateway campaigns currently require an identified Ollama artifact")
            observation["gateway_version"] = version
            observation["catalog_route"] = {k: selected.get(k) for k in ("id", "owned_by", "connection_type", "filters", "urlIdx")}
        elif row["backend"] in ("openai", "mtplx"):
            models = json_request(row["endpoint"], "/models", token=self.token(row))["data"]
            require(any(r["id"] == model.tag for r in models), "Model absent from service catalog")
        return observation

    def generate(self, payload, model):
        row = read_json(model.metadata_json)
        path = {"ollama": "/api/chat", "openai": "/chat/completions", "webui": "/api/chat/completions",
                "mtplx": "/chat/completions", "webui-mtplx": "/api/chat/completions"}[row["backend"]]
        response = http_request(row["endpoint"], path, payload, self.token(row), timeout=self.request_timeout)
        if ollama_context_controls(row):
            response.evidence["ollama_context"] = self._preflight.pop(fingerprint(payload), None)
        if mtplx_controls(row):
            # Never discard a received response if supplemental capture fails.
            try:
                from .mtplx import capture_response
                response.evidence["mtplx"] = capture_response(response.raw, model, self._preflight.pop(fingerprint(payload)))
            except Exception as exc:
                response.evidence["mtplx_capture_error"] = type(exc).__name__
        return response


def parse_live(raw, payload, model, transport, parser_version=LIVE_PARSER):
    require(parser_version in LIVE_PARSERS, "Unknown live parser version")
    row = read_json(model.metadata_json)
    require(transport is not None, "Missing HTTP evidence")
    data_bytes = base64.b64decode(transport["response_bytes_base64"], validate=True)
    require(sha256(data_bytes) == transport["response_sha256"] and data_bytes.decode("utf-8", errors="replace") == raw,
            "Response bytes differ from saved text/hash")
    require(200 <= transport["http_status"] < 300, "HTTP " + str(transport["http_status"]))
    require(data_bytes.decode("utf-8") == raw, "Response is not valid UTF-8")
    if row["backend"] == "ollama":
        from .runner import parse_response
        if ollama_context_controls(row):
            from .ollama_context import validate_response_evidence
            require(parser_version == "http-chat/3", "Qualified Ollama requires parser 3")
            validate_response_evidence(read_json(raw), payload, transport.get("ollama_context"), model)
        return parse_response(raw, payload)
    data = read_json(raw)
    require(isinstance(data, dict) and data.get("model") in row["reported_models"], "Unexpected reported model")
    if mtplx_controls(row):
        from .mtplx import validate_response_evidence
        validate_response_evidence(data, payload, transport.get("mtplx"),
                                   strict_effective=parser_version != "http-chat/1")
    choices = data.get("choices")
    require(isinstance(choices, list) and len(choices) == 1, "Expected one chat choice")
    choice = choices[0]
    message = choice.get("message")
    require(isinstance(message, dict) and message.get("role") == "assistant", "Missing assistant message")
    require(isinstance(message.get("content"), str), "Missing text content")
    require(not message.get("tool_calls") and not message.get("function_call"), "Unexpected tool request")
    require(choice.get("finish_reason") in ("stop", "length"), "Unknown finish reason")
    traces = {k: message[k] for k in ("reasoning", "reasoning_content", "reasoning_details", "thinking") if k in message}
    # Traces always remain in raw evidence, never in either participant's next input.
    disabled = (payload.get("reasoning_effort") == "none" or payload.get("reasoning", {}).get("enabled") is False
                or payload.get("options", {}).get("think") is False or payload.get("enable_thinking") is False)
    reason = "output_cap" if choice["finish_reason"] == "length" else None
    if disabled and any(traces.values()):
        reason = "unexpected_thinking_output"
    return {"content": message["content"], "thinking": canonical(traces) if traces else None,
            "invalid_reason": reason}
