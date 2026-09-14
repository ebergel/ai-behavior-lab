import base64
import copy
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab import mtplx
from behaviorlab.backends import HTTPBackend, parse_live, prepare_request
from behaviorlab.common import canonical, fingerprint, read_json, sha256
from behaviorlab.history import Turn, messages
from behaviorlab.journal import read_events
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import create_campaign, execute
from test_live import wire, FixtureHTTPBackend

ROOT = Path(__file__).resolve().parents[1]


class MTPLXTests(unittest.TestCase):
    def setUp(self):
        self.registry = Registry.load(ROOT / 'design/mtplx-engineering-models.json')
        self.model = self.registry.model('ON')
        self.row = read_json(self.model.metadata_json)
        self.doc = read_json((ROOT / 'examples/mtplx-mode-smoke.engineering.json').read_text())
        self.protocol = Protocol.from_dict(self.doc, self.registry)
        self.settings = self.doc['settings']['by_model']['ON']
        self.payload = prepare_request(self.model, self.settings, [{'role': 'user', 'content': 'Test'}], 7)

    def evidence(self):
        data = {'id': 'chatcmpl-test', 'model': self.model.tag,
                'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'Answer',
                            'reasoning_content': 'private trace'}}],
                'usage': {'prompt_tokens': 2, 'completion_tokens': 3}}
        c = {k: self.payload[k] for k in ('max_tokens', 'temperature', 'top_p', 'top_k',
             'presence_penalty', 'frequency_penalty', 'generation_mode', 'depth')}
        c.update(request_id=data['id'], model_id=self.model.tag, phase='completed', prompt_len=2,
                 prompt_token_ids=[11, 22], requested_seed=7,
                 observability={'request_enable_thinking': True, 'request_reasoning_effort': 'medium',
                     'preserve_thinking_effective': False, 'strip_assistant_reasoning_history': True,
                     'request_session_bank_bypass': True},
                 outcome={'resolved_seed': 7, 'attempts': 1, 'blank_retries': 0, 'completion_tokens': 3,
                          'finish_reason': 'stop'})
        return data, {'preflight': {'input_tokens': 2, 'prompt_token_ids_sha256': fingerprint([11, 22])}, 'capture': c}

    def test_explicit_controls_and_manifest_tampering(self):
        for key, value in [('top_k', True), ('enable_thinking', 'false'), ('metadata', {}), ('unknown', 1)]:
            s = copy.deepcopy(self.settings); s[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                mtplx.validate_settings(s, self.row)
        row = copy.deepcopy(self.row)
        row['artifact']['files'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            mtplx.validate_artifact(row)

    def test_stat_cache_does_not_mask_content_or_inventory_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / 'model.safetensors'; p.write_bytes(b'abc')
            a = {'model_path': td, 'files': [{'name': p.name, 'bytes': 3, 'sha256': sha256(b'abc')}], 'runtime_files': []}
            cache = {}
            one = mtplx.verify_files(a, fingerprint(a['files']), cache)
            self.assertEqual(one, mtplx.verify_files(a, fingerprint(a['files']), cache))
            p.write_bytes(b'xyz')
            with self.assertRaisesRegex(ValueError, 'content drift'):
                mtplx.verify_files(a, fingerprint(a['files']), cache)
            p.write_bytes(b'abc'); (root / 'new.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'inventory drift'):
                mtplx.verify_files(a, fingerprint(a['files']), cache)

    def test_direct_generation_cannot_target_another_local_service(self):
        row = copy.deepcopy(self.row)
        row['endpoint'] = 'http://localhost:9000/v1'
        with self.assertRaisesRegex(ValueError, 'differs from the verified engine'):
            mtplx.validate_artifact(row)

    def test_rendered_context_reserves_output_and_rejects_before_generation(self):
        n = self.row['artifact']['expected_health']['context_window'] - self.payload['max_tokens']
        def rendered(count):
            return subprocess.CompletedProcess([], 0, canonical({'token_ids': [1]*count, 'rendered_text': 'fixture'}), '')
        with patch('behaviorlab.mtplx.subprocess.run', return_value=rendered(n)):
            self.assertEqual(mtplx.preflight(self.payload, self.model)['input_tokens'], n)
        with patch('behaviorlab.mtplx.subprocess.run', return_value=rendered(n+1)):
            with self.assertRaisesRegex(ValueError, 'exceeds context'):
                mtplx.preflight(self.payload, self.model)
        class TooLong(FixtureHTTPBackend):
            def preflight(self, payload, model):
                raise ValueError('exceeds context')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td) / 'campaign'
            create_campaign(directory, self.protocol, self.registry)
            backend = TooLong()
            with self.assertRaisesRegex(ValueError, 'exceeds context'):
                execute(directory, backend=backend)
            self.assertEqual(backend.calls, 0)
            self.assertEqual(len(read_events(directory / 'events.jsonl')), 1)

    def test_capture_rejects_changed_tokens_sampling_seed_retry_and_policy(self):
        data, evidence = self.evidence()
        mtplx.validate_response_evidence(data, self.payload, evidence)
        changes = [('prompt_token_ids', [11, 23]), ('temperature', 0.5), ('requested_seed', 8),
                   ('model_id', 'wrong'), ('phase', 'dispatched')]
        for key, value in changes:
            altered = copy.deepcopy(evidence); altered['capture'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                mtplx.validate_response_evidence(data, self.payload, altered)
        for group, key, value in [('observability', 'request_enable_thinking', False),
                ('observability', 'request_session_bank_bypass', False),
                ('observability', 'preserve_thinking_effective', True),
                ('outcome', 'resolved_seed', 8), ('outcome', 'attempts', 2)]:
            altered = copy.deepcopy(evidence); altered['capture'][group][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                mtplx.validate_response_evidence(data, self.payload, altered)

    def test_capture_bytes_usage_and_finish_reason_are_verified(self):
        data, evidence = self.evidence()
        content = canonical(evidence['capture']).encode()
        evidence.update(capture_sha256=sha256(content), capture_bytes_base64=base64.b64encode(content).decode())
        mtplx.validate_response_evidence(data, self.payload, evidence)
        evidence['capture']['top_k'] = 10
        with self.assertRaisesRegex(ValueError, 'capture bytes'):
            mtplx.validate_response_evidence(data, self.payload, evidence)
        data, evidence = self.evidence(); data['usage']['prompt_tokens'] = 3
        with self.assertRaisesRegex(ValueError, 'Usage'):
            mtplx.validate_response_evidence(data, self.payload, evidence)

    def test_missing_capture_does_not_discard_http_response(self):
        response = wire({'id': 'fixture'})
        backend = HTTPBackend(); backend._preflight[fingerprint(self.payload)] = {}
        with patch('behaviorlab.backends.http_request', return_value=response), \
             patch('behaviorlab.mtplx.capture_response', side_effect=OSError('private detail')):
            result = backend.generate(self.payload, self.model)
        self.assertEqual(result.raw, response.raw)
        self.assertEqual(result.evidence['mtplx_capture_error'], 'OSError')
        self.assertNotIn('private detail', canonical(result.evidence))

    def test_thinking_is_archived_but_excluded_from_partner_and_own_history(self):
        data, evidence = self.evidence(); response = wire(data); response.evidence['mtplx'] = evidence
        parsed = parse_live(response.raw, self.payload, self.model, response.evidence)
        self.assertIn('private trace', parsed['thinking'])
        turn = Turn('one', None, 'root', 1, 'X', parsed['content'], parsed['thinking'])
        for speaker in ('X', 'Y'):
            history = messages(self.protocol, [turn], speaker, 'F')
            self.assertNotIn('private trace', canonical(history))
            self.assertIn('Answer', canonical(history))

    def test_disabled_reasoning_rejects_unexpected_trace(self):
        data, evidence = self.evidence()
        payload = copy.deepcopy(self.payload); payload['enable_thinking'] = False
        evidence['capture']['observability']['request_enable_thinking'] = False
        response = wire(data); response.evidence['mtplx'] = evidence
        self.assertEqual(parse_live(response.raw, payload, self.model, response.evidence)['invalid_reason'],
                         'unexpected_thinking_output')

    def test_gateway_rejects_cloud_route_before_generation_without_retaining_keys(self):
        row = copy.deepcopy(self.row)
        row.update(backend='webui-mtplx', endpoint='http://localhost:8080', server_version='0.11.3')
        model = Registry.from_dict({'schema': 'behaviorlab.models/2', 'models': [row]}).model('ON')
        catalog = {'data': [{'id': model.tag, 'owned_by': 'openai', 'urlIdx': 0}]}
        config = {'OPENAI_API_BASE_URLS': ['https://example.com/v1'], 'OPENAI_API_KEYS': ['secret']}
        with patch('behaviorlab.mtplx.verify', return_value={}), patch('behaviorlab.backends.json_request',
                side_effect=[{'version': '0.11.3'}, catalog, config]):
            with self.assertRaisesRegex(ValueError, 'verified local engine'):
                HTTPBackend().verify(model)


if __name__ == '__main__':
    unittest.main()
