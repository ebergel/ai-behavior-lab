import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.backends import (HTTPBackend, WireResponse, LIVE_BACKEND, parse_live,
                                 prepare_request, validate_endpoint)
from behaviorlab.common import canonical, read_json, sha256
from behaviorlab.history import request
from behaviorlab.journal import read_events
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import create_campaign, execute, NeedsAttention
from behaviorlab.webui import export_transcript, import_transcript

ROOT = Path(__file__).resolve().parents[1]


def setup():
    registry = Registry.load(ROOT / "design/local-engineering-models.json")
    d = read_json((ROOT / "examples/local-bridge.engineering.json").read_text())
    return registry, d, Protocol.from_dict(d, registry)


def wire(data, status=200):
    raw = data if isinstance(data, str) else canonical(data)
    return WireResponse(raw, {"http_status": status, "response_bytes_base64": base64.b64encode(raw.encode()).decode(),
                              "response_sha256": sha256(raw.encode())})


class FixtureHTTPBackend:
    """No networking: tests durability of HTTP-shaped evidence only."""
    identity = LIVE_BACKEND
    def __init__(self):
        self.calls = 0
        self.verifications = 0
    def verify(self, model):
        self.verifications += 1
        return {"test_fixture": True}
    def generate(self, payload, model):
        self.calls += 1
        message = {"role": "assistant", "content": "HTTP fixture " + str(self.calls)}
        if read_json(model.metadata_json)["backend"] == "ollama":
            return wire({"model": model.tag, "done": True, "done_reason": "stop", "message": message})
        return wire({"model": model.tag, "choices": [{"finish_reason": "stop", "message": message}],
                     "usage": {"prompt_tokens": 17, "completion_tokens": 3}, "provider": "test-provider"})


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name) / "campaign"
        self.registry, self.d, self.protocol = setup()
    def tearDown(self):
        self.tmp.cleanup()
    def create(self):
        create_campaign(self.directory, self.protocol, self.registry)

    def test_service_digest_unknown_is_null_and_cloud_cannot_run_locally(self):
        row = read_json(self.registry.model("A").metadata_json)
        row.update(backend="openai", endpoint="https://example.com/v1", location="remote", digest=None,
                   artifact=None, auth_env="EXAMPLE_KEY", server_version="unknown", capabilities=["max_tokens"])
        document = {"schema": "behaviorlab.models/2", "models": [row]}
        remote = Registry.from_dict(document)
        self.assertIsNone(remote.model("A").digest)
        d = copy.deepcopy(self.d)
        d.update(registry_sha256=remote.digest, settings={"by_model": {"A": {"max_tokens": 10}}})
        with self.assertRaisesRegex(ValueError, "Cloud execution"):
            Protocol.from_dict(d, remote)
        row["digest"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "null"):
            Registry.from_dict(document)

    def test_webui_native_controls_are_nested_without_altering_history(self):
        model = self.registry.model("B")
        messages = [{"role": "system", "content": " Ω \n"}, {"role": "user", "content": ""}]
        payload = prepare_request(model, self.d["settings"]["by_model"]["B"], messages, 7)
        self.assertEqual(payload["messages"], messages)
        self.assertEqual(payload["options"]["seed"], 7)
        self.assertIs(payload["options"]["think"], False)
        self.assertNotIn("think", payload)
        self.assertEqual(payload["options"]["num_predict"], 256)
        self.assertTrue(all(v is False for v in payload["features"].values()))
        self.assertNotIn("seed", self.d["settings"]["by_model"]["B"]["options"])

    def test_unsupported_parameters_rejected_not_silently_ignored(self):
        self.d["settings"]["by_model"]["A"]["options"]["made_up"] = 3
        with self.assertRaises(ValueError):
            Protocol.from_dict(self.d, self.registry)

    def test_endpoint_cannot_embed_secrets_or_send_cleartext_off_loopback(self):
        for endpoint in ["https://user:password@example.com", "http://example.com", "https://example.com?api_key=abc"]:
            with self.assertRaises(ValueError):
                validate_endpoint(endpoint)

    def test_client_deadline_is_validated_and_does_not_enter_model_payload(self):
        for value in (0, -1, True, float('nan'), float('inf'), 3601):
            with self.subTest(value=value), self.assertRaises(ValueError):
                HTTPBackend(request_timeout=value)
        model = self.registry.model('A')
        payload = prepare_request(model, self.d['settings']['by_model']['A'], [], 7)
        before = canonical(payload)
        with patch('behaviorlab.backends.http_request', return_value=wire('{}')) as api:
            HTTPBackend(request_timeout=300).generate(payload, model)
        self.assertEqual(api.call_args.kwargs['timeout'], 300)
        self.assertEqual(canonical(payload), before)
        self.assertNotIn('timeout', payload)

    def test_live_resume_reuses_raw_response_and_final_rerun_needs_no_network(self):
        self.create()
        def crash(stage, node):
            if stage == "after_response":
                raise KeyboardInterrupt()
        first = FixtureHTTPBackend()
        with self.assertRaises(KeyboardInterrupt):
            execute(self.directory, backend=first, hook=crash)
        second = FixtureHTTPBackend()
        result = execute(self.directory, backend=second)
        self.assertEqual((first.calls, second.calls), (1, 13))
        self.assertEqual(result["committed_turns"], 14)
        original = (self.directory / "events.jsonl").read_bytes()
        after = FixtureHTTPBackend()
        execute(self.directory, backend=after)
        self.assertEqual((after.calls, after.verifications), (0, 0))
        self.assertEqual(original, (self.directory / "events.jsonl").read_bytes())

    def test_legacy_parser_replay_preserves_bytes_and_refuses_new_inference(self):
        with patch('behaviorlab.runner.LIVE_PARSER', 'http-chat/1'):
            self.create()
            execute(self.directory, backend=FixtureHTTPBackend(), max_calls=1)
        before = (self.directory / 'events.jsonl').read_bytes()
        backend = FixtureHTTPBackend()
        with self.assertRaisesRegex(ValueError, 'replay-only'):
            execute(self.directory, backend=backend)
        self.assertEqual(backend.calls, 0)
        self.assertEqual(before, (self.directory / 'events.jsonl').read_bytes())

    def test_http_failure_body_and_status_saved_without_generation_retry(self):
        class Failure(FixtureHTTPBackend):
            def generate(self, payload, model):
                self.calls += 1
                return wire('{"error":"test unavailable"}', 503)
        self.create()
        backend = Failure()
        result = execute(self.directory, backend=backend)
        self.assertEqual((backend.calls, result["invalid_turns"], result["blocked_nodes"]), (1, 1, 13))
        e = next(e for e in read_events(self.directory / "events.jsonl") if e["kind"] == "response_saved")
        self.assertEqual(e["payload"]["transport"]["http_status"], 503)
        self.assertIn("test unavailable", e["payload"]["raw_response"])

    def test_transport_exception_details_cannot_leak_credential(self):
        class Failure(FixtureHTTPBackend):
            def generate(self, payload, model):
                raise OSError("SENSITIVE_TOKEN")
        self.create()
        with self.assertRaises(NeedsAttention):
            execute(self.directory, backend=Failure())
        self.assertNotIn("SENSITIVE_TOKEN", (self.directory / "events.jsonl").read_text())

    def test_openai_cap_trace_model_and_corrupt_bytes_are_not_valid_turns(self):
        model = self.registry.model("B")
        payload = prepare_request(model, self.d["settings"]["by_model"]["B"], [], 1)
        data = {"model": model.tag, "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": ""}}]}
        def parse(d):
            response = wire(d)
            return parse_live(response.raw, payload, model, response.evidence)
        self.assertEqual(parse(data)["content"], "")
        data["choices"][0]["finish_reason"] = "length"
        self.assertEqual(parse(data)["invalid_reason"], "output_cap")
        data["choices"][0]["finish_reason"] = "stop"
        data["choices"][0]["message"]["reasoning_content"] = "trace"
        self.assertEqual(parse(data)["invalid_reason"], "unexpected_thinking_output")
        data["model"] = "unexpected-fallback"
        with self.assertRaises(ValueError):
            parse(data)
        response = wire({"example": True})
        response.evidence["response_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "bytes"):
            parse_live(response.raw, payload, model, response.evidence)

    def test_verified_weight_drift_stops_before_generation(self):
        model = self.registry.model("A")
        with patch("behaviorlab.backends.json_request", return_value={"models": [{"name": model.tag, "digest": "0" * 64}]}):
            with self.assertRaisesRegex(ValueError, "artifact drift"):
                HTTPBackend().verify(model)

    def test_display_export_uses_actual_restricted_ancestry_and_cannot_import_twice(self):
        self.create()
        execute(self.directory, backend=FixtureHTTPBackend())
        document = export_transcript(self.directory, "AB-r01:RF:6")
        chat = document["chats"][0]["chat"]
        ids = [m.get("lab_node_id") for m in chat["messages"]][1:]
        self.assertIn("AB-r01:R:3", ids)
        self.assertNotIn("AB-r01:F:3", ids)
        self.assertTrue(chat["lab_evidence"]["display_only"])
        receipt = Path(self.tmp.name) / "receipt.json"
        with patch("behaviorlab.webui.json_request", side_effect=[[{"id": "test-id"}], {"chat": chat}]) as api:
            imported = import_transcript("http://localhost:8080", "secret", document, receipt)
            repeated = import_transcript("http://localhost:8080", "secret", document, receipt)
        self.assertEqual(imported, repeated)
        self.assertEqual(api.call_count, 2)
        self.assertNotIn("secret", receipt.read_text())

    def test_uncertain_import_is_not_repeated(self):
        self.create()
        execute(self.directory, backend=FixtureHTTPBackend())
        document = export_transcript(self.directory, "AB-r01:FF:6")
        receipt = Path(self.tmp.name) / "receipt.json"
        with patch("behaviorlab.webui.json_request", side_effect=OSError("lost response")):
            with self.assertRaises(OSError):
                import_transcript("http://localhost:8080", "secret", document, receipt)
        with patch("behaviorlab.webui.json_request") as api:
            with self.assertRaisesRegex(ValueError, "unknown outcome"):
                import_transcript("http://localhost:8080", "secret", document, receipt)
            api.assert_not_called()

    def test_import_verification_failure_retries_only_the_read(self):
        self.create()
        execute(self.directory, backend=FixtureHTTPBackend())
        document = export_transcript(self.directory, "AB-r01:FF:6")
        receipt = Path(self.tmp.name) / "receipt.json"
        with patch("behaviorlab.webui.json_request", side_effect=[[{"id": "known-id"}], OSError("read failed")]):
            with self.assertRaises(OSError):
                import_transcript("http://localhost:8080", "secret", document, receipt)
        with patch("behaviorlab.webui.json_request", return_value={"chat": document["chats"][0]["chat"]}) as api:
            result = import_transcript("http://localhost:8080", "secret", document, receipt)
            self.assertTrue(result["round_trip_verified"])
            api.assert_called_once_with("http://localhost:8080", "/api/v1/chats/known-id", token="secret")


if __name__ == "__main__":
    unittest.main()
