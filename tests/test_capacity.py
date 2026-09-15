import copy
from pathlib import Path
import tempfile
import unittest

from behaviorlab.backends import LIVE_BACKEND, LIVE_PARSER
from behaviorlab.capacity import execute_capacity, validate_plan, reconstruct
from behaviorlab.common import read_json
from behaviorlab.journal import read_events
from behaviorlab.runner import NeedsAttention
import test_ollama_context


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.path = Path(self.tmp.name)/'diagnostic'
        self.fixture = f = test_ollama_context.OllamaContextTests(); f.setUp()
        self.plan = {'schema': 'behaviorlab.capacity-plan/1', 'data_class': 'local_engineering_capacity_diagnostic',
            'parser_version': LIVE_PARSER, 'sources': {'fixture': {'registry': read_json(f.registry.document_json)}},
            'jobs': [{'id': 'one', 'source': 'fixture', 'model': 'A', 'request': f.payload,
                      'original_request': copy.deepcopy(f.payload), 'matched_group': 'pair'}]}
        class Backend:
            identity = LIVE_BACKEND
            calls = 0
            def verify(self, model): return {'fixture': True}
            def preflight(self, payload, model):
                self.evidence = f.preflight(); return self.evidence
            def generate(self, payload, model):
                self.calls += 1; return f.response(self.evidence)[1]
        self.backend = Backend()

    def tearDown(self): self.tmp.cleanup()

    def test_saved_response_recovers_and_complete_replay_is_byte_preserving(self):
        def stop(event, job):
            if event == 'after_response': raise RuntimeError('simulated interruption')
        with self.assertRaises(RuntimeError):
            execute_capacity(self.path, self.plan, 1, self.backend, stop)
        self.assertEqual(self.backend.calls, 1)
        recovered = execute_capacity(self.path, self.plan, 0, self.backend)
        self.assertTrue(recovered['complete']); self.assertEqual(recovered['new_calls'], 0)
        before = (self.path/'events.jsonl').read_bytes()
        execute_capacity(self.path, self.plan, 1, self.backend)
        self.assertEqual(self.backend.calls, 1)
        self.assertEqual((self.path/'events.jsonl').read_bytes(), before)

    def test_unknown_request_never_retries(self):
        def stop(event, job):
            if event == 'after_request': raise RuntimeError('simulated interruption')
        with self.assertRaises(RuntimeError): execute_capacity(self.path, self.plan, 1, self.backend, stop)
        with self.assertRaises(NeedsAttention): execute_capacity(self.path, self.plan, 1, self.backend)
        self.assertEqual(self.backend.calls, 0)

    def test_changed_context_and_changed_result_are_rejected(self):
        bad = copy.deepcopy(self.plan); bad['jobs'][0]['request']['messages'][0]['content'] = 'changed'
        with self.assertRaises(ValueError): validate_plan(bad)
        execute_capacity(self.path, self.plan, 1, self.backend)
        events = read_events(self.path/'events.jsonl')
        events[-1]['payload']['result']['generated_tokens'] += 1
        with self.assertRaises(ValueError): reconstruct(events)


if __name__ == '__main__': unittest.main()
