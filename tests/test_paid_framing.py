import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from behaviorlab.common import fingerprint
from behaviorlab.journal import Journal,read_events
from behaviorlab.paid_framing import MODELS,execute,ledger,make_plan,parse_response,replay,request_for,reservation,skip_reason,summary,validate
from test_assessment import wire


def fixture():
    models=[];routes={}
    for label,(model,tag,name,inp,out) in MODELS.items():
        models.append({'id':model,'name':model,'canonical_slug':model})
        routes[model]={'endpoints':[{'tag':tag,'provider_name':name,'status':0,'context_length':128000,'max_completion_tokens':8192,
            'pricing':{'prompt':str(float(inp)/1000000),'completion':str(float(out)/1000000)},'supported_parameters':['temperature','max_tokens','reasoning']} ]}
    return make_plan({'models':models},{'routes':routes},[])


def setup(d,p):
    with Journal(d,create=True) as j:j.append('paid_framing_created',{'plan':p,'plan_sha256':fingerprint(p),'code_hashes':{},'synthetic':True})


def response(p,**kw):return wire(p['model'],provider='OpenAI' if p['model'].startswith('openai/') else 'Anthropic',cost=kw.pop('cost',0.00001),**kw)


class PaidFramingTests(unittest.TestCase):
    def test_projection_preserves_model_root_mapping_and_cost(self):
        from behaviorlab.explorer import Catalog
        from behaviorlab.framing_explorer import load_framing
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)/'paid';directory.mkdir();setup(directory,fixture())
            execute(directory,generate=lambda p:response(p,content='A café 🙂 conversation.'),sleep=lambda _:None)
            before=(directory/'events.jsonl').read_bytes()
            with patch('behaviorlab.paid_framing.http_request',side_effect=AssertionError('Reader dispatched')):
                runs,screen=load_framing(directory);catalog=Catalog(d)
            self.assertEqual(len(runs),8);self.assertEqual(len(catalog.assessments),1)
            self.assertEqual(screen['calls'],96);self.assertEqual(screen['cost_usd'],'0.00096')
            self.assertEqual(runs[0]['title'],'GPT-4o mini · Anonymous 1')
            self.assertEqual(runs[1]['title'],'Claude Haiku 4.5 · Anonymous 1')
            self.assertTrue(runs[1]['models'][0].startswith('anthropic/'))
            self.assertEqual(runs[1]['settings']['provider']['only'],['anthropic'])
            self.assertFalse(runs[0]['messages'][0]['repeat'])
            self.assertEqual(sum(m['repeat'] for m in runs[0]['messages']),11)
            self.assertEqual((directory/'events.jsonl').read_bytes(),before)

    def test_onset_passages_require_exact_source_text(self):
        from behaviorlab.framing_explorer import load_framing
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d);plan=fixture();setup(directory,plan)
            execute(directory,generate=lambda p:response(p,content='A café 🙂 conversation.'),sleep=lambda _:None)
            runs,screen=load_framing(directory)
            reviews={r['id']:{'onsets':[]} for r in plan['roots']}
            quote={'run_id':runs[0]['id'],'message_id':runs[0]['messages'][0]['id'],
                   'start':2,'end':8,'quote':'café 🙂'}
            reviews[plan['roots'][0]['id']]['onsets']=[{'evidence':quote}]
            reading={'journal_head':screen['source']['journal_head'],'author':'Synthetic test',
                     'method':'Fixture only','findings':[],'root_reviews':reviews}
            sidecar=directory/'reading.json';sidecar.write_text(json.dumps(reading))
            load_framing(directory)
            quote['quote']='fabricated'
            sidecar.write_text(json.dumps(reading))
            with self.assertRaisesRegex(ValueError,'evidence span differs'):load_framing(directory)

    def test_models_budget_and_exact_ancestry(self):
        p=validate(fixture());self.assertEqual(len(p['tasks']),96)
        for change in ('budget','model','price'):
            bad=copy.deepcopy(p)
            if change=='budget':bad['budget_usd']='2'
            elif change=='model':bad['candidates'][0]['model']='openai/gpt-4o'
            else:bad['candidates'][1]['route']['pricing']['prompt']='1'
            with self.assertRaises(ValueError):validate(bad)
        mini=request_for(p,p['tasks'][0],{});haiku=request_for(p,p['tasks'][1],{})
        self.assertNotIn('reasoning',mini);self.assertEqual(haiku['reasoning'],{'enabled':False})
        self.assertNotIn('seed',mini);self.assertFalse(mini['provider']['allow_fallbacks'])
        t=next(t for t in p['tasks'] if t['id']=='mini-mirror-01:3')
        history={'mini-mirror-01:1':{'status':'valid','text':'One','thinking':'Hidden'},'mini-mirror-01:2':{'status':'valid','text':'Two'},
                 'haiku-mirror-01:1':{'status':'valid','text':'Other'}}
        req=request_for(p,t,history)
        self.assertEqual([m['content'] for m in req['messages']][-2:],['One','Two'])
        self.assertEqual([m['role'] for m in req['messages']],['system','user','assistant','user'])
        req['messages'][1]['content']='x'*40000
        with self.assertRaises(ValueError):reservation(p,t,req)

    def test_complete_and_closed_resume(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d,fixture());calls=[]
            def gen(p):calls.append(p);return response(p,content='Reply '+str(len(calls)))
            s=execute(d,generate=gen,sleep=lambda _:None)
            self.assertTrue(s['finished']);self.assertEqual(len(calls),96)
            self.assertEqual(calls[8]['messages'][1]['content'],'Reply 8')
            self.assertEqual(summary(s)['known_cost_usd'],'0.00096')
            execute(d,generate=lambda _:self.fail('Closed batch retried'))

    def test_cap_stops_own_root(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d,fixture());calls=[]
            def gen(p):calls.append(p);return response(p,finish='length' if len(calls)==1 else 'stop')
            s=execute(d,generate=gen,sleep=lambda _:None)
            self.assertEqual(len(calls),85)
            self.assertEqual(s['results']['mini-anonymous-01:12']['status'],'not_dispatched')
            self.assertEqual(s['results']['haiku-anonymous-01:12']['status'],'valid')

    def test_accounting_overrun_and_missing_cost_halt(self):
        p=fixture();t=p['tasks'][0];req=request_for(p,t,{});reserved=reservation(p,t,req)
        w=response(req,cost=2)
        result=parse_response(w.raw,w.evidence,p,t,req,reserved)
        self.assertTrue(result['halt']);self.assertEqual(result['cost_usd'],'2')
        w=response(req,cost=None)
        result=parse_response(w.raw,w.evidence,p,t,req,reserved)
        self.assertTrue(result['halt']);self.assertIsNone(result['cost_usd'])
        state={'results':{'prior':{'cost_usd':'0.9999','status':'valid'}},'reservations':{}}
        self.assertIn('budget',skip_reason(p,t,state))
        state={'results':{},'reservations':{'unknown':{'usd':'0.9999'}}}
        self.assertIn('budget',skip_reason(p,t,state))

    def test_uncertain_request_and_saved_error_are_not_retried(self):
        for raw_saved in (False,True):
            with tempfile.TemporaryDirectory() as d:
                p=fixture();setup(d,p);t=p['tasks'][0];req=request_for(p,t,{})
                with Journal(d) as j:
                    j.append('paid_framing_request',{'id':t['id'],'request':req,'reservation':reservation(p,t,req)})
                    if raw_saved:
                        w=response(req,status=429,cost=None)
                        j.append('paid_framing_response',{'id':t['id'],'raw':w.raw,'transport':w.evidence})
                s=execute(d,generate=lambda _:self.fail('Unknown/error request retried'),sleep=lambda _:None)
                self.assertTrue(s['finished']);self.assertEqual(len(s['requests']),1)
                self.assertGreater(ledger(s)[1],0)
                self.assertEqual(s,replay(read_events(Path(d)/'events.jsonl')))

    def test_reservation_or_skip_forgery_rejected(self):
        for skip in (False,True):
            with tempfile.TemporaryDirectory() as d:
                p=fixture();setup(d,p);t=p['tasks'][0];req=request_for(p,t,{})
                with Journal(d) as j:
                    if skip:j.append('paid_framing_skipped',{'id':t['id'],'reason':'Unavailable root ancestor'})
                    else:j.append('paid_framing_request',{'id':t['id'],'request':req,'reservation':{'usd':'0'}})
                with self.assertRaises(ValueError):replay(read_events(Path(d)/'events.jsonl'))
