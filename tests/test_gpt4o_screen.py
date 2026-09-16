import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from behaviorlab.common import fingerprint
from behaviorlab.journal import Journal,read_events
from behaviorlab.gpt4o_screen import MODELS,execute,ledger,make_plan,replay,request_for,reservation,skip_reason,summary,validate
from test_assessment import wire


def fixture():
    model,tag,provider,inp,out=MODELS['gpt4o']
    return make_plan({'models':[{'id':model,'name':'GPT-4o','canonical_slug':model}]},
        {'routes':{model:{'endpoints':[{'tag':tag,'provider_name':provider,'status':0,'context_length':128000,
            'max_completion_tokens':16384,'pricing':{'prompt':'0.0000025','completion':'0.00001'},
            'supported_parameters':['temperature','max_tokens']}]}}},[])


def setup(d):
    p=fixture()
    with Journal(d,create=True) as j:j.append('gpt4o_screen_created',{'plan':p,'plan_sha256':fingerprint(p),'code_hashes':{},'synthetic':True})
    return p


def response(p,**kw):return wire(p['model'],provider='OpenAI',cost=kw.pop('cost',0.00001),**kw)


class GPT4oScreenTests(unittest.TestCase):
    def test_pinned_scope_budget_and_controls(self):
        p=fixture();validate(p)
        for key,value in (('budget_usd','1.00'),('max_calls',48),('messages_per_root',30)):
            bad=copy.deepcopy(p);bad[key]=value
            with self.assertRaises(ValueError):validate(bad)
        bad=copy.deepcopy(p);bad['candidates'][0]['model']='openai/gpt-4o-mini'
        with self.assertRaises(ValueError):validate(bad)
        req=request_for(p,p['tasks'][0],{})
        self.assertNotIn('reasoning',req);self.assertNotIn('seed',req)
        self.assertEqual(req['provider']['only'],['openai']);self.assertFalse(req['provider']['allow_fallbacks'])
        self.assertEqual(req['provider']['max_price'],{'prompt':2.5,'completion':10.0})
        req['messages'][1]['content']='x'*40000
        with self.assertRaises(ValueError):reservation(p,p['tasks'][0],req)

    def test_complete_ancestry_closed_resume_and_reader(self):
        from behaviorlab.framing_explorer import load_framing
        with tempfile.TemporaryDirectory() as d:
            setup(d);calls=[]
            def gen(p):calls.append(p);return response(p,content='Message '+str(len(calls)))
            s=execute(d,generate=gen,sleep=lambda _:None)
            self.assertEqual(len(calls),24);self.assertTrue(s['finished'])
            self.assertEqual(calls[2]['messages'][1]['content'],'Message 2')
            self.assertEqual(calls[3]['messages'][1]['content'],'Message 1')
            self.assertEqual(summary(s)['known_cost_usd'],'0.00024')
            before=(Path(d)/'events.jsonl').read_bytes()
            with patch('behaviorlab.gpt4o_screen.http_request',side_effect=AssertionError('Unexpected dispatch')):
                runs,screen=load_framing(d);execute(d)
            self.assertEqual(len(runs),2);self.assertEqual(screen['calls'],24)
            self.assertEqual(runs[0]['models'],['openai/gpt-4o-2024-11-20'])
            self.assertEqual(runs[0]['title'],'GPT-4o (2024-11-20) · Anonymous 1')
            self.assertEqual((Path(d)/'events.jsonl').read_bytes(),before)

    def test_cap_preserves_output_and_blocks_only_own_root(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d);calls=[]
            def gen(p):calls.append(p);return response(p,content='Partial',finish='length' if len(calls)==1 else 'stop')
            s=execute(d,generate=gen,sleep=lambda _:None)
            self.assertEqual(len(calls),13)
            self.assertEqual(s['results']['gpt4o-anonymous-01:1']['text'],'Partial')
            self.assertEqual(s['results']['gpt4o-anonymous-01:12']['status'],'not_dispatched')
            self.assertEqual(s['results']['gpt4o-mirror-01:12']['status'],'valid')

    def test_unknown_request_or_saved_error_never_retried(self):
        for saved in (False,True):
            with tempfile.TemporaryDirectory() as d:
                p=setup(d);t=p['tasks'][0];req=request_for(p,t,{})
                with Journal(d) as j:
                    j.append('gpt4o_screen_request',{'id':t['id'],'request':req,'reservation':reservation(p,t,req)})
                    if saved:
                        w=response(req,status=429,cost=None)
                        j.append('gpt4o_screen_response',{'id':t['id'],'raw':w.raw,'transport':w.evidence})
                s=execute(d,generate=lambda _:self.fail('Retried'),sleep=lambda _:None)
                self.assertEqual(len(s['requests']),1);self.assertTrue(s['finished']);self.assertGreater(ledger(s)[1],0)

    def test_held_cost_and_overrun_stop_dispatch(self):
        p=fixture();t=p['tasks'][0]
        self.assertIn('budget',skip_reason(p,t,{'results':{},'reservations':{'pending':{'usd':'0.4999'}}}))
        with tempfile.TemporaryDirectory() as d:
            setup(d);calls=[]
            def gen(p):calls.append(p);return response(p,cost=1)
            s=execute(d,generate=gen,sleep=lambda _:None)
            self.assertEqual(len(calls),1);self.assertTrue(s['results'][t['id']]['halt'])
            self.assertEqual(summary(s)['known_cost_usd'],'1')

    def test_replay_rejects_forged_reservation(self):
        with tempfile.TemporaryDirectory() as d:
            p=setup(d);t=p['tasks'][0];req=request_for(p,t,{})
            with Journal(d) as j:j.append('gpt4o_screen_request',{'id':t['id'],'request':req,'reservation':{'usd':'0'}})
            with self.assertRaises(ValueError):replay(read_events(Path(d)/'events.jsonl'))
