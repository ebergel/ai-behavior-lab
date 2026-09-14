import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from behaviorlab.common import canonical, read_json
from behaviorlab.legacy import (import_corpus, verify_corpus, reindex_corpus,
                                corpus_summary, parse_run)


class LegacyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.source = self.base / "reference"
        self.destination = self.base / "lab/corpus"
        p = self.source / "data/runs3"
        p.mkdir(parents=True)
        self.path = p / "TEST-A_run01.jsonl"
        self.rows = [{"kind": "header", "cond": "TEST-A", "run": 1, "pair_model": "old:model", "unknown": 123},
                     {"kind": "message", "turn": 1, "speaker": "X", "content": "One\u2028two."},
                     {"kind": "message", "turn": 2, "speaker": "Y", "content": "", "thinking": "", "done_reason": "stop"},
                     {"kind": "third", "turn": 2, "speaker": "Z", "content": "A separate intervention."},
                     {"kind": "custom_event", "original_information": [1, 2, 3]},
                     {"kind": "footer", "pair_turns": 2, "ended_at": None}]
        self.raw = ('\r\n'.join(json.dumps(r, ensure_ascii=False) for r in self.rows)).encode()
        self.path.write_bytes(self.raw)

    def tearDown(self):
        self.tmp.cleanup()

    def do_import(self, **kwargs):
        return import_corpus(self.source, self.destination, "https://example.org/reference", "test-revision", **kwargs)

    def test_preserves_bytes_unknown_fields_interventions_and_missing_provenance(self):
        result = self.do_import(expected_runs=1)
        self.assertEqual((result["runs"], result["pair_messages"], result["third_messages"]), (1, 2, 1))
        self.assertEqual(result["known_model_digests"], 0)
        manifest = verify_corpus(self.destination)
        self.assertEqual((self.destination / "blobs" / manifest["runs"][0]["sha256"]).read_bytes(), self.raw)
        self.assertEqual(self.path.read_bytes(), self.raw)
        db = sqlite3.connect(self.destination / "catalog.sqlite")
        try:
            rows = db.execute("SELECT content,thinking,thinking_present FROM records WHERE kind='message' ORDER BY turn").fetchall()
            self.assertEqual(rows, [("One\u2028two.", None, 0), ("", "", 1)])
            self.assertEqual(db.execute("SELECT count(*) FROM records WHERE kind='custom_event'").fetchone()[0], 1)
            header = read_json(db.execute("SELECT header_json FROM runs").fetchone()[0])
            self.assertEqual(header["unknown"], 123)
        finally:
            db.close()

    def test_import_idempotent_but_refuses_different_data_at_same_destination(self):
        first = self.do_import()
        self.assertEqual(self.do_import()["dataset_sha256"], first["dataset_sha256"])
        self.path.write_bytes(self.raw.replace(b'One', b'New'))
        with self.assertRaises(ValueError):
            self.do_import()

    def test_index_rebuild_does_not_need_reference_repository(self):
        first = self.do_import()
        self.path.unlink()
        (self.destination / "catalog.sqlite").unlink()
        reindex_corpus(self.destination)
        self.assertEqual(corpus_summary(self.destination), first)

    def test_bad_footer_aborts_import_before_destination_created(self):
        self.path.write_bytes(self.raw.replace(b'"pair_turns": 2', b'"pair_turns": 3'))
        with self.assertRaises(ValueError):
            self.do_import()
        self.assertFalse(self.destination.exists())

    def test_source_repository_cannot_be_import_destination(self):
        with self.assertRaises(ValueError):
            import_corpus(self.source, self.source / "new-data", "reference")

    def test_blob_tampering_detected(self):
        self.do_import()
        manifest = verify_corpus(self.destination)
        blob = self.destination / "blobs" / manifest["runs"][0]["sha256"]
        blob.write_bytes(blob.read_bytes() + b" ")
        with self.assertRaises(ValueError):
            verify_corpus(self.destination)

    def test_audit_is_separate_source_not_rewritten_transcript(self):
        audit = self.base / "AUDIT.md"
        audit.write_text("Interpretation corrected in a later analysis.")
        result = self.do_import(audit=audit)
        self.assertEqual(len(result["supplements"]), 1)
        self.assertEqual(result["supplements"][0]["role"], "separate_analysis_not_original_run_data")
        self.assertEqual(self.path.read_bytes(), self.raw)


if __name__ == "__main__":
    unittest.main()
