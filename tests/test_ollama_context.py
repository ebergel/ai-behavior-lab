import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behaviorlab import ollama_context as oc
from behaviorlab.backends import HTTPBackend, parse_live, prepare_request
from behaviorlab.common import canonical, read_json, sha256
from behaviorlab.journal import read_events
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import create_campaign, execute, campaign_documents
from test_live import wire, FixtureHTTPBackend

ROOT = Path(__file__).resolve().parents[1]


class OllamaContextTests(unittest.TestCase):
    def setUp(self):
        self.registry = Registry.load(ROOT / 'design/ollama-context-models.json')
        self.model = self.registry.model('A')
        self.q = oc.profile(self.model)
        self.d = read_json((ROOT / 'examples/local-bridge.engineering.json').read_text())
        self.d['registry_sha256'] = self.registry.digest
        for s in self.d['settings']['by_model'].values():
            s.update(truncate=False, shift=False)
        self.protocol = Protocol.from_dict(self.d, self.registry)
        self.payload = prepare_request(self.model, self.d['settings']['by_model']['A'],
                                       [{'role': 'user', 'content': 'café 空'}], 7)
        argv = list(self.q['runner_arguments']); argv[argv.index('{port}')] = '1234'
        self.runner = {'pid': 1, 'parent_pid': 2, 'endpoint': 'http://127.0.0.1:1234', 'arguments': argv}
        self.tokens = [11, 22, 33]

    def fake_http(self, endpoint, path, payload=None):
        if path == '/api/chat':
            self.assertIs(payload['_debug_render_only'], True)
            return wire({'model': self.model.tag, 'done': False,
                         '_debug_info': {'rendered_template': '<turn>café 空🙂'}})
        if path == '/props':
            return wire({'model_path': self.q['model_blob'], 'build_info': self.q['runner_build_info'],
                         'total_slots': 1, 'default_generation_settings': {'n_ctx': 32768}})
        self.assertEqual(path, '/tokenize')
        self.assertIs(payload['add_special'], False)
        self.assertIs(payload['parse_special'], True)
        return wire({'tokens': self.tokens})

    def preflight(self):
        with patch('behaviorlab.backends.http_request', side_effect=self.fake_http), \
             patch('behaviorlab.ollama_context.discover_runner', return_value=self.runner):
            return oc.preflight(self.payload, self.model)

    def response(self, evidence):
        d = {'model': self.model.tag, 'done': True, 'done_reason': 'stop',
             'message': {'role': 'assistant', 'content': 'A measured response.'},
             'prompt_eval_count': len(self.tokens), 'prompt_eval_cached_count': 1, 'eval_count': 3}
        r = wire(d); r.evidence['ollama_context'] = evidence
        return d, r

    def test_defaults_ignore_key_order_but_preserve_values_and_stop_order(self):
        a = 'top_k 20\nstop "a"\nstop "b"\ntemperature 0.8'
        b = 'temperature 0.8\nstop "a"\nstop "b"\ntop_k 20'
        self.assertEqual(oc.parameter_values(a), oc.parameter_values(b))
        self.assertNotEqual(oc.parameter_values(a), oc.parameter_values(b.replace('top_k 20', 'top_k 21')))
        self.assertNotEqual(oc.parameter_values(a), oc.parameter_values(b.replace('"a"\nstop "b"', '"b"\nstop "a"')))

    def test_native_context_controls_are_explicit_and_gateway_cannot_accept_them(self):
        self.assertIs(self.payload['truncate'], False)
        self.assertIs(self.payload['shift'], False)
        for key in ('truncate', 'shift'):
            d = copy.deepcopy(self.d); d['settings']['by_model']['A'].pop(key)
            with self.assertRaisesRegex(ValueError, 'truncation'):
                Protocol.from_dict(d, self.registry)
        old = Registry.load(ROOT / 'design/local-engineering-models.json')
        d = copy.deepcopy(self.d); d['registry_sha256'] = old.digest
        with self.assertRaisesRegex(ValueError, 'Unsupported native control'):
            Protocol.from_dict(d, old)

    def test_recipient_tokens_and_raw_evidence_cross_check_generation(self):
        evidence = self.preflight()
        self.assertEqual(evidence['input_tokens'], 3)
        self.assertEqual(evidence['context_headroom'], 32768-256-3)
        _, r = self.response(evidence)
        self.assertEqual(parse_live(r.raw, self.payload, self.model, r.evidence)['content'], 'A measured response.')
        for key, value in [('prompt_eval_count', 2), ('prompt_eval_cached_count', None), ('eval_count', 257)]:
            d, _ = self.response(evidence); d[key] = value
            r = wire(d); r.evidence['ollama_context'] = evidence
            with self.subTest(key=key), self.assertRaises(ValueError):
                parse_live(r.raw, self.payload, self.model, r.evidence)
        bad = copy.deepcopy(evidence); bad['tokenization']['request']['content'] += ' changed'
        _, r = self.response(bad)
        with self.assertRaisesRegex(ValueError, 'tokenization input'):
            parse_live(r.raw, self.payload, self.model, r.evidence)

    def test_oversize_preflight_keeps_evidence_and_dispatches_no_generation(self):
        self.tokens = list(range(32768))
        with self.assertRaises(oc.ContextLimitError) as caught:
            self.preflight()
        self.assertEqual(caught.exception.evidence['input_tokens'], 32768)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)/'campaign'
            create_campaign(tmp, self.protocol, self.registry)
            with patch.object(HTTPBackend, 'verify', return_value={'fixture': True}), \
                 patch('behaviorlab.backends.http_request', side_effect=self.fake_http), \
                 patch('behaviorlab.ollama_context.discover_runner', return_value=self.runner), \
                 patch.object(HTTPBackend, 'generate') as generate:
                with self.assertRaises(oc.ContextLimitError):
                    execute(tmp, backend=HTTPBackend(), max_calls=1)
                generate.assert_not_called()
            _, _, state = campaign_documents(read_events(Path(tmp)/'events.jsonl'))
            self.assertFalse(state.requests)

    def test_file_verification_cache_is_per_model_and_detects_content_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = []
            for label in ('a', 'b'):
                p = Path(tmp)/label; p.write_bytes(label.encode())
                q = {'files': [{'path': str(p), 'bytes': 1, 'sha256': sha256(p.read_bytes())}]}
                models.append(SimpleNamespace(digest=label, metadata_json=canonical({'artifact': {'qualification': q}})))
            cache = {}; original_open = Path.open; reads = []
            def counted(path, *args, **kwargs):
                reads.append(str(path)); return original_open(path, *args, **kwargs)
            with patch.object(Path, 'open', counted):
                for model in (models[0], models[1], models[0]):
                    oc.verify_files(model, cache)
            self.assertEqual(len(reads), 2)
            (Path(tmp)/'a').write_bytes(b'z')
            with self.assertRaisesRegex(ValueError, 'content changed'):
                oc.verify_files(models[0], cache)

    def test_parser2_campaign_is_replay_only_under_parser3(self):
        registry = Registry.load(ROOT / 'design/local-engineering-models.json')
        d = read_json((ROOT/'examples/local-bridge.engineering.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)/'campaign'
            with patch('behaviorlab.runner.LIVE_PARSER', 'http-chat/2'):
                create_campaign(tmp, Protocol.from_dict(d, registry), registry)
                execute(tmp, backend=FixtureHTTPBackend(), max_calls=1)
            before = (Path(tmp)/'events.jsonl').read_bytes(); backend = FixtureHTTPBackend()
            with self.assertRaisesRegex(ValueError, 'replay-only'):
                execute(tmp, backend=backend)
            self.assertEqual(backend.calls, 0)
            self.assertEqual((Path(tmp)/'events.jsonl').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
