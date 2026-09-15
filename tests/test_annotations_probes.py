import copy
import json
from pathlib import Path
import tempfile
import unittest

from behaviorlab.annotations import (CODEBOOK, DIMENSIONS, annotation_report, create_packet,
    import_annotations, mechanics)
from behaviorlab.common import canonical, fingerprint, read_json
from behaviorlab.history import Turn
from behaviorlab.journal import read_events
from behaviorlab.probes import (create_batch, execute_probes, probe_report, probe_request,
    reconstruct, score_content, scheduled_jobs, validate_plan, export_probes)
from behaviorlab.runner import FakeBackend, NeedsAttention, create_campaign, execute
from behaviorlab.protocol import Protocol
from test_core import setup_protocol


class Stopped(BaseException):
    pass


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.base = Path(self.tmp.name)
        _, self.registry, self.protocol = setup_protocol()
        self.main = self.base/'main'
        create_campaign(self.main, self.protocol, self.registry)
        execute(self.main)
        self.original = (self.main/'events.jsonl').read_bytes()
    def tearDown(self):
        self.assertEqual((self.main/'events.jsonl').read_bytes(), self.original)
        self.tmp.cleanup()

    def packet(self):
        directory = self.base/'review'; create_packet(self.main, directory)
        packet = read_json((directory/'packet.json').read_text())
        submission = read_json((directory/'ratings.template.json').read_text())
        submission['rater'] = {'id': 'test-rater', 'kind': 'model'}
        for r in submission['ratings']:
            for d in r['dimensions'].values(): d['status'] = 'coded'
        return directory, packet, submission

    def test_packet_masks_metadata_and_deduplicates_shared_prefix(self):
        directory, packet, _ = self.packet()
        text = canonical(packet)
        for value in ('AB-r01', self.registry.model('A').tag, 'history_policy', 'model_digest', 'root_index'):
            self.assertNotIn(value, text)
        targets = [m['id'] for w in packet['windows'] for m in w['messages']]
        self.assertEqual(len(targets), len(set(targets)))
        self.assertEqual(len(targets), 14)
        self.assertEqual({m['speaker'] for w in packet['windows'] for m in w['messages']}, {'P', 'Q'})
        self.assertTrue((directory/'key.private.json').exists())

    def test_annotations_require_completed_assessments_and_exact_evidence(self):
        directory, packet, s = self.packet()
        bad = copy.deepcopy(s); bad['ratings'][0]['dimensions']['experience']['status'] = 'unreviewed'
        with self.assertRaisesRegex(ValueError, 'Unreviewed'): import_annotations(directory, bad)
        target = s['ratings'][0]['target']
        text = next(m['text'] for w in packet['windows'] for m in w['messages'] if m['id'] == target)
        # Fixture evidence validates the storage contract, not the truth of this label.
        d = s['ratings'][0]['dimensions']['experience']; d['labels'] = ['discussion']
        d['evidence'] = [{'label': 'discussion', 'message': target, 'start': 0, 'end': len(text), 'quote': text}]
        bad = copy.deepcopy(s); bad['ratings'][0]['dimensions']['experience']['evidence'][0]['quote'] += 'invented'
        with self.assertRaisesRegex(ValueError, 'quote/offset'): import_annotations(directory, bad)
        good = import_annotations(directory, s)
        self.assertTrue(import_annotations(directory, s)['already_present'])
        revised = copy.deepcopy(s); revised['ratings'][0]['notes'] = 'revised'
        with self.assertRaisesRegex(ValueError, 'supersede'): import_annotations(directory, revised)
        revised['supersedes'] = good['annotation_id']; import_annotations(directory, revised)
        self.assertEqual(len(list((directory/'annotations').glob('*.json'))), 2)
        report = annotation_report(directory)
        self.assertEqual(len(report['active_raters']), 1)
        self.assertEqual(report['independent_human_agreement'], [])

    def test_unknown_is_not_absence_and_small_windows_do_not_trigger_threshold(self):
        directory, _, s = self.packet()
        for r in s['ratings']: r['dimensions']['nonseparation']['status'] = 'insufficient_context'
        import_annotations(directory, s)
        windows = annotation_report(directory)['active_raters'][0]['windows']
        self.assertTrue(all(w['explicit_proportion_among_coded'] is None and w['sustained_explicit_expression'] is None for w in windows))

    def test_six_message_threshold_requires_three_endorsements_and_both_speakers(self):
        d, registry, _ = setup_protocol()
        d['segments'] = [dict(d['segments'][0], stop=6)]
        d['roots'][0]['segment_order'] = ['prefix']
        campaign = self.base/'six'; create_campaign(campaign, Protocol.from_dict(d,registry),registry); execute(campaign)
        folder = self.base/'six-review'; create_packet(campaign,folder)
        packet = read_json((folder/'packet.json').read_text())
        s = read_json((folder/'ratings.template.json').read_text()); s['rater']={'id':'fixture','kind':'model'}
        for r in s['ratings']:
            for assessment in r['dimensions'].values(): assessment['status']='coded'
        def endorse(indices):
            for i,r in enumerate(s['ratings']):
                dim=r['dimensions']['nonseparation']; dim.update(labels=[],evidence=[])
                if i in indices:
                    m=packet['windows'][0]['messages'][i]
                    dim.update(labels=['self_endorsement'],evidence=[{'label':'self_endorsement','message':m['id'],'start':0,'end':len(m['text']),'quote':m['text']}])
        endorse([0,1,2]); record=import_annotations(folder,s)
        self.assertIs(annotation_report(folder)['active_raters'][0]['windows'][0]['sustained_explicit_expression'],True)
        s['supersedes']=record['annotation_id']; endorse([0,2,4]); record=import_annotations(folder,s)
        self.assertIs(annotation_report(folder)['active_raters'][0]['windows'][0]['sustained_explicit_expression'],False)
        s['supersedes']=record['annotation_id']; s['ratings'][1]['dimensions']['nonseparation']['status']='insufficient_context'; import_annotations(folder,s)
        self.assertIsNone(annotation_report(folder)['active_raters'][0]['windows'][0]['sustained_explicit_expression'])

    def test_unavailable_descendants_are_missing_not_semantic_negatives(self):
        class Capped(FakeBackend):
            def generate(self,payload):
                raw=super().generate(payload); d=read_json(raw)
                if self.calls==2: d['done_reason']='length'
                return canonical(d)
        campaign=self.base/'capped'; create_campaign(campaign,self.protocol,self.registry); execute(campaign,backend=Capped())
        folder=self.base/'capped-review'; result=create_packet(campaign,folder)
        self.assertEqual(result['targets'],1); self.assertEqual(result['unavailable_targets'],13)
        report=annotation_report(folder); self.assertEqual(report['planned_target_count'],14)
        self.assertEqual(report['active_raters'],[])
        mechanical=read_json((folder/'mechanics.json').read_text())
        self.assertEqual(sum(r['metrics'] is None for r in mechanical['rows']),13)
        probes=self.base/'capped-probes'; result=create_batch(campaign,probes,snapshot_turns=(2,6))
        self.assertEqual(result['planned_calls'],0); self.assertEqual(len(result['unavailable_snapshots']),5)

    def test_only_declared_unassisted_humans_enter_human_agreement(self):
        folder,_,s=self.packet()
        for identity,kind in [('one','human'),('two','human'),('helper','human_with_model_assistance')]:
            s['rater']={'id':identity,'kind':kind}; import_annotations(folder,s)
        rows=annotation_report(folder)['independent_human_agreement']
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]['coded_overlap'],14)
        self.assertEqual(rows[0]['observed_agreement'],1); self.assertFalse(rows[0]['at_least_120_double_coded'])

    def test_mechanics_empty_unicode_and_cycles_remain_distinct_from_semantics(self):
        def history(texts):
            return [Turn(str(i), str(i-1) if i else None, 'root', i+1, 'X' if i%2==0 else 'Y', t, None) for i,t in enumerate(texts)]
        empty = mechanics(history(['', '']))
        self.assertIsNone(empty['adjacent_lexical_jaccard']); self.assertEqual(empty['constant_suffix_messages'], 2)
        self.assertEqual(mechanics(history(['CAFÉ 空', 'café 空']))['adjacent_lexical_jaccard'], 1)
        self.assertFalse(mechanics(history(['CAFÉ 空', 'café 空']))['adjacent_exact_repeat'])
        self.assertEqual(mechanics(history(['a','b','a','b']))['two_message_cycle_suffix'], 4)
        self.assertEqual(mechanics(history(['a','a','a','a']))['two_message_cycle_suffix'], 0)
        self.assertTrue(mechanics(history(['🙂']))['symbols_only'])

    def batch(self, baselines=False):
        directory = self.base/'probes'
        create_batch(self.main, directory, snapshot_turns=(2,6), include_baselines=baselines)
        return directory

    def test_probe_history_roles_actual_restricted_ancestry_and_independence(self):
        directory = self.batch(True)
        meta, protocol, registry, *_ = reconstruct(read_events(directory/'events.jsonl'))
        plan = meta['plan']; jobs = plan['jobs']; self.assertEqual(len(jobs), 40)
        for job in jobs:
            payload, _, _ = probe_request(plan, job, protocol, registry)
            self.assertEqual(payload['messages'][-1]['role'], 'user')
            self.assertEqual(sum('Researcher probe' in m['content'] for m in payload['messages']), 1)
            if job['baseline']: self.assertEqual(len(payload['messages']), 2)
            if job['snapshot'].endswith(':RR:6') and not job['baseline']:
                self.assertEqual(len(payload['messages']), 4 if job['recipient']=='X' else 5)
        rf = next(s for s in plan['snapshots'] if s['node'].endswith(':RF:6'))
        self.assertTrue(any(t['node_id'].endswith(':R:4') for t in rf['history']))
        self.assertFalse(any(t['node_id'].endswith(':F:4') for t in rf['history']))
        before = canonical(plan)
        a, _, _ = probe_request(plan, jobs[0], protocol, registry); a['messages'][-1]['content'] = 'contaminated'
        self.assertEqual(canonical(plan), before)
        # Matched baseline pairs differ only in their input messages.
        for a,b in zip(jobs[::2], jobs[1::2]):
            pa, _, _ = probe_request(plan,a,protocol,registry); pb, _, _ = probe_request(plan,b,protocol,registry)
            self.assertEqual({k:v for k,v in pa.items() if k!='messages'}, {k:v for k,v in pb.items() if k!='messages'})

    def test_full_pilot_probe_counts_and_source_variants_are_balanced_per_recipient(self):
        snapshots = [{'node': str(n)} for n in range(100)]
        jobs = scheduled_jobs(snapshots, 10, False)
        self.assertEqual(len(jobs), 400)
        for recipient in ('X','Y'):
            values = [j['variant'] for j in jobs if j['recipient']==recipient and j['item']=='source']
            self.assertEqual([values.count(n) for n in range(4)], [25]*4)

    def test_probe_resume_reuses_saved_response_and_replay_makes_no_calls(self):
        directory = self.batch(); first = FakeBackend()
        def hook(stage, job):
            if stage == 'after_response': raise Stopped()
        with self.assertRaises(Stopped): execute_probes(directory, 1, first, hook)
        self.assertEqual(first.calls, 1)
        prefix = (directory/'events.jsonl').read_bytes()
        second = FakeBackend(); result = execute_probes(directory, 100, second)
        self.assertEqual(second.calls, 19); self.assertTrue(result['complete'])
        self.assertTrue((directory/'events.jsonl').read_bytes().startswith(prefix))
        before = (directory/'events.jsonl').read_bytes()
        third = FakeBackend(); execute_probes(directory, 100, third)
        self.assertEqual(third.calls, 0); self.assertEqual((directory/'events.jsonl').read_bytes(), before)
        self.assertEqual(result['requests'], 20)

    def test_unknown_probe_attempt_is_not_automatically_retried(self):
        directory = self.batch(); backend = FakeBackend()
        def hook(stage, job):
            if stage == 'after_request': raise Stopped()
        with self.assertRaises(Stopped): execute_probes(directory, 1, backend, hook)
        with self.assertRaises(NeedsAttention): execute_probes(directory, 1, backend)
        self.assertEqual(backend.calls, 0)

    def test_probe_display_labels_independent_requests_without_changing_evidence(self):
        directory=self.batch(); execute_probes(directory,20)
        raw=(directory/'events.jsonl').read_bytes(); export=export_probes(directory)
        chat=export['chats'][0]['chat']
        self.assertEqual(len(chat['messages']),21)
        self.assertIn('not one conversation',chat['messages'][0]['content'])
        self.assertTrue(chat['lab_evidence']['display_only'])
        self.assertEqual((directory/'events.jsonl').read_bytes(),raw)

    def test_probe_plan_tampering_and_response_tampering_are_detected(self):
        directory = self.batch(); events = read_events(directory/'events.jsonl')
        bad=copy.deepcopy(events); bad[0]['payload']['data_class']='research'
        with self.assertRaisesRegex(ValueError, 'data-class'): reconstruct(bad)
        plan = copy.deepcopy(events[0]['payload']['plan']); plan['jobs'][0]['seed'] += 1
        with self.assertRaisesRegex(ValueError, 'schedule'): validate_plan(plan)
        execute_probes(directory, 1)
        events = read_events(directory/'events.jsonl')
        event = next(e for e in events if e['kind']=='probe_result_saved')
        event['payload']['result']['status'] = 'correct'
        with self.assertRaisesRegex(ValueError, 'score differs'): reconstruct(events)

    def test_probe_scoring_distinguishes_wrong_answers_from_format_and_technical_failure(self):
        self.assertEqual(score_content('{"total":4,"blue":2}', {'total':4,'blue':2})['status'], 'correct')
        self.assertEqual(score_content('{"total":5,"blue":2}', {'total':4,'blue':2})['status'], 'incorrect')
        for text in ('Four, with two blue.', '```json\n{"total":4,"blue":2}\n```', '{"total":4.0,"blue":2}', '{"total":4,"total":5,"blue":2}'):
            self.assertEqual(score_content(text, {'total':4,'blue':2})['status'], 'needs_manual_review')
        self.assertEqual(score_content('{"speaker":" x ","color":"AMBER"}', {'speaker':'X','color':'amber'})['status'], 'correct')


if __name__ == '__main__': unittest.main()
