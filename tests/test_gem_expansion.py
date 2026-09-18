import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.common import fingerprint
from behaviorlab.gem_expansion import EXPANSION, EXECUTION, select, length_band, execute, software
from behaviorlab.gem_plan import PILOT, payload
from behaviorlab.gem_runner import execute as original_execute, summary
from behaviorlab.jev_atlas import read_record, write_record
from test_gem_finder import fixture, answer


class ExpansionSelectionTests(unittest.TestCase):
    def test_selection_uses_model_and_length_but_not_scores_and_caps_shared_lineages(self):
        candidates=[{'id':str(i),'lineage':'l'+str(i//6),'model':'m'+str(i%2),
                     'words':[10,50,100,200,400,50][i%6],'topic_scores':{'b':i}} for i in range(120)]
        prior=[dict(candidates[0])]
        selected,audit=select(candidates,prior,50)
        self.assertNotIn('0',{i['id'] for i in selected})
        self.assertEqual(audit['combined_max_per_lineage'],3)
        self.assertEqual(audit['combined_lineages'],20)
        self.assertEqual(len({i['id'] for i in selected}),50)
        for i in candidates:i['topic_scores']['b']=10000-i['topic_scores']['b']
        again,_=select(candidates,prior,50)
        self.assertEqual([i['id'] for i in selected],[i['id'] for i in again])
        with self.assertRaisesRegex(ValueError,'lineage cap'):select(candidates,prior,60)

    def test_length_band_boundaries_and_duplicate_rejection(self):
        self.assertEqual([length_band(n) for n in (25,26,75,76,150,151,300,301)],
                         ['1–25','26–75','26–75','76–150','76–150','151–300','151–300','301+'])
        with self.assertRaisesRegex(ValueError,'Duplicate'):select([{'id':'x'},{'id':'x'}],[],1)


class ExpansionRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.workspace=Path(self.tmp.name)
        base,self.catalog=fixture(self.workspace,2)
        original_execute(self.workspace,send=lambda p,k:(200,json.dumps(answer(p))),key='secret',sleep=lambda _:None)
        self.base_bytes=(self.workspace/PILOT/'plan.json').read_bytes()
        plan={**base,'schema':'behaviorlab.gem-expansion/1','parent_plan_sha256':base['sha256'],
              'software_sha256':software(),'execution':dict(EXECUTION),
              'budget':dict(base['budget'],max_attempts=29,retry_allowance=27),
              'items':[dict(i,id='new-'+i['id']) for i in base['items']]}
        plan.pop('sha256');write_record(self.workspace/EXPANSION/'plan.json',plan)
        self.plan=read_record(self.workspace/EXPANSION/'plan.json')
        write_record(self.workspace/EXPANSION/'authorization.json',{'plan_sha256':self.plan['sha256'],'usd_ceiling':2})
    def tearDown(self):self.tmp.cleanup()

    def test_finite_execution_resume_and_original_preservation(self):
        calls=[]
        def send(p,k):calls.append(p);return 200,json.dumps(answer(p))
        first=execute(self.workspace,max_calls=1,send=send,key='secret')
        self.assertEqual((first['complete'],first['attempts']),(1,1))
        final=execute(self.workspace,send=send,key='secret')
        self.assertEqual((final['complete'],final['attempts']),(2,2))
        with patch('behaviorlab.gem_expansion.credential',side_effect=AssertionError('No credential needed')):
            self.assertEqual(execute(self.workspace)['complete'],2)
        self.assertEqual(len(calls),2)
        self.assertEqual((self.workspace/PILOT/'plan.json').read_bytes(),self.base_bytes)

    def test_failed_or_uncertain_response_is_not_retried(self):
        result=execute(self.workspace,max_calls=1,send=lambda p,k:(200,'{}'),key='secret')
        self.assertEqual(result['stopped'],['invalid'])
        with self.assertRaisesRegex(ValueError,'uncertain'):execute(self.workspace,send=lambda p,k:self.fail())

    def test_request_marker_without_response_is_not_redispatched(self):
        item=self.plan['items'][0]
        write_record(self.workspace/EXPANSION/'attempts'/item['id']/'01.request.json',
                     {'plan_sha256':self.plan['sha256'],'item_id':item['id'],'attempt':1,'payload':payload(self.plan,item)})
        with self.assertRaisesRegex(ValueError,'uncertain'):execute(self.workspace,send=lambda p,k:self.fail())

    def test_overload_retains_reservation_and_only_retries_that_item(self):
        execute(self.workspace,max_calls=1,send=lambda p,k:(529,'overload'),key='secret')
        # Advance monotonic time so the production backoff remains frozen without waiting in tests.
        clock=iter(range(0,100000,100))
        with patch('behaviorlab.gem_expansion.time.monotonic',side_effect=lambda:next(clock)):
            result=execute(self.workspace,send=lambda p,k:(200,json.dumps(answer(p))),key='secret')
        self.assertEqual((result['complete'],result['attempts']),(2,3))
        self.assertGreater(result['unknown_reserved_usd'],0)

    def test_frozen_software_is_enforced(self):
        with patch('behaviorlab.gem_expansion.software',return_value={}):
            with self.assertRaisesRegex(ValueError,'software'):execute(self.workspace,send=lambda p,k:self.fail())

class ExpansionReaderTests(unittest.TestCase):
    def setUp(self):
        from behaviorlab.explorer import Notes
        from behaviorlab.gem_finder import GemFinder
        self.tmp=tempfile.TemporaryDirectory();self.workspace=Path(self.tmp.name)
        base,self.catalog=fixture(self.workspace,2)
        self.base=base
        original_execute(self.workspace,send=lambda p,k:(200,json.dumps(answer(p))),key='test',sleep=lambda _:None)
        item=dict(base['items'][0],id='fresh',message_id='m2',text='A genuinely different passage.',sample_role='expansion')
        self.catalog.runs['r0']['messages'].append({'id':'m2','kind':'message','text':item['text'],'segment':'conversation'})
        item['request_sha256']=fingerprint(payload(base,item))
        plan={**base,'schema':'behaviorlab.gem-expansion/1','parent_plan_sha256':base['sha256'],
              'reference_sha256':fingerprint([]),'software_sha256':software(),'execution':dict(EXECUTION),
              'budget':dict(base['budget'],unique_requests=1,max_attempts=28,retry_allowance=27),'items':[item]}
        plan.pop('sha256');write_record(self.workspace/EXPANSION/'plan.json',plan)
        self.plan=read_record(self.workspace/EXPANSION/'plan.json')
        write_record(self.workspace/EXPANSION/'authorization.json',{'plan_sha256':self.plan['sha256'],'usd_ceiling':2})
        self.store=GemFinder(self.workspace,Notes(self.workspace/'notes.sqlite'),self.catalog)
    def tearDown(self):self.tmp.cleanup()

    def test_pending_expansion_is_unknown_and_cohort_totals_are_separate(self):
        combined=self.store.detail();original=self.store.detail(batch='pilot')
        fresh=self.store.detail(batch=Path(EXPANSION).name)
        self.assertEqual((combined['summary']['complete'],combined['summary']['planned']),(2,3))
        self.assertEqual(combined['lineages'],2)
        self.assertEqual((len(original['items']),len(fresh['items'])),(2,1))
        self.assertEqual(fresh['items'][0]['answers'],{})
        self.assertEqual(fresh['items'][0]['assessment'],'pending')
        with self.assertRaisesRegex(ValueError,'Unknown Gem batch'):self.store.detail(batch='typo')
        execute(self.workspace,send=lambda p,k:(200,json.dumps(answer(p))),key='test')
        self.assertEqual(self.store.detail()['summary']['complete'],3)
        self.assertEqual(self.store.detail(batch='pilot')['summary']['complete'],2)
        self.assertAlmostEqual(self.store.detail(batch=Path(EXPANSION).name)['items'][0]['answers']['surprise']['normalized_score'],55)

    def test_expansion_reading_uses_its_own_plan_and_exports_both_samples(self):
        old=self.store.save({'run_id':'r0','message_id':'m1','source_sha256':'s0','exposure':'visible','author':'Codex'})
        new=self.store.save({'run_id':'r0','message_id':'m2','source_sha256':'s0','exposure':'visible'})
        self.assertEqual(old['plan_sha256'],self.base['sha256'])
        self.assertEqual(new['plan_sha256'],self.plan['sha256'])
        self.assertEqual(len(self.store.detail(batch='pilot')['items']),2)
        exported=self.store.export()
        self.assertEqual(len(exported['batches']),2)
        self.assertEqual(len(exported['history']),2)
        self.assertEqual(exported['plan'],self.base)

    def test_reader_rejects_incompatible_or_duplicate_expansion(self):
        from copy import deepcopy
        self.store.plan()
        for field,value,error in [('reference_sha256','different','reference'),('questions',{},'rubric')]:
            broken=deepcopy(self.plan);broken[field]=value
            with patch('behaviorlab.gem_finder.read_record',return_value=broken):
                with self.assertRaisesRegex(ValueError,error):self.store.batches()
        broken=deepcopy(self.plan);broken['items'][0]['message_id']='m1'
        with patch('behaviorlab.gem_finder.read_record',return_value=broken):
            with self.assertRaisesRegex(ValueError,'source message'):self.store.batches()

class ExpansionReportTests(unittest.TestCase):
    def test_descriptive_correlations_and_length_band_denominators(self):
        from behaviorlab.gem_expansion_report import correlation, describe
        self.assertIsNone(correlation([1,1,1],[2,3,4]))
        self.assertIsNone(correlation([1,2],[2,4]))
        self.assertAlmostEqual(correlation([1,2,3],[9,6,3]),-1)
        rows=[{'words':w,'lineage':'shared','model':'m','scores':{'expression':s}} for w,s in [(10,0),(20,80),(30,100)]]
        d=describe(rows,['expression'])
        self.assertEqual((d['n'],d['lineages']),(3,1))
        self.assertEqual(d['length_bands'],{'1–25':2,'26–75':1})
        self.assertEqual(d['axes']['expression']['at_least_80'],2)
