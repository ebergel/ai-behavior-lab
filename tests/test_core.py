import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from behaviorlab.common import canonical, read_json
from behaviorlab.history import Turn, messages
from behaviorlab.journal import Journal, read_events, rebuild_index
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import (FakeBackend, NeedsAttention, create_campaign, execute,
                                summarize, State)

ROOT = Path(__file__).resolve().parents[1]


def setup_protocol(two_roots=False):
    registry = Registry.load(ROOT / "design/models.json")
    data = read_json((ROOT / "examples/history-factorial.fake.json").read_text())
    data["roots"] = [r for r in data["roots"] if r["id"] == "AB-r01"]
    if two_roots:
        other = copy.deepcopy(data["roots"][0])
        other.update(id="AB-r02", root_index=2)
        data["roots"].append(other)
    for segment in data["segments"]:
        if segment["id"] == "prefix":
            segment.update(start=1, stop=2)
        elif len(segment["id"]) == 1:
            segment.update(start=3, stop=4)
        else:
            segment.update(start=5, stop=6)
    return data, registry, Protocol.from_dict(data, registry)


class ProtocolTests(unittest.TestCase):
    def test_full_factorial_is_shared_graph_not_eighty_independent_roots(self):
        registry = Registry.load(ROOT / "design/models.json")
        protocol = Protocol.load(ROOT / "examples/history-factorial.fake.json", registry)
        nodes = protocol.nodes()
        self.assertEqual(len(nodes), 1800)
        self.assertEqual(len({n.id for n in nodes}), 1800)
        self.assertEqual(len(protocol.roots), 20)
        self.assertEqual(sum(n.turn == 50 for n in nodes), 80)
        for root in protocol.roots:
            group = [n for n in nodes if n.root == root.name]
            self.assertEqual(len(group), 90)
            same_turn = [n for n in group if n.turn == 41]
            self.assertEqual(len({n.seed for n in same_turn}), 1)
            self.assertEqual(len(same_turn), 4)

    def test_rejects_silent_protocol_changes(self):
        for change in [lambda d: d.update(execution_class="live"),
                       lambda d: d.update(registry_sha256="0"*64),
                       lambda d: d.update(recent_messages=2),
                       lambda d: d["settings"]["options"].update(unrecognized=42),
                       lambda d: d["segments"][3].update(start=4),
                       lambda d: d["roots"][0].update(segment_order=["FF", "FR", "F", "R", "RF", "RR", "prefix"])]:
            d, registry, _ = setup_protocol()
            change(d)
            with self.assertRaises(ValueError):
                Protocol.from_dict(d, registry)

    def test_registry_detects_artifact_drift(self):
        _, registry, _ = setup_protocol()
        model = registry.model("A")
        registry.verify_observation("A", model.tag, model.digest)
        with self.assertRaises(ValueError):
            registry.verify_observation("A", model.tag, "0" * 64)
        document = read_json(registry.document_json)
        document["models"][0]["template"] += "changed"
        with self.assertRaises(ValueError):
            Registry.from_dict(document)

    def test_immutable_snapshot_has_no_alias_to_input(self):
        d, registry, protocol = setup_protocol()
        original = protocol.digest
        d["settings"]["options"]["temperature"] = 99
        d["roots"][0]["X"] = "B"
        self.assertEqual(protocol.digest, original)
        self.assertEqual(read_json(protocol.settings_json)["options"]["temperature"], .8)
        with self.assertRaises(FrozenInstanceError):
            protocol.roots[0].x_model = "B"

    def test_research_proposal_cannot_be_executed_as_runtime_schema(self):
        _, registry, _ = setup_protocol()
        d = read_json((ROOT / "design/round0-factorial-v0.1.json").read_text())
        with self.assertRaises(ValueError):
            Protocol.from_dict(d, registry)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):
            read_json('{"seed":1,"seed":2}')


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.d, self.registry, self.protocol = setup_protocol()

    def tearDown(self):
        self.tmp.cleanup()

    def campaign(self, name="run", protocol=None):
        path = self.base / name
        create_campaign(path, protocol or self.protocol, self.registry)
        return path

    def records(self, path):
        return read_events(path / "events.jsonl")

    def committed(self, path):
        return [e["payload"] for e in self.records(path) if e["kind"] == "turn_committed"]

    def test_roles_and_actual_restricted_branch_restoration(self):
        path = self.campaign()
        execute(path)
        events = self.records(path)
        requests = {e["payload"]["node_id"]: e["payload"]["request"] for e in events if e["kind"] == "request_saved"}
        content = {p["node_id"]: p["content"] for p in self.committed(path)}
        restored = requests["AB-r01:RF:5"]["messages"]
        self.assertEqual([m["role"] for m in restored], ["system", "user", "assistant", "user", "assistant", "user"])
        self.assertEqual([m["content"] for m in restored[2:]],
                         [content[f"AB-r01:{s}:{t}"] for s, t in [("prefix", 1), ("prefix", 2), ("R", 3), ("R", 4)]])
        self.assertNotIn(content["AB-r01:F:3"], [m["content"] for m in restored])
        restricted = requests["AB-r01:RR:5"]["messages"]
        self.assertEqual(len(restricted), 4)
        self.assertEqual([m["content"] for m in restricted[1:]],
                         [content[f"AB-r01:{s}:{t}"] for s, t in [("prefix", 2), ("R", 3), ("R", 4)]])
        self.assertEqual(requests["AB-r01:prefix:1"]["model"], self.registry.model("A").tag)
        self.assertEqual(requests["AB-r01:prefix:2"]["model"], self.registry.model("B").tag)
        self.assertEqual(requests["AB-r01:prefix:2"]["messages"],
                         [{"role": "system", "content": self.protocol.system},
                          {"role": "user", "content": content["AB-r01:prefix:1"]}])

    def test_pause_resume_reuses_committed_turns_and_completed_run_is_idempotent(self):
        control = self.campaign("control")
        execute(control)
        path = self.campaign()
        first = FakeBackend()
        summary = execute(path, backend=first, max_calls=3)
        self.assertEqual(first.calls, 3)
        self.assertFalse(summary["complete"])
        second = FakeBackend()
        result = execute(path, backend=second)
        self.assertEqual(second.calls, 11)
        self.assertEqual(result["committed_turns"], 14)
        self.assertEqual(self.committed(control), self.committed(path))
        size = (path / "events.jsonl").stat().st_size
        again = FakeBackend()
        execute(path, backend=again)
        self.assertEqual(again.calls, 0)
        self.assertEqual((path / "events.jsonl").stat().st_size, size)

    def test_recovery_after_raw_response_does_not_regenerate(self):
        path = self.campaign()
        def crash(stage, node):
            if stage == "after_response":
                raise KeyboardInterrupt("simulated process interruption")
        before = FakeBackend()
        with self.assertRaises(KeyboardInterrupt):
            execute(path, backend=before, hook=crash)
        self.assertEqual(before.calls, 1)
        self.assertEqual(len(self.committed(path)), 0)
        after = FakeBackend()
        result = execute(path, backend=after)
        self.assertEqual(after.calls, 13)
        self.assertEqual(result["responses"], 14)

    def test_unknown_outcome_requires_explicit_retry_and_preserves_attempt(self):
        path = self.campaign()
        def crash(stage, node):
            if stage == "after_request":
                raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            execute(path, hook=crash)
        backend = FakeBackend()
        with self.assertRaises(NeedsAttention):
            execute(path, backend=backend)
        self.assertEqual(backend.calls, 0)
        result = execute(path, backend=backend, retry_unresolved=True)
        self.assertEqual(result["requests"], 15)
        self.assertEqual(result["responses"], 14)
        self.assertEqual(sum(e["kind"] == "attempt_retry_authorized" for e in self.records(path)), 1)

    def test_backend_error_is_saved_and_not_silently_retried(self):
        class Broken(FakeBackend):
            def generate(self, payload):
                raise OSError("fixture failure")
        path = self.campaign()
        with self.assertRaises(NeedsAttention):
            execute(path, backend=Broken())
        self.assertEqual(self.records(path)[-1]["kind"], "request_error")
        with self.assertRaises(NeedsAttention):
            execute(path)
        result = execute(path, retry_unresolved=True)
        self.assertEqual(result["committed_turns"], 14)

    def test_invalid_branch_blocks_descendants_but_other_root_runs(self):
        _, _, protocol = setup_protocol(two_roots=True)
        class Capped(FakeBackend):
            def generate(self, payload):
                result = read_json(super().generate(payload))
                if self.calls == 1:
                    result["done_reason"] = "length"
                return canonical(result)
        path = self.campaign(protocol=protocol)
        result = execute(path, backend=Capped())
        self.assertEqual((result["invalid_turns"], result["blocked_nodes"], result["committed_turns"]), (1, 13, 14))
        self.assertTrue(result["complete"])
        again = FakeBackend()
        execute(path, backend=again)
        self.assertEqual(again.calls, 0)

    def test_empty_normal_response_and_literal_end_are_preserved(self):
        class EmptyAndEnd(FakeBackend):
            def generate(self, payload):
                result = read_json(super().generate(payload))
                if self.calls == 1:
                    result["message"]["content"] = ""
                if self.calls == 2:
                    result["message"]["content"] = "[END]"
                result["unknown_field"] = {"retained": True}
                return canonical(result)
        path = self.campaign()
        result = execute(path, backend=EmptyAndEnd())
        self.assertEqual(result["committed_turns"], 14)
        turns = self.committed(path)
        self.assertEqual([p["content"] for p in turns[:2]], ["", "[END]"])
        events = self.records(path)
        raws = [e["payload"]["raw_response"] for e in events if e["kind"] == "response_saved"]
        self.assertTrue(read_json(raws[0])["unknown_field"]["retained"])
        second = [e["payload"]["request"] for e in events if e["kind"] == "request_saved"][1]
        self.assertEqual(second["messages"][-1]["content"], "")

    def test_malformed_response_saved_before_parsing_and_halted(self):
        class Malformed(FakeBackend):
            def generate(self, payload):
                return ' {"unparseable": '
        path = self.campaign()
        result = execute(path, backend=Malformed())
        self.assertEqual(result["invalid_turns"], 1)
        raw = next(e for e in self.records(path) if e["kind"] == "response_saved")
        self.assertEqual(raw["payload"]["raw_response"], ' {"unparseable": ')

    def test_unexpected_trace_invalidates_nominal_thinking_off(self):
        class Thinking(FakeBackend):
            def generate(self, payload):
                result = read_json(super().generate(payload))
                result["message"]["thinking"] = "private generated text"
                return canonical(result)
        path = self.campaign()
        result = execute(path, backend=Thinking())
        self.assertEqual(result["committed_turns"], 0)
        self.assertEqual(result["invalid_turns"], 1)

    def test_turn_traces_never_enter_partner_or_own_api_history(self):
        history = (Turn("one", None, "root", 1, "X", "visible", "PRIVATE TRACE"),)
        for speaker in ["X", "Y"]:
            text = canonical(messages(self.protocol, history, speaker, "F"))
            self.assertIn("visible", text)
            self.assertNotIn("PRIVATE TRACE", text)

    def test_duplicate_writer_and_existing_campaign_rejected(self):
        path = self.campaign()
        with self.assertRaises(FileExistsError):
            create_campaign(path, self.protocol, self.registry)
        with Journal(path):
            with self.assertRaises(BlockingIOError):
                with Journal(path):
                    pass

    def test_partial_or_corrupt_journal_is_not_silently_repaired(self):
        path = self.campaign()
        original = (path / "events.jsonl").read_bytes()
        (path / "events.jsonl").write_bytes(original + b'{"partial":')
        with self.assertRaises(ValueError):
            execute(path)
        self.assertTrue((path / "events.jsonl").read_bytes().endswith(b'{"partial":'))
        changed = original.replace(b'campaign_created', b'campaign_changed')
        (path / "events.jsonl").write_bytes(changed)
        with self.assertRaises(ValueError):
            summarize(path)

    def test_index_is_rebuildable_and_unicode_separators_are_not_record_delimiters(self):
        path = self.campaign()
        execute(path)
        (path / "index.sqlite").unlink()
        with Journal(path) as journal:
            journal.append("campaign_paused", {"note": "one\u2028two\u2029three"})
            rebuild_index(path, journal.events)
        events = self.records(path)
        self.assertEqual(events[-1]["payload"]["note"], "one\u2028two\u2029three")
        db = sqlite3.connect(path / "index.sqlite")
        try:
            self.assertEqual(db.execute("SELECT count(*) FROM events").fetchone()[0], len(events))
            self.assertEqual(db.execute("SELECT journal_head FROM identity").fetchone()[0], events[-1]["hash"])
        finally:
            db.close()

    def test_premature_completion_is_rejected(self):
        path = self.campaign()
        with Journal(path) as journal:
            journal.append("campaign_complete", {"planned_nodes": 14, "accounted_nodes": 0})
        with self.assertRaises(ValueError):
            summarize(path)


if __name__ == "__main__":
    unittest.main()
