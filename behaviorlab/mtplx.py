"""MTPLX-specific local artifact, context and effective-request verification."""

import base64
import hashlib
from pathlib import Path
import subprocess

from .common import canonical, fingerprint, read_json, require, sha256

PARAMETERS = {"temperature", "top_p", "top_k", "max_tokens", "presence_penalty", "frequency_penalty",
              "enable_thinking", "reasoning_effort", "generation_mode", "depth", "metadata"}


def validate_artifact(row):
    from .protocol import HEX
    from .backends import validate_endpoint, LOOPBACK
    artifact = row["artifact"]
    fields = {"kind", "model_path", "files", "runtime_files", "endpoint", "tokenizer_python",
              "expected_health", "expected_settings", "capture_dir"}
    require(isinstance(artifact, dict) and set(artifact) == fields and artifact["kind"] == "mtplx-local-files/1",
            "Invalid MTPLX artifact specification")
    require(validate_endpoint(artifact["endpoint"]).hostname in LOOPBACK, "MTPLX verification is local only")
    require(row["location"] == "local", "MTPLX profile is local only")
    if row["backend"] == "mtplx":
        actual, expected = validate_endpoint(row["endpoint"]), validate_endpoint(artifact["endpoint"])
        require(actual.hostname in LOOPBACK and actual.scheme == expected.scheme and actual.port == expected.port
                and actual.path.rstrip("/") == expected.path.rstrip("/") + "/v1",
                "MTPLX generation endpoint differs from the verified engine")
    for name in ("model_path", "tokenizer_python", "capture_dir"):
        require(isinstance(artifact[name], str) and Path(artifact[name]).is_absolute(), "MTPLX paths must be absolute")
    require(isinstance(artifact["files"], list) and artifact["files"], "Missing artifact files")
    names = set()
    for f in artifact["files"]:
        require(set(f) == {"name", "bytes", "sha256"} and isinstance(f["name"], str)
                and Path(f["name"]).name == f["name"] and f["name"] not in (".", ".."), "Invalid artifact file name")
        require(f["name"] not in names, "Duplicate artifact file")
        names.add(f["name"])
        require(type(f["bytes"]) is int and f["bytes"] > 0 and bool(HEX.fullmatch(f["sha256"])), "Invalid artifact fingerprint")
    require({"tokenizer.json", "tokenizer_config.json", "config.json", "chat_template.jinja", "mtplx_runtime.json"} <= names
            and any(n.endswith(".safetensors") for n in names), "Incomplete MTPLX artifact manifest")
    require(row["digest"] == fingerprint(artifact["files"]), "Artifact manifest digest mismatch")
    require(isinstance(artifact["runtime_files"], list) and artifact["runtime_files"], "Missing runtime source provenance")
    for f in artifact["runtime_files"]:
        require(set(f) == {"path", "sha256"} and Path(f["path"]).is_absolute() and bool(HEX.fullmatch(f["sha256"])),
                "Invalid runtime file fingerprint")
    health = artifact["expected_health"]
    require(isinstance(health, dict) and health.get("model") == row["tag"] and
            health.get("model_path") == artifact["model_path"] and
            health.get("preserve_thinking") == "off" and health.get("strip_assistant_reasoning_history") is True,
            "Declare the model and trace-withholding policy in health requirements")
    require(type(health.get("context_window")) is int and health["context_window"] > 0, "Missing context limit")
    require(isinstance(artifact["expected_settings"], dict) and artifact["expected_settings"], "Missing effective settings")


def validate_settings(settings, row):
    require(set(settings) == PARAMETERS, "MTPLX requires explicit supported settings")
    require(type(settings["enable_thinking"]) is bool, "Missing explicit thinking mode")
    require(settings["reasoning_effort"] in ("low", "medium", "xhigh"), "Unsupported Qwen3.8 reasoning effort")
    require(settings["generation_mode"] in ("mtp", "ar"), "Invalid generation mode")
    require(type(settings["depth"]) is int and 1 <= settings["depth"] <= 3, "Unqualified MTP depth")
    require(type(settings["top_k"]) is int and settings["top_k"] >= 0, "Invalid top_k")
    require(type(settings["max_tokens"]) is int and 1 <= settings["max_tokens"] < row["artifact"]["expected_health"]["context_window"],
            "Invalid output token reserve")
    for name in ("temperature", "top_p", "presence_penalty", "frequency_penalty"):
        require(type(settings[name]) in (int, float), "Invalid sampling number")
    require(settings["temperature"] >= 0 and 0 < settings["top_p"] <= 1, "Invalid sampling range")
    require(settings["metadata"] in ({"cache_mode": "off"}, {"cache_mode": "auto"}), "Specify cache mode off or auto only")
    require(set(settings) | {"seed"} <= set(row["capabilities"]), "Unsupported MTPLX control")
    canonical(settings)


def nested(data, key):
    for name in key.split("."):
        require(isinstance(data, dict) and name in data, "Missing observed field " + key)
        data = data[name]
    return data


def verify_files(artifact, digest, cache):
    root = Path(artifact["model_path"])
    relevant = {p.name for p in root.iterdir() if p.suffix in (".json", ".jinja", ".safetensors")}
    require(relevant == {r["name"] for r in artifact["files"]}, "Artifact file inventory drift")
    paths = [(root / r["name"], r["sha256"], r["bytes"]) for r in artifact["files"]]
    paths += [(Path(r["path"]), r["sha256"], None) for r in artifact["runtime_files"]]
    signatures = []
    for path, expected, size in paths:
        stat = path.stat()
        require(size is None or stat.st_size == size, "Artifact file size drift: " + path.name)
        signatures.append((str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))
    cache_key = fingerprint({"artifact": digest, "runtime": artifact["runtime_files"], "stats": signatures})
    if cache_key not in cache:
        for path, expected, size in paths:
            h = hashlib.sha256()
            with path.open("rb") as f:
                for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
                    h.update(block)
            require(h.hexdigest() == expected, "Artifact or runtime content drift: " + path.name)
        after = []
        for path, _, _ in paths:
            stat = path.stat()
            after.append((str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))
        require(after == signatures, "Artifact changed during verification")
        cache.clear()
        cache[cache_key] = True
    return {"artifact_manifest_sha256": digest, "content_hash_verified": True,
            "verification_cache_key": cache_key, "file_count": len(paths)}


def verify(model, cache):
    from .backends import json_request
    row = read_json(model.metadata_json)
    artifact = row["artifact"]
    evidence = verify_files(artifact, model.digest, cache)
    health = json_request(artifact["endpoint"], "/health")
    settings = json_request(artifact["endpoint"], "/v1/mtplx/settings")
    for source, expected in ((health, artifact["expected_health"]), (settings, artifact["expected_settings"])):
        for key, value in expected.items():
            require(nested(source, key) == value, "MTPLX effective setting drift: " + key)
    evidence.update(health={k: nested(health, k) for k in artifact["expected_health"]},
                    settings={k: nested(settings, k) for k in artifact["expected_settings"]},
                    server_pid=health["startup"]["pid"], server_started_at=health["startup"].get("started_at"))
    return evidence


def preflight(payload, model):
    artifact = read_json(model.metadata_json)["artifact"]
    cap = artifact["expected_settings"].get("max_response_tokens")
    require(cap is None or payload["max_tokens"] <= cap,
            "Requested output allowance exceeds MTPLX server cap; update the server and registry before generation")
    helper = Path(__file__).with_name("mtplx_tokenizer.py")
    result = subprocess.run([artifact["tokenizer_python"], str(helper)],
                            input=canonical({"model_path": artifact["model_path"], "request": payload}),
                            text=True, capture_output=True, timeout=60)
    require(result.returncode == 0, "Local MTPLX tokenizer failed; no generation sent")
    rendered = read_json(result.stdout)
    ids = rendered["token_ids"]
    require(isinstance(ids, list) and ids and all(type(x) is int and x >= 0 for x in ids), "Invalid token IDs")
    limit = artifact["expected_health"]["context_window"]
    require(len(ids) + payload["max_tokens"] <= limit, "Rendered input plus reserved output exceeds context")
    return {"renderer": "local-hf-template/1", "input_tokens": len(ids), "reserved_output_tokens": payload["max_tokens"],
            "context_window": limit, "prompt_token_ids_sha256": fingerprint(ids),
            "rendered_text_sha256": sha256(rendered["rendered_text"].encode())}


def capture_response(raw, model, preflight_evidence):
    """Copy this request's engine capture into durable response evidence."""
    data = read_json(raw)
    response_id = data.get("id")
    require(isinstance(response_id, str) and response_id, "Missing MTPLX response ID")
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in response_id)[:80]
    directory = Path(read_json(model.metadata_json)["artifact"]["capture_dir"])
    files = list(directory.glob("req-*-" + safe_id + ".json"))
    require(len(files) == 1, "Missing or ambiguous MTPLX dispatch capture")
    content = files[0].read_bytes()
    capture = read_json(content.decode())
    require(capture.get("request_id") == response_id, "Capture belongs to a different request")
    return {"preflight": preflight_evidence, "capture": capture, "capture_sha256": sha256(content),
            "capture_bytes_base64": base64.b64encode(content).decode()}


def validate_response_evidence(data, payload, evidence, strict_effective=True):
    require(isinstance(evidence, dict), "Missing MTPLX dispatch evidence")
    pre = evidence["preflight"]
    c = evidence["capture"]
    # The first two identification smoke calls retained the original capture
    # hash and parsed object; subsequent calls also embed the original bytes.
    if "capture_bytes_base64" in evidence:
        original = base64.b64decode(evidence["capture_bytes_base64"], validate=True)
        require(sha256(original) == evidence["capture_sha256"] and read_json(original.decode()) == c,
                "Engine capture bytes differ from saved object/hash")
    require(c["request_id"] == data["id"] and c["model_id"] == payload["model"], "Dispatch identity mismatch")
    require(c.get("phase") == "completed", "MTPLX capture has no completed outcome")
    require(c["prompt_len"] == pre["input_tokens"] and fingerprint(c["prompt_token_ids"]) == pre["prompt_token_ids_sha256"],
            "Engine's rendered history differs from the supplied message template")
    for key in ("max_tokens", "temperature", "top_p", "top_k", "presence_penalty", "frequency_penalty", "generation_mode", "depth"):
        require(c[key] == payload[key], "MTPLX changed requested control: " + key)
    require(c["requested_seed"] == payload["seed"], "MTPLX changed requested seed")
    obs, outcome = c["observability"], c["outcome"]
    require(obs["request_enable_thinking"] is payload["enable_thinking"], "MTPLX changed thinking mode")
    if payload["enable_thinking"]:
        require(obs["request_reasoning_effort"] == payload["reasoning_effort"], "MTPLX changed reasoning effort")
    require(obs["preserve_thinking_effective"] is False and obs["strip_assistant_reasoning_history"] is True,
            "Reasoning history retention changed")
    require(obs["request_session_bank_bypass"] is (payload["metadata"]["cache_mode"] == "off"),
            "MTPLX changed requested cache policy")
    require(outcome["resolved_seed"] == payload["seed"] and outcome["attempts"] == 1 and outcome["blank_retries"] == 0,
            "Hidden retry or resolved seed drift")
    require(data["usage"]["prompt_tokens"] == c["prompt_len"] and
            data["usage"]["completion_tokens"] == outcome["completion_tokens"] and
            data["choices"][0]["finish_reason"] == outcome["finish_reason"], "Usage or finish reason differs from capture")
    if strict_effective:
        # Dispatch capture precedes the generator's final limit resolution.
        # Its max_tokens can therefore be the request even when a server cap
        # reduces the effective allowance. The response reports that resolution.
        stats = data["mtplx_stats"]
        require(stats["effective_max_tokens"] == payload["max_tokens"] and
                not stats["server_cap_applied"] and not stats["context_cap_applied"],
                "MTPLX effective output allowance differs from request")
        for key in ("temperature", "top_p", "top_k"):
            require(stats["effective_" + key] == payload[key], "MTPLX effective sampler differs: " + key)
        for key in ("presence_penalty", "frequency_penalty"):
            require(obs["effective_" + key] == payload[key], "MTPLX effective penalty differs: " + key)
        require(stats["generation_mode"] == payload["generation_mode"], "MTPLX effective generation mode differs")
        if payload["generation_mode"] == "mtp":
            require(stats["mtp_depth"] == payload["depth"], "MTPLX effective MTP depth differs")
        require(stats["server_seed"] == payload["seed"] and stats["server_attempts"] == 1 and
                stats["server_blank_retries"] == 0, "MTPLX final seed or retry count differs")
        if payload["metadata"]["cache_mode"] == "off":
            require(data["usage"]["prompt_tokens_details"]["cached_tokens"] == 0,
                    "MTPLX reused cached tokens despite bypass")
