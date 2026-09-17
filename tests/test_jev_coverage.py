import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from behaviorlab.common import canonical, fingerprint
from behaviorlab.jev_atlas import JevAtlas, read_record, write_record
from behaviorlab.explorer import Notes
from behaviorlab.topic_atlas import TopicAtlas
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.jev_coverage import build_inventory, development_sample, context_for, freeze_coverage
from behaviorlab.jev_two_tier import prepare, make_questions, run as qualify
from test_jev_atlas import reply
from test_topic_atlas import run


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.workspace=Path(self.tmp.name);self.store=JevAtlas(self.workspace)
        self.notes=Notes(self.workspace/'explorer'/'notes.sqlite');self.atlas=TopicAtlas(self.notes)
        self.studies=ResearchCollections(self.notes)

    def prepare(self,**kwargs):
        catalog=SimpleNamespace(runs={'r':self.fixture()},issues=[])
        return self.store.prepare(dict(topics=['emergence','consciousness'],**kwargs),catalog,self.atlas,self.studies)['id']

    def fixture(self,identity='r',**kwargs):
        r=run(identity,**kwargs);r['data_class']='test';r['models']=['test']
        for m in r['messages']:m['kind']='message'
        return r

    def test_intervention_recipient_label_does_not_make_a_participant_target(self):
        r=self.fixture();r['messages'].insert(2,dict(r['messages'][0],id='external',kind='third',speaker='X',status='intervention',text='External interruption'))
        inv,items=build_inventory(SimpleNamespace(runs={'r':r},issues=[]))
        self.assertEqual(len(inv['targets']),6)
        target=next(i for i in items.values() if i['message_id']==r['messages'][3]['id'])
        self.assertEqual(target['context'][-1]['id'],'external')

    def test_branch_context_uses_parent_path_and_counts_shared_nodes_once(self):
        r=self.fixture(leaves=['a','b']);ms=r['messages']
        for n,m in enumerate(ms):m['parent']=ms[n-1]['id'] if n else None
        ms[4]['parent']=ms[1]['id'];ms[5]['parent']=ms[4]['id']
        self.assertEqual([m['id'] for m in context_for(r,ms[5])],[ms[1]['id'],ms[4]['id']])
        inv,_=build_inventory(SimpleNamespace(runs={'r':r},issues=[]))
        self.assertEqual(len(inv['targets']),6)
        ms[0]['parent']=ms[5]['id']
        with self.assertRaises(ValueError):context_for(r,ms[5])

    def test_inventory_retains_flagged_and_unavailable_but_separates_synthetic(self):
        r=self.fixture();r['messages'][0]['text']=None;r['messages'][1]['status']='cap';r['messages'][2]['status']='after_cap'
        inv,items=build_inventory(SimpleNamespace(runs={'r':r,'s':self.fixture('s',kind='synthetic')},issues=[]))
        self.assertEqual(inv['totals']['categories'],{'conversation':1,'synthetic':1})
        self.assertEqual(inv['totals']['visible_flagged_targets'],2)
        self.assertEqual(len(items),6)
        self.assertEqual(inv['totals']['visible_nonsynthetic_targets'],5)

    def test_reading_selection_reproducible_lineage_disjoint_and_freeze_no_overwrite(self):
        c=SimpleNamespace(runs={str(i):self.fixture(str(i)) for i in range(8)},issues=[])
        inv,items=build_inventory(c)
        a=development_sample(inv,items,count=3);b=development_sample(inv,items,count=3)
        self.assertEqual(a['items'],b['items'])
        self.assertFalse(set(a['development_lineages'])&set(a['future_evaluation_lineages']))
        dest=self.workspace/'coverage';freeze_coverage(c,dest,count=3)
        with self.assertRaises(ValueError):freeze_coverage(c,dest,count=3)

    def setup_qualification(self):
        pilot=self.store.plan(self.prepare(count=6))
        c=SimpleNamespace(runs={'r':self.fixture()},issues=[]);coverage=self.workspace/'coverage'
        freeze_coverage(c,coverage,count=1);packet=read_record(coverage/'reading-packet.json')
        write_record(coverage/'open-readings.json',{'packet_sha256':packet['sha256'],'readings':[{'item_id':i['id']} for i in packet['items']]})
        entries=[dict(t,group='focused',anchor=True) for t in pilot['dictionary'] if t['id'] in pilot['topics']]
        entries.append({'id':'form_poetry','title':'Poetry','definition':'Performs a poem.','boundary':'Form, not discussion.','group':'form','variants':[]})
        codebook={'coverage_packet_sha256':packet['sha256'],'pilot_plan_sha256':pilot['sha256'],'version':'test','groups':{'focused':'Focused','form':'Form'},'topics':entries}
        path=self.workspace/'codebook.json';path.write_text(canonical(codebook))
        protocol=prepare(self.workspace,coverage,path,pilot_id=pilot['id'])
        return coverage,protocol,pilot,codebook

    def test_packs_keep_exact_anchors_and_states_and_forms_ask_about_performance(self):
        coverage,protocol,pilot,book=self.setup_qualification()
        plans=[self.store.plan(a['batch']) for a in protocol['allocations']]
        for key,q in plans[1]['questions'].items():
            self.assertEqual(q,pilot['questions'][key]);self.assertEqual(q,plans[0]['questions'][key])
        self.assertEqual(self.store.payload(plans[0],plans[0]['items'][0])['state'],self.store.payload(plans[1],plans[1]['items'][0])['state'])
        self.assertIn('what the target does',plans[0]['questions']['topic_form_poetry']['instructions']['question'])
        with self.assertRaises(ValueError):prepare(self.workspace,coverage,self.workspace/'codebook.json')

    def test_aggregate_resumes_without_duplicate_calls_and_stops_after_failure(self):
        coverage,protocol,_,_=self.setup_qualification();calls=[]
        def send(payload,key):calls.append(payload);return reply(payload)
        with patch('behaviorlab.jev_runner.credential',return_value='test'),patch('behaviorlab.jev_runner.transport',side_effect=send):
            qualify(self.workspace,coverage,max_calls=1);self.assertEqual(len(calls),1)
            qualify(self.workspace,coverage);self.assertEqual(len(calls),protocol['max_calls'])
            qualify(self.workspace,coverage);self.assertEqual(len(calls),protocol['max_calls'])

    def test_aggregate_error_blocks_other_pack_and_preserves_failed_response(self):
        coverage,protocol,_,_=self.setup_qualification()
        with patch('behaviorlab.jev_runner.credential',return_value='test'),patch('behaviorlab.jev_runner.transport',return_value=(529,'overloaded')) as send:
            result=qualify(self.workspace,coverage);self.assertEqual(result['status'],'stopped');self.assertEqual(send.call_count,1)
            with self.assertRaises(ValueError):qualify(self.workspace,coverage)
            self.assertEqual(send.call_count,1)
        second=self.store.plan(protocol['allocations'][1]['batch'])
        self.assertTrue(all(r['status']=='pending' for r in self.store.results(second)))
