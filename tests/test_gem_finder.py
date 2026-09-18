import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.common import fingerprint
from behaviorlab.explorer import Notes
from behaviorlab.gem_plan import PILOT, questions, payload, software, select_items, profile_distance
from behaviorlab.gem_runner import validate, execute, summary
from behaviorlab.gem_finder import GemFinder
from behaviorlab.jev_atlas import MODEL, ENDPOINT, PRICE, MAX_INPUT, read_record, write_record
from behaviorlab.research_bundle import export_notebook, restore_notebook


def fixture(workspace,count=2):
    rubric=json.loads(Path('behaviorlab/gem_rubric.json').read_text())
    items=[{'id':f'i{i}','run_id':f'r{i}','message_id':'m1','lineage':f'l{i}','text':f'An explicit idea {i}.',
            'context':[{'speaker':'Y','text':'Consider this question.'}],'speaker':'X','source_sha256':f's{i}',
            'turn':2,'title':f'Run {i}','model':'test-model','model_label':'Test','words':4,'sample_role':'pilot',
            'profile_distance':{'value':2,'neighbors':[]},'broad_topic':'b','topic_scores':{'b':20}} for i in range(count)]
    plan={'model':MODEL,'endpoint':ENDPOINT,'items':items,'questions':questions(rubric),'rubric':rubric,
          'budget':{'unique_requests':count,'max_attempts':count+10,'retry_allowance':10,'max_attempts_per_item':3,
                    'usd_ceiling':2,'usd_per_million_input':PRICE,'reserved_input_tokens_per_attempt':MAX_INPUT},
          'execution':{'retryable_http':[429,529],'backoff_seconds':[20,40],'minimum_interval_seconds':1,'timeout_seconds':60},
          'discovery_runs':{i['run_id']:i['source_sha256'] for i in items},'software_sha256':software(),
          'selection':{'reserved_lineages':['reserved']},'broad_topics':[],'created_at':'2026-09-18','policy':'Development'}
    for i in items:i['request_sha256']=fingerprint(payload(plan,i))
    root=workspace/PILOT;write_record(root/'plan.json',plan);plan=read_record(root/'plan.json')
    write_record(root/'authorization.json',{'plan_sha256':plan['sha256'],'usd_ceiling':2,'scope':'Synthetic test only'})
    runs={i['run_id']:{'id':i['run_id'],'title':i['title'],'source':{'sha256':i['source_sha256']},
            'messages':[{'id':'m1','kind':'message','text':i['text'],'segment':'conversation','model':'test-model'}],
            'segments':[{'id':'conversation','parent':None}],'leaves':['conversation']} for i in items}
    return plan,SimpleNamespace(runs=runs)


def answer(payload):
    return {'model':MODEL,'answers':{k:{'type':'score','score':2.2,'confidence':.6,
             'legend':{str(i):c for i,c in enumerate(q['criteria'])},
             'probabilities':{'0':0,'1':0,'2':.8,'3':.2,'4':0}} for k,q in payload['questions'].items()},
             'usage':{'input_tokens':1000,'output_tokens':100}}


class GemTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.workspace=Path(self.tmp.name)
        self.plan,self.catalog=fixture(self.workspace)
    def tearDown(self):self.tmp.cleanup()

    def test_gem_http_api_requires_origin_token_and_persists_separate_history(self):
        import io
        from behaviorlab.explorer import make_server
        for r in self.catalog.runs.values():r['experiment']={}
        self.catalog.collections=[];self.catalog.assessments=[];self.catalog.issues=[];self.catalog.indexed_at='test'
        with patch('behaviorlab.explorer.Catalog',return_value=self.catalog),patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda a,h:SimpleNamespace(server_port=8765,handler=h)):
            server=make_server(self.workspace)
        def call(method,path,data=None,headers=None):
            h=server.handler.__new__(server.handler);h.server=server;h.path=path
            raw=json.dumps(data).encode() if data is not None else b''
            h.headers={'Host':'127.0.0.1:8765','Content-Type':'application/json','Content-Length':str(len(raw)),**(headers or {})}
            h.rfile=io.BytesIO(raw);out=[];h.send=lambda d,status=200,**kw:out.append((status,d))
            getattr(h,'do_'+method)();return out[0]
        self.assertEqual(call('GET','/api/gems')[0],200)
        self.assertEqual(call('GET','/gems.js')[0],200)
        self.assertEqual(call('POST','/api/gems/readings',{})[0],403)
        self.assertEqual(call('POST','/api/gems/readings',{}, {'Origin':'http://elsewhere'})[0],403)
        # Bootstrap's closure contains the same CSRF token used for all notebook writes.
        token=next(c.cell_contents for c in server.handler.allowed.__closure__ if isinstance(c.cell_contents,str))
        headers={'Origin':'http://127.0.0.1:8765','X-Explorer-Token':token}
        data={'run_id':'r0','message_id':'m1','source_sha256':'s0','rating':'gem','note':'Specific reason','exposure':'hidden_in_this_view'}
        status,saved=call('POST','/api/gems/readings',data,headers)
        self.assertEqual(status,200)
        self.assertEqual(call('GET','/api/gems/history/'+saved['id'])[1]['history'],[saved])
        self.assertEqual(call('GET','/api/gems/export')[1]['readings'],[saved])
        self.assertEqual(call('POST','/api/gems/readings',dict(saved,revision=0),headers)[0],400)

    def test_score_validation_preserves_distributions_and_separates_normalized_rating(self):
        raw=answer(payload(self.plan,self.plan['items'][0]));checked,cost=validate(raw,self.plan['questions'])
        self.assertAlmostEqual(checked['surprise']['normalized_score'],55)
        self.assertEqual(checked['surprise']['probabilities'],raw['answers']['surprise']['probabilities'])
        self.assertAlmostEqual(cost,.000042)
        for key,value in [('score',float('nan')),('score',4.1),('confidence',True),('legend',{})]:
            broken=json.loads(json.dumps(raw));broken['answers']['surprise'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate(broken,self.plan['questions'])

    def test_rounding_tolerance_is_bounded_and_does_not_renormalize(self):
        raw=answer(payload(self.plan,self.plan['items'][0]));a=raw['answers']['surprise']
        a['probabilities']={'0':.2,'1':.2,'2':.2,'3':.2,'4':.19};a['score']=1.99
        checked,_=validate(raw,self.plan['questions']);self.assertTrue(checked['surprise']['rounding_tolerated'])
        a['probabilities']['4']=.1
        with self.assertRaisesRegex(ValueError,'sum'):validate(raw,self.plan['questions'])

    def test_completed_resume_does_not_dispatch_or_need_credential(self):
        calls=[]
        def send(p,k):calls.append(p);return 200,json.dumps(answer(p))
        result=execute(self.workspace,send=send,key='test',sleep=lambda _:None)
        self.assertEqual((result['complete'],result['attempts']),(2,2))
        with patch('behaviorlab.gem_runner.credential',side_effect=AssertionError('No credential on completed resume')):
            self.assertEqual(execute(self.workspace)['complete'],2)
        self.assertEqual(len(calls),2)

    def test_overload_reserves_unknown_cost_and_retries_only_within_allocation(self):
        calls=[]
        def send(p,k):calls.append(p);return (529,'overloaded') if len(calls)==1 else (200,json.dumps(answer(p)))
        result=execute(self.workspace,send=send,key='test',sleep=lambda _:None)
        self.assertEqual(result['attempts'],3);self.assertEqual(result['complete'],2)
        self.assertAlmostEqual(result['unknown_reserved_usd'],MAX_INPUT*PRICE/1_000_000)

    def test_timeout_and_invalid_response_stop_without_redispatch(self):
        result=execute(self.workspace,send=lambda p,k:(200,'{}'),key='test',sleep=lambda _:None)
        self.assertEqual(result['stopped'],['invalid']);self.assertEqual(result['attempts'],1)
        with self.assertRaisesRegex(ValueError,'stopped'):
            execute(self.workspace,send=lambda p,k:self.fail('Unexpected call'),key='test')

    def test_durable_request_without_response_remains_unresolved(self):
        i=self.plan['items'][0];write_record(self.workspace/PILOT/'attempts'/i['id']/'01.request.json',
             {'plan_sha256':self.plan['sha256'],'item_id':i['id'],'attempt':1,'payload':payload(self.plan,i)})
        with self.assertRaisesRegex(ValueError,'uncertain'):execute(self.workspace,send=lambda p,k:self.fail(),key='test')
        self.assertEqual(summary(self.workspace/PILOT,self.plan)['attempts'],1)

    def test_software_and_authorization_are_frozen(self):
        with patch('behaviorlab.gem_runner.software',return_value={}):
            with self.assertRaisesRegex(ValueError,'software'):execute(self.workspace,send=lambda p,k:self.fail(),key='test')

    def test_profile_distance_excludes_same_lineage_and_uses_distinct_neighbors(self):
        item={'lineage':'own','topic_scores':{'b':100}}
        reference=[{'id':'same','lineage':'own','vector':[100],'run_id':'r','message_id':'m'},
                   {'id':'a','lineage':'other','vector':[80],'run_id':'a','message_id':'m'},
                   {'id':'b','lineage':'other','vector':[90],'run_id':'a','message_id':'n'},
                   {'id':'c','lineage':'third','vector':[50],'run_id':'b','message_id':'m'}]
        d=profile_distance(item,reference,[{'id':'b'}],k=2)
        self.assertEqual(d['value'],30);self.assertEqual([n['id'] for n in d['neighbors']],['b','c'])
        self.assertIsNone(profile_distance(item,reference,[{'id':'b'}],k=5)['value'])

    def test_reading_is_versioned_source_checked_and_personal(self):
        notes=Notes(self.workspace/'notes.sqlite');before=export_notebook(self.workspace/'notes.sqlite')
        store=GemFinder(self.workspace,notes,self.catalog)
        data={'run_id':'r0','message_id':'m1','source_sha256':'s0','rating':'gem','note':'A specific distinction.',
              'quote':'explicit idea','axes':{'contribution':3},'exposure':'hidden_in_this_view'}
        saved=store.save(data);self.assertEqual(saved['author'],'Local researcher')
        revised=store.save(dict(saved,rating='promising'));self.assertEqual(len(store.history(saved['id'])),2)
        with self.assertRaisesRegex(ValueError,'reload'):store.save(saved)
        with self.assertRaisesRegex(ValueError,'quoted'):store.save(dict(revised,quote='Not the actual text'))
        with self.assertRaisesRegex(ValueError,'reserved'):store.save(dict(data,run_id='reserved'))
        with self.assertRaisesRegex(ValueError,'stale'):store.save(dict(revised,source_sha256='changed'))
        with self.assertRaisesRegex(ValueError,'author'):store.save(dict(revised,author='Codex'))
        tables=export_notebook(self.workspace/'notes.sqlite')
        for k,v in before.items():self.assertEqual(tables[k],v)
        restore_notebook(tables,self.workspace/'restored.sqlite')
        self.assertEqual(tables,export_notebook(self.workspace/'restored.sqlite'))

    def test_changed_sources_hide_model_answers(self):
        execute(self.workspace,send=lambda p,k:(200,json.dumps(answer(p))),key='test',sleep=lambda _:None)
        store=GemFinder(self.workspace,Notes(self.workspace/'notes.sqlite'),self.catalog)
        self.catalog.runs['r0']['messages'][0]['text']='Changed'
        item=store.detail()['items'][0]
        self.assertFalse(item['source_current']);self.assertEqual(item['answers'],{})


class GemSelectionTests(unittest.TestCase):
    def test_selection_excludes_whole_reserved_lineage_and_never_selects_on_scores(self):
        targets=[];rows=[];passages={};runs={}
        for i in range(12):
            rid=f'r{i}';identity=f'i{i}';lineage='reserved' if i in (0,1) else f'l{i//2}'
            targets.append({'id':identity,'run_id':rid,'message_id':'m','lineage':lineage,'split':'reference_reserved' if i==0 else 'analysis',
              'text':'Text','context':[{'text':'Before','speaker':'Y'}],'speaker':'X','turn':2,'source_sha256':'s','condition':'condition'})
            rows.append({'__id':identity,'Inventory category':'conversation','Assessment status':'Complete','Observed history':'Clean recorded path',
              'Model ID':f'model{i%2}','Model':f'Model {i%2}','Identity':'Anonymous','Composition':'Mirror','Broad':i})
            passages[identity]={'source_current':True};runs[rid]={'title':rid,'source':{'sha256':'s'},'messages':[{'id':'m','text':'Text','status':'recorded'}]}
        dataset={'rows':rows,'passages':passages,'topics':[{'id':'b','group':'broad','field':'Broad'}]}
        a,reference,_,audit=select_items(SimpleNamespace(runs=runs),dataset,{'targets':targets},4)
        self.assertEqual(len({i['lineage'] for i in a}),4)
        self.assertNotIn('reserved',{i['lineage'] for i in a+reference})
        for r in rows:r['Broad']=100-r['Broad']
        b,_,_,_=select_items(SimpleNamespace(runs=runs),dataset,{'targets':targets},4)
        self.assertEqual([i['id'] for i in a],[i['id'] for i in b])


if __name__=='__main__':unittest.main()
