import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.common import fingerprint
from behaviorlab.jev_atlas import JevAtlas, write_record, read_record, questions_for, software_identity, MODEL, ENDPOINT
from behaviorlab.jev_coverage import freeze_coverage, build_inventory
from behaviorlab.jev_corpus import (packs_for, prepare_qualification, run_qualification,
    summarize_qualification, freeze_corpus)
from test_topic_atlas import run
from test_jev_atlas import reply


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.ws = Path(self.tmp.name); self.store = JevAtlas(self.ws)
        records = {}
        for n in range(5):
            r = run(str(n)); r['data_class'] = 'synthetic-test'; r['prompt'] = str(n)
            for m in r['messages']: m['kind'] = 'message'
            records[r['id']] = r
        records['0']['messages'][2]['text'] = 'Long content. ' * 1500
        records['0']['messages'][2]['status'] = 'cap'
        records['1']['messages'][0]['text'] = None
        self.catalog = SimpleNamespace(runs=records, issues=[])
        self.coverage = self.ws / 'coverage'; freeze_coverage(self.catalog, self.coverage, count=1)
        inv, items = build_inventory(self.catalog)
        control = next(i for i in items.values() if i['run_id'] == '1' and i['turn'] == 3)
        book = json.loads((Path(__file__).parents[1] / 'designs/jev-two-tier-v1.json').read_text())
        topics = [t['id'] for t in book['topics']]
        qs = questions_for(book['topics'], topics)
        self.source = {'schema': 'behaviorlab.jev-atlas/1', 'id': '0' * 24, 'model': MODEL,
            'endpoint': ENDPOINT, 'dictionary': book['topics'], 'dictionary_origin': 'independent-two-tier',
            'dictionary_version': book['version'], 'topic_groups': book['groups'],
            'questions': {k: qs[k] for k in qs if k.startswith('topic_')}, 'topics': topics,
            'thresholds': {'candidate': .8, 'unlikely': .2}, 'coverage_summary': inv['totals'],
            'items': [dict(control, sampling_stratum='root_sample')], 'title': 'Test source',
            'software_sha256': software_identity(), 'budget': {'max_calls': 1, 'usd_ceiling': .6}}
        write_record(self.store.batch_path(self.source['id']) / 'plan.json', self.source)
        self.dest = self.ws / 'qualification'

    def prepare(self):
        return prepare_qualification(self.ws, self.catalog, self.coverage, self.dest, self.source['id'])

    def complete(self):
        with patch('behaviorlab.jev_runner.credential', return_value='test'), patch('behaviorlab.jev_runner.transport', side_effect=reply):
            return run_qualification(self.ws, self.dest)

    def test_questions_partition_and_intact_unicode_context_are_preserved(self):
        p = self.prepare(); plans = [self.store.plan(a['batch']) for a in p['allocations']]
        self.assertEqual([len(x['questions']) for x in plans], [24, 29])
        self.assertEqual(set().union(*(set(x['questions']) for x in plans)), set(self.source['questions']))
        self.assertLess(max(p['request_bytes'].values()), 60000)
        for a, b in zip(plans[0]['items'], plans[1]['items']):
            self.assertEqual(self.store.payload(plans[0], a)['state'], self.store.payload(plans[1], b)['state'])
            original = next(m for m in self.catalog.runs[a['run_id']]['messages'] if m['id'] == a['message_id'])
            self.assertEqual(a['text'], original['text'])
        self.assertEqual(len(p['long_targets']), 3)  # target plus two windows retaining it as context
        with self.assertRaises(ValueError): self.prepare()

    def test_oversized_context_refuses_instead_of_truncating_or_skipping(self):
        self.catalog.runs['0']['messages'][2]['text'] = '界' * 25000
        other = self.ws / 'larger'; freeze_coverage(self.catalog, other, count=1)
        with self.assertRaisesRegex(ValueError, 'byte screen'):
            prepare_qualification(self.ws, self.catalog, other, self.dest, self.source['id'])
        self.assertFalse(self.dest.exists())

    def test_resume_and_complete_do_not_repeat_requests(self):
        p = self.prepare()
        with patch('behaviorlab.jev_runner.credential', return_value='test'), patch('behaviorlab.jev_runner.transport', side_effect=reply) as send:
            run_qualification(self.ws, self.dest, 1); self.assertEqual(send.call_count, 1)
            result = run_qualification(self.ws, self.dest); self.assertEqual(result['status'], 'complete')
            run_qualification(self.ws, self.dest); self.assertEqual(send.call_count, p['max_calls'])

    def test_failure_stops_other_pack_and_prevents_resume(self):
        p = self.prepare()
        with patch('behaviorlab.jev_runner.credential', return_value='test'), patch('behaviorlab.jev_runner.transport', return_value=(529, 'overload')) as send:
            self.assertEqual(run_qualification(self.ws, self.dest)['status'], 'stopped')
            with self.assertRaisesRegex(ValueError, 'Aggregate stopped'): run_qualification(self.ws, self.dest)
            self.assertEqual(send.call_count, 1)
        self.assertTrue(all(r['status'] == 'pending' for r in self.store.results(self.store.plan(p['allocations'][1]['batch']))))

    def test_corpus_reuses_exact_completed_requests_and_separates_reference_roots(self):
        protocol = self.prepare(); result = self.complete(); write_record(self.dest / 'summary.json', result)
        target = self.ws / 'corpus'
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('No dispatch')):
            out = freeze_corpus(self.ws, self.catalog, self.coverage, self.dest, target)
        plan = read_record(target / 'plan.json'); packet = read_record(target / 'reference-packet.json')
        self.assertEqual(out['counts']['visible_targets'], 29)
        self.assertEqual(out['counts']['reuse_requests'], protocol['max_calls'])
        self.assertEqual(out['counts']['new_calls'] + protocol['max_calls'], 58)
        self.assertEqual(len(plan['unavailable_positions']), 1)
        self.assertTrue(all(len(t['requests']) == 2 for t in plan['targets']))
        self.assertEqual(out['status'], 'prepared_not_dispatched')
        dev = {t['lineage'] for t in plan['targets'] if t['split'] == 'development'}
        self.assertFalse(dev & {t['lineage'] for t in packet['items']})
        self.assertTrue(all('answers' not in t and 'models' not in t for t in packet['items']))
        with self.assertRaises(ValueError): freeze_corpus(self.ws, self.catalog, self.coverage, self.dest, target)

    def test_corpus_freeze_rejects_changed_source_and_incomplete_qualification(self):
        self.prepare()
        write_record(self.dest / 'summary.json', summarize_qualification(self.ws, self.dest))
        with self.assertRaisesRegex(ValueError, 'must complete'):
            freeze_corpus(self.ws, self.catalog, self.coverage, self.dest, self.ws / 'corpus')
        self.catalog.runs['1']['messages'][2]['text'] = 'Changed evidence'
        with self.assertRaisesRegex(ValueError, 'Corpus changed'):
            prepare_qualification(self.ws, self.catalog, self.coverage, self.ws / 'changed', self.source['id'])

    def test_scope_audit_follows_actual_branch_history_and_actual_speaker(self):
        from scripts.audit_jev_corpus_scope import audit
        from behaviorlab.common import fingerprint
        r = self.catalog.runs['2']; ms = r['messages']
        for n, m in enumerate(ms):
            m['parent'] = ms[n-1]['id'] if n else None
            m['model'] = 'actual-' + m['speaker']
        ms[2]['status'] = 'cap'
        ms[4]['parent'] = ms[1]['id']  # another branch does not inherit this cap
        r['leaves'] = ['a', 'b']
        inv, _ = build_inventory(self.catalog); inv['sha256'] = fingerprint(inv)
        result = audit(self.catalog, inv)
        rows = {x['message_id']: x for x in result['targets']}
        self.assertFalse(rows[ms[3]['id']]['clean_observed_history'])
        self.assertTrue(rows[ms[5]['id']]['clean_observed_history'])
        self.assertEqual(rows[ms[5]['id']]['speaker_model'], ms[5]['model'])
        self.assertFalse(rows[self.catalog.runs['1']['messages'][5]['id']]['clean_observed_history'])
