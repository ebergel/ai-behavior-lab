import base64
import copy
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from behaviorlab.assessment import SELECTED, execute, make_plan, parse, replay, request_for, validate
from behaviorlab.common import canonical, fingerprint, sha256
from behaviorlab.journal import Journal, read_events


def fixture():
    models=[{'id':m,'name':m,'canonical_slug':m.removesuffix(':free')+'-dated'} for m in SELECTED]
    route={'tag':'fixture','provider_name':'Fixture','status':0,'pricing':{'prompt':'0','completion':'0'},
           'supported_parameters':['temperature','max_tokens','reasoning'],'context_length':32768,'max_completion_tokens':1024}
    return make_plan({'models':models},{'routes':{m:{'endpoints':[copy.deepcopy(route)]} for m in SELECTED}})


def wire(model, content='LAB_ROUTING_OK', status=200, cost=0, finish='stop', provider='Fixture'):
    d={'model':model,'provider':provider,'usage':{'prompt_tokens':12,'completion_tokens':8,'cost':cost},
       'choices':[{'message':{'role':'assistant','content':content},'finish_reason':finish}]}
    raw=canonical(d); b=raw.encode()
    return SimpleNamespace(raw=raw,evidence={'http_status':status,'response_bytes_base64':base64.b64encode(b).decode(),
                                            'response_sha256':sha256(b),'elapsed_seconds':0.1})


class AssessmentTests(unittest.TestCase):
    def completion_plan(self, base):
        from behaviorlab.assessment import make_followup, make_completion
        p=fixture(); catalog={'models':[{'id':c['model'],'name':c['name'],'canonical_slug':c['canonical_slug']} for c in p['candidates']]}
        routes={'routes':{c['model']:{'endpoints':c['route_observations']} for c in p['candidates']}}
        first=Path(base)/'first'; first.mkdir(); self.setup_journal(first,p)
        execute(first,None,lambda req:wire(req['model'],status=429),sleep=lambda _:None)
        second=Path(base)/'second'; second.mkdir()
        p2=make_followup(catalog,routes,read_events(first/'events.jsonl')); self.setup_journal(second,p2)
        execute(second,None,lambda req:wire(req['model'],status=403 if req['model'].startswith('thinkingmachines/') else 200),sleep=lambda _:None)
        return validate(make_completion(catalog,routes,[first,second]))

    def test_completion_reuses_prior_check_without_replaying_it(self):
        from behaviorlab.assessment_explorer import load_assessment
        with tempfile.TemporaryDirectory() as d:
            p=self.completion_plan(d); self.assertEqual(p['max_calls'],15)
            self.assertNotIn('m1-system:1',[t['id'] for t in p['tasks']])
            bad=copy.deepcopy(p); bad['prior_checks'][0]['request']['messages'][0]['content']='Different instruction'
            with self.assertRaises(ValueError): validate(bad)
            directory=Path(d)/'completion'; directory.mkdir(); self.setup_journal(directory,p); calls=[]
            def generate(req):
                calls.append(req); return wire(req['model'],content='A technically valid reply, even if it does not match the expected answer.')
            state=execute(directory,None,generate,sleep=lambda _:None)
            self.assertEqual(len(calls),15); self.assertTrue(state['finished'])
            self.assertEqual(sum(t['kind']=='selfplay' for t in p['tasks']),8)
            runs,screen=load_assessment(directory)
            self.assertEqual(len(runs),9); self.assertEqual(screen['profiles'][0]['planned_calls'],7)
            self.assertEqual(screen['profiles'][0]['valid_messages'],7)
            self.assertEqual(screen['profiles'][0]['checks']['system']['source'],'prior')
            self.assertEqual(screen['profiles'][0]['checks']['system']['run_id'],p['prior_checks'][0]['source']['run_id'])
            execute(directory,None,generate,sleep=lambda _:None); self.assertEqual(len(calls),15)

    def test_completion_check_cap_blocks_only_its_conversation(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.completion_plan(d); directory=Path(d)/'completion'; directory.mkdir(); self.setup_journal(directory,p)
            def generate(req):
                cap=req['model'].startswith('nvidia/') and 'sealed label' in req['messages'][-1]['content']
                return wire(req['model'],finish='length' if cap else 'stop')
            state=execute(directory,None,generate,sleep=lambda _:None)
            self.assertEqual(len(state['requests']),11)
            self.assertEqual(state['results']['m1-selfplay:1']['status'],'not_dispatched')
            self.assertEqual(state['results']['m2-selfplay:4']['status'],'valid')

    def test_read_only_projection_and_annotated_source_spans(self):
        from behaviorlab.assessment_explorer import load_assessment
        from behaviorlab.explorer import Catalog
        plan=fixture()
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)/'screen'; directory.mkdir(); self.setup_journal(directory,plan)
            execute(directory,None,lambda req:wire(req['model'],content='A neutral café 🙂 reply.'),sleep=lambda _:None)
            before=(directory/'events.jsonl').read_bytes()
            with patch('behaviorlab.assessment.http_request',side_effect=AssertionError('Reader dispatched inference')):
                runs,screen=load_assessment(directory); catalog=Catalog(d)
            self.assertEqual(screen['calls'],48); self.assertEqual(len(runs),30)
            self.assertEqual(len(catalog.assessments),1); self.assertEqual(screen['profiles'][0]['median_seconds'],0.1)
            r=next(r for r in runs if r['title'].endswith('selfplay')); m=r['messages'][0]
            start=m['text'].index('café')
            reading={'journal_head':screen['source']['journal_head'],'author':'Codex','method':'Synthetic fixture review',
                     'findings':[{'evidence':[{'run_id':r['id'],'message_id':m['id'],'start':start,'end':start+6,'quote':'café 🙂'}]}]}
            sidecar=directory/'reading.json'; sidecar.write_text(canonical(reading))
            self.assertIsNotNone(load_assessment(directory)[1]['reading'])
            reading['findings'][0]['evidence'][0]['quote']='invented'; sidecar.write_text(canonical(reading))
            with self.assertRaisesRegex(ValueError,'span differs'): load_assessment(directory)
            self.assertEqual((directory/'events.jsonl').read_bytes(),before)

    def test_unstarted_slots_are_inspectable_without_inflating_library(self):
        from behaviorlab.explorer import Catalog
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)/'screen'; directory.mkdir(); self.setup_journal(directory,fixture())
            execute(directory,None,lambda req:wire(req['model'],status=429),sleep=lambda _:None)
            c=Catalog(d)
            self.assertEqual(len(c.runs),30)
            self.assertEqual(c.search({'scope':['synthetic']},[])['total'],1)
            self.assertEqual(c.assessments[0]['profiles'][0]['checks']['system']['match'],None)

    def test_guards_and_actual_history(self):
        plan=validate(fixture()); t=plan['tasks'][0]; p=request_for(plan,t,{})
        self.assertEqual(p['provider']['max_price'],{'prompt':0,'completion':0})
        self.assertFalse(p['provider']['allow_fallbacks']); self.assertNotIn('seed',p)
        bad=copy.deepcopy(plan); bad['candidates'][0]['route']['pricing']['completion']='0.01'
        with self.assertRaises(ValueError): validate(bad)
        t=next(t for t in plan['tasks'] if t['id']=='m1-selfplay:3')
        history={'m1-selfplay:1':{'status':'valid','text':'first','thinking':'never insert'},
                 'm1-selfplay:2':{'status':'valid','text':'second'}}
        p=request_for(plan,t,history)
        self.assertEqual([m['role'] for m in p['messages']],['system','user','assistant','user'])
        self.assertEqual([m['content'] for m in p['messages']][-2:],['first','second'])

    def test_parser_and_exact_checks(self):
        p=fixture(); t=p['tasks'][0]
        def get(**kw):
            w=wire(SELECTED[0],**kw); return parse(w.raw,w.evidence,p,t)
        self.assertTrue(get()['check']); self.assertFalse(get(content='4')['check'])
        self.assertEqual(get(finish='length')['status'],'cap')
        self.assertTrue(get(provider='Wrong')['halt']); self.assertTrue(get(cost=0.1)['halt'])
        self.assertTrue(get(status=429)['halt']); self.assertFalse(get(status=503)['halt'])
        self.assertTrue(get(status=503)['stop_candidate'])
        w=wire(SELECTED[0]); w.evidence['response_sha256']='x'
        with self.assertRaises(ValueError): parse(w.raw,w.evidence,p,t)

    def test_followup_only_untouched_models_and_scoped_upstream_quota(self):
        from behaviorlab.assessment import make_followup
        p=fixture()
        with tempfile.TemporaryDirectory() as d:
            self.setup_journal(d,p); execute(d,None,lambda req:wire(req['model'],status=429),sleep=lambda _:None)
            catalog={'models':[{'id':c['model'],'name':c['name'],'canonical_slug':c['canonical_slug']} for c in p['candidates']]}
            routes={'routes':{c['model']:{'endpoints':c['route_observations']} for c in p['candidates']}}
            followup=validate(make_followup(catalog,routes,read_events(Path(d)/'events.jsonl')))
            self.assertEqual(followup['max_calls'],24); self.assertEqual(len(followup['candidates']),3)
            task=followup['tasks'][0]
            raw=canonical({'error':{'code':429,'metadata':{'limit_source':'upstream_provider_shared_pool'}}})
            transport={'http_status':429,'response_sha256':sha256(raw.encode()),'response_bytes_base64':base64.b64encode(raw.encode()).decode()}
            result=parse(raw,transport,followup,task)
            self.assertFalse(result['halt']); self.assertTrue(result['stop_candidate'])
            self.assertTrue(parse(raw,transport,p,p['tasks'][0])['halt'])
            raw=canonical({'error':{'code':429}})
            transport.update(response_sha256=sha256(raw.encode()),response_bytes_base64=base64.b64encode(raw.encode()).decode())
            self.assertTrue(parse(raw,transport,followup,task)['halt'])

    def setup_journal(self, d, plan):
        with Journal(d,create=True) as j:
            j.append('model_assessment_created',{'plan':plan,'plan_sha256':fingerprint(plan),'code_hashes':{},'synthetic':True})

    def test_finite_execution_no_retries_caps_and_unavailable(self):
        p=fixture(); p['candidates'][-1]['route']=None
        calls=[]
        def generate(req):
            calls.append(req)
            return wire(req['model'],content='A short reply.',finish='length' if len(calls)==21 else 'stop')
        with tempfile.TemporaryDirectory() as d:
            self.setup_journal(d,p)
            s=execute(d,None,generate,sleep=lambda _:None)
            self.assertEqual(len(calls),37); self.assertEqual(s['results']['m1-selfplay:2']['status'],'not_dispatched')
            self.assertEqual(len(s['results']),48)
            execute(d,None,generate,sleep=lambda _:None); self.assertEqual(len(calls),37)

    def test_quota_unknown_dispatch_and_raw_recovery(self):
        p=fixture(); t=p['tasks'][0]
        with tempfile.TemporaryDirectory() as d:
            self.setup_journal(d,p)
            with Journal(d) as j: j.append('assessment_request',{'id':t['id'],'request':request_for(p,t,{})})
            s=execute(d,None,lambda _:self.fail('Unknown request retried'),sleep=lambda _:None)
            self.assertEqual(len(s['requests']),1); self.assertEqual(s['results'][t['id']]['status'],'unresolved')
        with tempfile.TemporaryDirectory() as d:
            self.setup_journal(d,p); w=wire(SELECTED[0],status=429)
            with Journal(d) as j:
                j.append('assessment_request',{'id':t['id'],'request':request_for(p,t,{})})
                j.append('assessment_response',{'id':t['id'],'raw':w.raw,'transport':w.evidence})
            s=execute(d,None,lambda _:self.fail('Quota response retried'),sleep=lambda _:None)
            self.assertTrue(s['finished']); self.assertEqual(len(s['requests']),1)
            self.assertEqual(s,replay(read_events(Path(d)/'events.jsonl')))
