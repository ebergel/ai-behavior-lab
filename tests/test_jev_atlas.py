import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from behaviorlab.common import canonical, fingerprint
from behaviorlab.explorer import Notes, make_server
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.jev_atlas import JevAtlas, MODEL, read_record, validate_response, write_record
from behaviorlab.jev_runner import execute
from behaviorlab.research_bundle import export_notebook
from behaviorlab.topic_atlas import TopicAtlas
from test_topic_atlas import run


def reply(payload, key=None):
    answers = {}
    for name, question in payload['questions'].items():
        if question['type'] == 'noul': answers[name] = {'type': 'noul', 'noul': 0.91}
        else:
            choices = list(question['criteria'])
            answers[name] = {'type': 'choice', 'choice': choices[0], 'confidence': 0.8,
                             'probabilities': {c: 1.0 if c == choices[0] else 0.0 for c in choices}}
    return 200, json.dumps({'model': MODEL, 'answers': answers, 'usage': {'input_tokens': 900}})


class JevAtlasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name); self.notes = Notes(self.workspace / 'explorer' / 'notes.sqlite')
        self.atlas = TopicAtlas(self.notes); self.studies = ResearchCollections(self.notes)
        self.store = JevAtlas(self.workspace)
        self.r = run(); self.catalog = SimpleNamespace(runs={'r': self.r}, indexed_at='now', issues=[])
        self.original = fingerprint(export_notebook(self.notes.path.resolve()))
        self.dictionary = self.atlas.dictionary()

    def tearDown(self):
        self.assertEqual(fingerprint(export_notebook(self.notes.path.resolve())), self.original)
        self.assertEqual(self.atlas.dictionary(), self.dictionary)

    def prepare(self, **kwargs):
        return self.store.prepare({'count': 6, 'topics': ['emergence', 'consciousness'], **kwargs},
                                  self.catalog, self.atlas, self.studies)['id']

    def test_freeze_reproducible_sampling_source_splits_and_independent_dictionary(self):
        a = self.store.plan(self.prepare(count=4)); b = self.store.plan(self.prepare(count=4))
        self.assertEqual(a['items'], b['items']); self.assertNotEqual(a['id'], b['id'])
        self.assertEqual(a['dictionary'], self.dictionary)
        self.assertEqual(len({i['split'] for i in a['items']}), 1)
        for item in a['items']:
            self.assertNotIn('models', self.store.payload(a, item)['state'])
            target_index = next(i for i, m in enumerate(self.r['messages']) if m['id'] == item['message_id'])
            self.assertEqual([m['id'] for m in item['context']], [m['id'] for m in self.r['messages'][max(0, target_index-2):target_index]])

    def test_sampling_excludes_branches_synthetic_missing_capped_and_large_targets(self):
        self.catalog.runs.update(branch=run('branch', leaves=['a', 'b']), synthetic=run('synthetic', kind='synthetic'))
        self.r['messages'][0]['text'] = None
        self.r['messages'][1]['status'] = 'cap'
        self.r['messages'][5]['text'] = 'x' * 19000
        plan = self.store.plan(self.prepare())
        self.assertTrue(all(i['run_id'] == 'r' and i['turn'] in (3, 4, 5) for i in plan['items']))
        self.assertEqual(plan['sampling']['excluded']['branched_runs'], 1)
        self.assertEqual(plan['sampling']['excluded']['unavailable_or_partial_messages'], 2)

    def test_preparation_and_review_never_dispatch_and_preserve_old_notebook(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('No dispatch')):
            identity = self.prepare(); d = self.store.detail(identity, self.catalog, self.atlas)
            self.assertTrue(all(r['status'] == 'pending' and r['answers'] is None for r in d['rows']))
            item = d['rows'][0]
            body = {'batch': identity, 'item_id': item['id'], 'topic_id': 'emergence', 'label': 'uncertain', 'note': 'A question'}
            first = self.store.save_review(body, self.catalog)
            second = self.store.save_review(dict(body, label='present', revision=1), self.catalog)
            self.assertEqual(second['revision'], 2); self.assertEqual(first['author'], 'Local researcher')
            with self.assertRaisesRegex(ValueError, 'reload'): self.store.save_review(body, self.catalog)
            detail = self.store.export(identity, self.catalog, self.atlas)
            self.assertEqual(len(detail['review_history']), 2)
            self.assertEqual(detail['reviews'][0]['quote'], item['text'])
            self.assertEqual(detail['requests'], [])

    def test_completed_resume_skips_paid_calls_and_exports_exact_responses(self):
        identity = self.prepare(); calls = []
        def send(payload, key): calls.append(payload); return reply(payload)
        first = execute(self.workspace, identity, send=send, max_calls=2)
        self.assertEqual(first['complete'], 2)
        result = execute(self.workspace, identity, send=send)
        self.assertEqual(result['complete'], 6); self.assertEqual(len(calls), 6)
        self.assertAlmostEqual(result['cost_usd'], 6*900*0.042/1_000_000)
        execute(self.workspace, identity, send=lambda *a: self.fail('Duplicate dispatch'))
        exported = self.store.export(identity, self.catalog, self.atlas)
        self.assertEqual(len(exported['requests']), 6); self.assertEqual(len(exported['responses']), 6)
        self.assertEqual(json.loads(exported['responses'][0]['raw_text'])['model'], MODEL)

    def test_interrupted_dispatch_is_unknown_and_never_retried(self):
        identity = self.prepare()
        def interrupted(*args): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): execute(self.workspace, identity, send=interrupted)
        rows = self.store.results(self.store.plan(identity))
        self.assertEqual(sum(r['status'] == 'unresolved' for r in rows), 1)
        with self.assertRaisesRegex(ValueError, 'no automatic retry'):
            execute(self.workspace, identity, send=lambda *a: self.fail('Retry'))

    def test_http_transport_schema_version_and_missing_usage_fail_closed(self):
        for kind in ('http', 'transport', 'schema', 'version', 'usage'):
            with self.subTest(kind=kind):
                identity = self.prepare()
                def send(payload, key):
                    if kind == 'http': return 429, '{"error":"busy"}'
                    if kind == 'transport': raise OSError('sensitive credentials should not appear')
                    status, raw = reply(payload); obj = json.loads(raw)
                    if kind == 'schema': obj['answers']['topic_emergence']['noul'] = float('nan')
                    if kind == 'version': obj['model'] = 'jev-latest'
                    if kind == 'usage': obj.pop('usage')
                    return status, json.dumps(obj)
                result = execute(self.workspace, identity, send=send)
                self.assertEqual(result['started'], 1); self.assertEqual(result['failed'], 1)
                self.assertEqual(result['unknown_cost_calls'], 1)
                rows = self.store.results(self.store.plan(identity)); self.assertIsNone(rows[0]['answers'])
                self.assertNotIn('sensitive credentials', str(self.store.export(identity, self.catalog, self.atlas)))
                with self.assertRaises(ValueError): execute(self.workspace, identity, send=send)

    def test_source_changes_disable_reviews_and_plan_tampering_is_detected(self):
        identity = self.prepare(); item = self.store.plan(identity)['items'][0]
        self.r['source']['sha256'] = 'different'
        self.assertFalse(self.store.detail(identity, self.catalog, self.atlas)['rows'][0]['source_current'])
        with self.assertRaisesRegex(ValueError, 'Source changed'):
            self.store.save_review({'batch': identity, 'item_id': item['id'], 'topic_id': 'emergence', 'label': 'present'}, self.catalog)
        path = self.store.batch_path(identity) / 'plan.json'; text = json.loads(path.read_text()); text['model'] = 'other'
        path.write_text(json.dumps(text))
        with self.assertRaisesRegex(ValueError, 'checksum'): self.store.plan(identity)

    def test_source_reviews_and_errors_survive_reopen_and_atomic_records_refuse_overwrite(self):
        identity = self.prepare(); plan = self.store.plan(identity)
        with self.assertRaises(FileExistsError): write_record(self.store.batch_path(identity) / 'plan.json', {'replace': True})
        self.assertEqual(JevAtlas(self.workspace).plan(identity), plan)
        with self.assertRaises(ValueError): self.store.batch_path('../outside')

    def test_budget_reservation_and_software_drift_block_before_dispatch(self):
        identity = self.prepare()
        with patch('behaviorlab.jev_runner.software_identity', return_value={}):
            with self.assertRaisesRegex(ValueError, 'software changed'):
                execute(self.workspace, identity, send=lambda *a: self.fail('Dispatch'))
        plan = self.store.plan(identity)
        path = self.store.batch_path(identity) / 'plan.json'; path.unlink()
        plan.pop('sha256'); plan['budget']['usd_ceiling'] = 0.001
        write_record(path, plan)
        with self.assertRaisesRegex(ValueError, 'reserved budget'):
            execute(self.workspace, identity, send=lambda *a: self.fail('Dispatch'))
        self.assertFalse((path.parent / 'requests').exists())

    def test_http_csrf_and_endpoint_cannot_run_inference(self):
        with patch('behaviorlab.explorer.ThreadingHTTPServer', side_effect=lambda address, handler: SimpleNamespace(server_port=8765, handler=handler)):
            server = make_server(self.workspace / 'http-fixture')
        def call(method, path, body=None, headers=None):
            h = server.handler.__new__(server.handler); h.server = server; h.path = path
            raw = canonical(body).encode() if body is not None else b''
            h.headers = {'Host': '127.0.0.1:8765', 'Content-Type': 'application/json', 'Content-Length': str(len(raw)), **(headers or {})}
            h.rfile = io.BytesIO(raw); captured = []
            h.send = lambda data, status=200, **kwargs: captured.append((status, data))
            getattr(h, 'do_' + method)(); return captured[0]
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('Explorer dispatched')):
            self.assertEqual(call('GET', '/api/jev-atlas')[0], 200)
            self.assertEqual(call('GET', '/jev-atlas.js')[0], 200)
            self.assertEqual(call('POST', '/api/jev-atlas/prepare', {})[0], 403)
            token = call('GET', '/api/bootstrap')[1]['token']
            headers = {'Origin': 'http://127.0.0.1:8765', 'X-Explorer-Token': token}
            self.assertEqual(call('POST', '/api/jev-atlas/run', {}, headers)[0], 404)


if __name__ == '__main__': unittest.main()
