import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from behaviorlab.common import fingerprint
from behaviorlab.jev_atlas import MODEL, ENDPOINT, write_record, read_record
from behaviorlab.discourse_probe import ROOT, SPEC, VARIANTS, BUDGET, EXECUTION, software, questions, payload, select, execute, summary


def fixture(workspace):
    spec=json.loads(SPEC.read_text());samples=[{'id':str(i),'title':f'Test {i}','text':f'Test passage {i}.','kind':'transcript','model_label':'Fixture model','words':3,'run_id':f'r{i}','message_id':'m'} for i in range(48)]
    samples.extend(dict(c,kind='synthetic',words=len(c['text'].split())) for c in spec['controls'])
    plan={'model':MODEL,'endpoint':ENDPOINT,'spec':spec,'samples':samples,'conditions':{v:questions(spec,v) for v in VARIANTS},
          'items':[{'id':f'{i}-{v}','sample_id':sample['id'],'variant':v} for i,sample in enumerate(samples) for v in VARIANTS],
          'selection':{'method':'fixture'},'software_sha256':software(),'budget':BUDGET,'execution':EXECUTION,'interpretation':'Synthetic engineering test'}
    for item in plan['items']:item['request_sha256']=fingerprint(payload(plan,item))
    write_record(workspace/ROOT/'plan.json',plan);plan=read_record(workspace/ROOT/'plan.json')
    write_record(workspace/ROOT/'authorization.json',{'plan_sha256':plan['sha256'],'usd_ceiling':2,'explicit_confirmation':True,'endpoint':ENDPOINT,'unique_requests':180,'max_attempts':192})
    return plan


def response(p,k):return 200,json.dumps({'model':MODEL,'answers':{q:{'type':'noul','noul':.5} for q in p['questions']},'usage':{'input_tokens':100}})


class LensProbeTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.workspace=Path(self.tmp.name);self.plan=fixture(self.workspace)
    def tearDown(self):self.tmp.cleanup()

    def test_wording_conditions_share_state_but_do_not_leak_other_definitions(self):
        spec=self.plan['spec'];bare=questions(spec,'name_only');defined=questions(spec,'definition_only');named=questions(spec,'name_and_definition')
        for feature in spec['features']:
            key=feature['id']
            self.assertIn(feature['name'],bare[key]['instructions'])
            self.assertNotIn(feature['definition'],bare[key]['instructions'])
            self.assertIn(feature['definition'],defined[key]['instructions'])
            self.assertNotIn(feature['name'],defined[key]['instructions'])
            self.assertIn(feature['definition'],named[key]['instructions'])
        states=[payload(self.plan,i)['state'] for i in self.plan['items'][:3]]
        self.assertTrue(all(s==states[0] for s in states));self.assertEqual(set(states[0]),{'target_passage'})

    def test_selection_excludes_blank_reserved_and_shared_lineage_without_using_scores(self):
        items=[{'id':str(i),'model':f'm{i%3}','lineage':f'l{i//2}','text':'visible','score':i} for i in range(20)]
        items[0]['text']=' \n';reserved={'l1'}
        a=select(items,reserved,count=7)
        for i in items:i['score']=-i['score']
        b=select(items,reserved,count=7)
        self.assertEqual([i['id'] for i in a],[i['id'] for i in b]);self.assertEqual(len({i['lineage'] for i in a}),7)
        self.assertFalse(any(i['lineage'] in reserved or not i['text'].strip() for i in a))
        with self.assertRaisesRegex(ValueError,'Duplicate'):select(items+[items[0]],reserved)

    def test_finite_canary_resume_and_completed_no_dispatch(self):
        calls=[]
        def send(p,k):calls.append(p);return response(p,k)
        self.assertEqual(execute(self.workspace,max_calls=3,send=send,key='test',sleep=lambda _:None)['complete'],3)
        result=execute(self.workspace,send=send,key='test',sleep=lambda _:None)
        self.assertEqual((result['complete'],result['attempts'],len(calls)),(180,180,180))
        with patch('behaviorlab.discourse_probe.credential',side_effect=AssertionError('Completed')):
            self.assertEqual(execute(self.workspace)['complete'],180)

    def test_invalid_response_is_preserved_and_not_retried(self):
        result=execute(self.workspace,send=lambda p,k:(200,'{}'),key='test',sleep=lambda _:None)
        self.assertEqual(result['stopped'],['invalid']);self.assertGreater(result['unknown_reserved_usd'],0)
        with self.assertRaisesRegex(ValueError,'uncertain'):execute(self.workspace,send=lambda p,k:self.fail())

    def test_durable_unknown_request_blocks_redispatch(self):
        i=self.plan['items'][0]
        write_record(self.workspace/ROOT/'attempts'/i['id']/'01.request.json',{'plan_sha256':self.plan['sha256'],'item_id':i['id'],'attempt':1,'payload':payload(self.plan,i)})
        with self.assertRaisesRegex(ValueError,'uncertain'):execute(self.workspace,send=lambda p,k:self.fail())

    def test_overload_only_retry_retains_unknown_reservation(self):
        execute(self.workspace,max_calls=1,send=lambda p,k:(529,'overload'),key='test',sleep=lambda _:None)
        result=execute(self.workspace,max_calls=1,send=response,key='test',sleep=lambda _:None)
        self.assertEqual((result['complete'],result['attempts']),(1,2));self.assertGreater(result['unknown_reserved_usd'],0)

    def test_freeze_rejects_changed_software(self):
        with patch('behaviorlab.discourse_probe.software',return_value={}):
            with self.assertRaisesRegex(ValueError,'Software'):execute(self.workspace,send=lambda p,k:self.fail())

    def test_missing_explicit_confirmation_never_reads_credential(self):
        (self.workspace/ROOT/'authorization.json').unlink()
        with patch('behaviorlab.discourse_probe.credential',side_effect=AssertionError('Must not read key')):
            with self.assertRaisesRegex(ValueError,'explicit dispatch'):execute(self.workspace)
        self.assertEqual(summary(self.workspace/ROOT,self.plan)['attempts'],0)

    def test_label_is_only_change_between_matched_defined_conditions(self):
        for feature in self.plan['spec']['features']:
            key=feature['id'];conditions=self.plan['conditions']
            self.assertEqual(conditions['name_and_definition'][key]['instructions'],
                             conditions['definition_only'][key]['instructions']+'\nLabel: '+feature['name'])
        self.assertEqual(len(self.plan['spec']['features']),27)
        self.assertEqual(len({f['id'] for f in self.plan['spec']['features']}),27)
        self.assertEqual(sum(f['family']=='thinkers' for f in self.plan['spec']['features']),16)

    def test_view_preserves_unknowns_separate_controls_and_paired_denominators(self):
        from behaviorlab.discourse_view import build
        a=build(self.workspace)
        self.assertEqual(a['status'],'prepared')
        self.assertEqual(a['groups']['transcript'][0]['conditions']['name_only']['n'],0)
        self.assertIsNone(a['groups']['transcript'][0]['conditions']['name_only']['mean'])
        execute(self.workspace,max_calls=1,send=response,key='test',sleep=lambda _:None)
        a=build(self.workspace)
        self.assertEqual(a['status'],'in_progress')
        self.assertEqual(a['groups']['transcript'][0]['conditions']['name_only']['n'],1)
        self.assertEqual(a['groups']['transcript'][0]['contrasts']['name_only']['n'],0)
        execute(self.workspace,send=response,key='test',sleep=lambda _:None)
        a=build(self.workspace)
        self.assertEqual(a['status'],'complete')
        self.assertEqual(a['groups']['transcript'][0]['contrasts']['name_only']['n'],48)
        self.assertEqual(a['groups']['synthetic'][0]['contrasts']['name_only']['n'],12)
        self.assertEqual(a['groups']['synthetic'][0]['contrasts']['name_only']['mean_difference'],0)
        self.assertTrue(all(v==0 for row in a['author_cue_differences'].values() for values in row.values() for v in values.values()))

    def test_bad_confirmation_scope_and_exhausted_overload_do_not_redispatch(self):
        from behaviorlab.discourse_probe import receipts
        item=self.plan['items'][0]
        for number in range(1,4):
            path=self.workspace/ROOT/'attempts'/item['id']/f'{number:02d}.request.json'
            write_record(path,{'plan_sha256':self.plan['sha256'],'item_id':item['id'],'attempt':number,'payload':payload(self.plan,item)})
            req=read_record(path)
            write_record(path.with_name(f'{number:02d}.response.json'),{'request_sha256':req['sha256'],'http_status':529,'raw_text':'overload'})
        with self.assertRaisesRegex(ValueError,'allowance exhausted'):execute(self.workspace,send=lambda p,k:self.fail())
        self.assertEqual(len(receipts(self.workspace/ROOT,self.plan)[1]),3)
