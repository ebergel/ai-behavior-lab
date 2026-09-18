import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from behaviorlab import discourse_probe as old, discourse_portrait_probe as probe
from behaviorlab.common import fingerprint
from behaviorlab.jev_atlas import read_record, write_record
from behaviorlab.discourse_view import build, export_plan
from tests.test_discourse_probe import fixture, response

class PortraitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.workspace=Path(self.tmp.name)
        self.parent=fixture(self.workspace);self.spec=json.loads(probe.SPEC.read_text())
        p={**self.parent,'spec':self.spec,'conditions':{v:probe.questions(self.spec,v) for v in probe.VARIANTS},
           'software_sha256':probe.software(),'budget':probe.BUDGET,'execution':probe.EXECUTION}
        p.pop('sha256',None)
        p['items']=[{'id':f'{n}-{v}','sample_id':s['id'],'variant':v} for n,s in enumerate(p['samples']) for v in probe.VARIANTS]
        for item in p['items']:item['request_sha256']=fingerprint(probe.payload(p,item))
        write_record(self.workspace/probe.ROOT/'plan.json',p);self.plan=read_record(self.workspace/probe.ROOT/'plan.json')
    def tearDown(self):self.tmp.cleanup()
    def authorize(self):
        write_record(self.workspace/probe.ROOT/'authorization.json',{'explicit_confirmation':True,'plan_sha256':self.plan['sha256'],'endpoint':probe.ENDPOINT,'unique_requests':240,'max_attempts':252,'usd_ceiling':2})
    def test_preserves_every_old_question_and_changes_only_sixteen_portrait_questions(self):
        for v in old.VARIANTS:self.assertEqual(self.parent['conditions'][v],self.plan['conditions'][v])
        for before,after in zip(self.parent['spec']['features'],self.spec['features']):
            self.assertTrue(all(after[k]==v for k,v in before.items()))
            a=self.plan['conditions']['name_and_portrait'][after['id']];b=self.plan['conditions']['name_and_definition'][after['id']]
            if after['family']=='thinkers':
                self.assertNotEqual(a,b);self.assertIn(after['portrait'],a['instructions']);self.assertIn(after['recognition'],a['instructions'])
                self.assertNotIn(after['definition'],a['instructions']);self.assertNotIn(after['sources'][0]['url'],a['instructions'])
            else:self.assertEqual(a,b)
        self.assertEqual(len({i['id'] for i in self.plan['items']}),240)
        for item in self.plan['items']:self.assertEqual(set(probe.payload(self.plan,item)['state']),{'target_passage'})
    def test_new_release_requires_its_own_exact_authorization(self):
        with patch('behaviorlab.discourse_portrait_probe.credential',side_effect=AssertionError('No credential read')):
            with self.assertRaisesRegex(ValueError,'explicit dispatch'):probe.execute(self.workspace)
        self.assertEqual(probe.summary(self.workspace/probe.ROOT,self.plan)['attempts'],0)
    def test_new_view_and_export_select_the_new_plan_with_unknowns(self):
        v=build(self.workspace);self.assertEqual(export_plan(self.workspace)['sha256'],self.plan['sha256'])
        self.assertEqual(v['execution']['planned'],240);self.assertEqual(v['status'],'prepared')
        c=v['groups']['transcript'][0]['contrasts']['name_and_portrait']
        self.assertEqual(c['baseline'],'name_and_definition');self.assertEqual(c['n'],0);self.assertIsNone(c['mean_difference'])
    def test_four_condition_resume_and_contrast_use_exact_pairs(self):
        self.authorize();calls=[]
        def send(p,k):
            calls.append(p);status,raw=response(p,k);body=json.loads(raw)
            if 'What to recognize:' in p['questions']['f01']['instructions']:
                for q in body['answers']:body['answers'][q]['noul']=.7
            return status,json.dumps(body)
        with contextlib.redirect_stdout(io.StringIO()):
            probe.execute(self.workspace,max_calls=3,send=send,key='test',sleep=lambda _:None)
            v=build(self.workspace);self.assertEqual(v['groups']['transcript'][0]['contrasts']['name_and_portrait']['n'],0)
            probe.execute(self.workspace,max_calls=1,send=send,key='test',sleep=lambda _:None)
            v=build(self.workspace);c=v['groups']['transcript'][0]['contrasts']['name_and_portrait']
            self.assertEqual(c['n'],1);self.assertAlmostEqual(c['mean_difference'],.2)
            result=probe.execute(self.workspace,send=send,key='test',sleep=lambda _:None)
        self.assertEqual((result['complete'],len(calls)),(240,240))
        with patch('behaviorlab.discourse_portrait_probe.credential',side_effect=AssertionError('Completed')):
            self.assertEqual(probe.execute(self.workspace)['complete'],240)
        v=build(self.workspace)
        self.assertEqual(v['groups']['transcript'][0]['contrasts']['name_and_portrait']['n'],48)
        self.assertEqual(v['groups']['synthetic'][0]['contrasts']['name_and_portrait']['n'],12)
    def test_new_freeze_rejects_changed_software(self):
        self.authorize()
        with patch('behaviorlab.discourse_portrait_probe.software',return_value={}):
            with self.assertRaisesRegex(ValueError,'Software'):probe.execute(self.workspace,send=lambda p,k:self.fail())
