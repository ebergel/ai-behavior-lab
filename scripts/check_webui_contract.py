"""Inspect WebUI's outgoing JSON through an already configured, idle local port.

No connection settings are changed. The temporary receiver advertises only a
unique test model, refuses other model IDs, and never reads/logs auth headers.
Run explicitly: python3 -m scripts.check_webui_contract --port 8000 --output ...
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

from behaviorlab.backends import http_request, json_request
from behaviorlab.common import canonical, fingerprint, timestamp


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--endpoint", default="http://127.0.0.1:8080")
    p.add_argument("--token-file", default="workspace/private/webui-token")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError("Use a new output path for every check")
    token = Path(args.token_file).read_text().strip()
    model = "behaviorlab-contract-" + str(time.time_ns())
    captures = []
    class Receiver(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def send(self, status, value):
            body = canonical(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            if self.path.rstrip("/") == "/v1/models":
                self.send(200, {"object": "list", "data": [{"id": model, "object": "model", "owned_by": "behaviorlab-test"}]})
            else:
                self.send(404, {"error": "Unknown test route"})
        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            data = json.loads(raw)
            if self.path != "/v1/chat/completions" or data.get("model") != model:
                self.send(404, {"error": "Only the unique contract model is served"})
                return
            captures.append({"raw_body": raw, "json": data})
            self.send(200, {"id": "contract-response", "object": "chat.completion", "created": int(time.time()),
                           "model": model, "choices": [{"index": 0, "finish_reason": "stop",
                           "message": {"role": "assistant", "content": "SYNTHETIC CONTRACT RESPONSE"}}],
                           "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})
    # Fails if a real service is already listening. Never stop or replace it.
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Receiver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    report = {"at": timestamp(), "data_class": "synthetic_gateway_contract_check", "model": model, "checks": []}
    try:
        models = json_request(args.endpoint, "/api/models?refresh=true", token=token)["data"]
        assert any(x["id"] == model for x in models), "Configured WebUI connection did not discover the temporary receiver"
        report["webui_version"] = json_request(args.endpoint, "/api/version")["version"]
        cases = [
            [{"role": "system", "content": "Contract check. Preserve Ω and line\nbreaks."},
             {"role": "user", "content": ""}],
            [{"role": "system", "content": "Long history contract check."}] +
            [{"role": "user" if i % 2 == 0 else "assistant", "content": str(i) + " · " + "context " * 100} for i in range(51)],
        ]
        for messages in cases:
            before = len(captures)
            submitted = {"model": model, "messages": messages, "stream": False, "temperature": .37,
                         "top_p": .83, "seed": 123456, "max_tokens": 64, "presence_penalty": 0,
                         "frequency_penalty": 0, "stop": ["CONTRACT_STOP"], "reasoning": {"enabled": False},
                         "provider": {"only": ["contract-provider"], "allow_fallbacks": False, "require_parameters": True},
                         "features": {"memory": False, "web_search": False, "code_interpreter": False},
                         "background_tasks": {"title_generation": False, "tags_generation": False, "follow_up_generation": False}}
            response = http_request(args.endpoint, "/api/chat/completions", submitted, token)
            effective = captures[-1]["json"] if len(captures) == before + 1 else None
            expected = {k: v for k, v in submitted.items() if k not in ("features", "background_tasks")}
            report["checks"].append({"submitted": submitted, "received": captures[before:],
                                     "response": response.raw, "transport": response.evidence,
                                     "exact_expected_provider_payload": effective == expected,
                                     "messages_preserved": effective is not None and effective.get("messages") == messages})
        report["passed"] = all(x["exact_expected_provider_payload"] and x["transport"]["http_status"] == 200 for x in report["checks"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        # Remove the ephemeral model from the cache after the receiver stops.
        try:
            refreshed = json_request(args.endpoint, "/api/models?refresh=true", token=token)
            report["temporary_model_removed"] = all(x["id"] != model for x in refreshed["data"])
        except Exception as exc:
            report["cache_cleanup_error"] = type(exc).__name__
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": report.get("passed", False), "checks": len(report["checks"]),
                      "temporary_model_removed": report.get("temporary_model_removed"), "evidence": str(output)}))


if __name__ == "__main__":
    main()
