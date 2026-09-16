import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.common import canonical, fingerprint, read_json, sha256
from behaviorlab.journal import Journal, read_events
from behaviorlab.mixed_dialogue import (execute, ledger, make_plan, parse_response, replay, request_for,
    reservation, skip_reason, summary, validate)
from behaviorlab.mixed_explorer import load_mixed
from test_live import wire as raw_wire

ROOT=Path(__file__).resolve().parents[1]


def wire(data):
    result=raw_wire(data); result.evidence['elapsed_seconds']=0.01; return result


def fixture():
    local=read_json((ROOT/'design/ollama-context-models.json').read_text())['models'][1]
    route={'tag':'anthropic','provider_name':'Anthropic','status':0,'pricing':{'prompt':'.000001','completion':'.000005'},
           'context_length':200000,'max_completion_tokens':64000,'supported_parameters':['temperature','max_tokens','reasoning']}
    return make_plan(local,route,{})


def preflight(p,model):
    q=read_json(model.metadata_json)['artifact']['qualification']; prompt=canonical(p['messages']); tokens=[11,22,33]
    def doc(request,data):
        w=wire(data); return {'request':request,'raw_response':w.raw,'transport':w.evidence}
    argv=list(q['runner_arguments']); argv[argv.index('{port}')]='1234'
    return {'schema':q['schema'],'request_sha256':fingerprint(p),
        'render':doc(dict(p,_debug_render_only=True),{'model':model.tag,'done':False,'_debug_info':{'rendered_template':prompt}}),
        'tokenization':doc({'content':prompt,'add_special':False,'parse_special':True},{'tokens':tokens}),
        'runner':{'endpoint':'http://127.0.0.1:1234','arguments':argv},
        'runner_configuration_defaults':doc(None,{'model_path':q['model_blob'],'build_info':q['runner_build_info'],
            'total_slots':1,'default_generation_settings':{'n_ctx':32768}}),
        'rendered_utf8_sha256':sha256(prompt.encode()),'prompt_token_ids_sha256':fingerprint(tokens),
        'input_tokens':3,'context_window':32768,'reserved_output_tokens':1024,'context_headroom':32768-1024-3}


def response(task,p,context,finish='stop',cost=.00001):
    text='[SYNTHETIC FIXTURE] '+task['id']+' café 空'
    if task['participant']=='G':
        w=wire({'model':p['model'],'done':True,'done_reason':finish,'message':{'role':'assistant','content':text},
            'prompt_eval_count':3,'prompt_eval_cached_count':0,'eval_count':12})
        w.evidence['ollama_context']=context; return w
    return wire({'model':p['model'],'provider':'Anthropic','choices':[{'finish_reason':finish,'message':{'role':'assistant','content':text}}],
        'usage':{'prompt_tokens':3,'completion_tokens':12,'cost':cost}})


def setup(directory):
    plan=fixture()
    with Journal(directory,create=True) as j:j.append('mixed_dialogue_created',{'plan':plan,'plan_sha256':fingerprint(plan),'code_hashes':{},'synthetic':True})
    return plan


class MixedDialogueTests(unittest.TestCase):
    def test_scope_routing_and_recipient_history(self):
        p=validate(fixture()); self.assertEqual(len(set(p['seed_allocations'])),36)
        for key,value in [('max_calls',73),('budget_usd','2'),('messages_per_root',19)]:
            bad=copy.deepcopy(p); bad[key]=value
            with self.assertRaises(ValueError):validate(bad)
        with tempfile.TemporaryDirectory() as d:
            setup(d); seen=[]
            def gen(t,r,c):seen.append((t,r)); return response(t,r,c)
            s=execute(d,generate=gen,preflight=preflight,sleep=lambda _:None)
            self.assertEqual(len(seen),72); self.assertEqual(summary(s)['known_cost_usd'],'0.00036')
            for t,r in seen:
                self.assertEqual(r['model'],'gemma4:26b' if t['participant']=='G' else 'anthropic/claude-haiku-4.5')
                previous=r['messages'][2 if t['speaker']=='X' else 1:]
                self.assertEqual(len(previous),t['turn']-1)
                for i,m in enumerate(previous,1):
                    own=(i%2==t['turn']%2)
                    self.assertEqual(m['role'],'assistant' if own else 'user')
                    self.assertIn(t['root']+':'+str(i)+' café 空',m['content'])
                    self.assertEqual(m['content'].startswith('Participant '),not own)
                if t['participant']=='H':
                    self.assertNotIn('seed',r); self.assertEqual(r['provider']['only'],['anthropic']); self.assertFalse(r['reasoning']['enabled'])
            before=(Path(d)/'events.jsonl').read_bytes()
            with patch('behaviorlab.mixed_dialogue.http_request',side_effect=AssertionError('Dispatch')):
                self.assertTrue(execute(d)['finished']); runs=load_mixed(d)
            self.assertEqual((Path(d)/'events.jsonl').read_bytes(),before)
            self.assertEqual(len(runs),4); self.assertTrue(all(r['kind']=='synthetic' for r in runs))
            self.assertEqual(runs[2]['messages'][0]['model'],'gemma4:26b')
            self.assertEqual(runs[2]['messages'][1]['model'],'anthropic/claude-haiku-4.5')
            self.assertEqual(runs[2]['segments'][0]['stop'],18)
            sidecar=Path(d)/'reading.json'; q={'run_id':runs[0]['id'],'message_id':'gg:1','start':0,'end':11,'quote':'[SYNTHETIC '}
            reading={'journal_head':runs[0]['source']['journal_head'],'author':'Codex','method':'Synthetic validation',
                'root_reviews':{k:{} for k in ('gg','hh','gh','hg')},'findings':[{'evidence':[q]}]}
            sidecar.write_text(canonical(reading)); load_mixed(d)
            reading['findings'][0]['evidence'][0]['quote']='Wrong text'; sidecar.write_text(canonical(reading))
            with self.assertRaises(ValueError):load_mixed(d)

    def test_cap_blocks_only_its_root(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d)
            def gen(t,p,c):return response(t,p,c,finish='length' if t['id']=='gg:1' else 'stop')
            s=execute(d,generate=gen,preflight=preflight,sleep=lambda _:None)
            self.assertEqual(len(s['requests']),55); self.assertEqual(s['results']['gg:1']['status'],'cap')
            self.assertEqual(s['results']['gg:18']['status'],'not_dispatched'); self.assertEqual(s['results']['gh:18']['status'],'valid')
            self.assertFalse(load_mixed(d)[0]['complete']); self.assertTrue(load_mixed(d)[2]['complete'])

    def test_unknown_dispatch_never_retried_and_cost_is_held(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d)
            def gen(t,p,c):
                if t['participant']=='H':raise TimeoutError()
                return response(t,p,c)
            s=execute(d,generate=gen,preflight=preflight,sleep=lambda _:None)
            self.assertEqual(len(s['requests']),2); self.assertEqual(s['results']['hh:1']['status'],'unresolved'); self.assertGreater(ledger(s)[1],0)
            execute(d,generate=lambda *args:self.fail('Retried'))

    def test_preflight_failure_has_no_generation_or_reservation(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d)
            def fail(*args):raise ValueError('Context gate')
            s=execute(d,generate=lambda *args:self.fail('Dispatched'),preflight=fail,sleep=lambda _:None)
            self.assertEqual(len(s['requests']),0); self.assertEqual(ledger(s),(0,0)); self.assertTrue(s['results']['gg:1']['halt'])

    def test_saved_raw_response_recovers_without_duplicate(self):
        from behaviorlab.mixed_dialogue import local_model
        with tempfile.TemporaryDirectory() as d:
            p=setup(d); t=p['tasks'][0]; req=request_for(p,t,{}); w=response(t,req,preflight(req,local_model(p)))
            with Journal(d) as j:
                j.append('mixed_dialogue_request',{'id':t['id'],'request':req,'reservation':reservation(p,t,req)})
                j.append('mixed_dialogue_response',{'id':t['id'],'raw':w.raw,'transport':w.evidence})
            calls=[]
            def gen(t,r,c):calls.append(t['id']); return response(t,r,c)
            s=execute(d,generate=gen,preflight=preflight,sleep=lambda _:None)
            self.assertEqual(len(calls),71); self.assertNotIn('gg:1',calls); self.assertTrue(s['finished'])
            events=read_events(Path(d)/'events.jsonl'); events[1]['payload']['request']['messages'][0]['content']='changed'
            with self.assertRaises(ValueError):replay(events)

    def test_budget_identity_and_returned_cost_failure(self):
        p=fixture(); t=p['tasks'][1]; req=request_for(p,t,{})
        w=response(t,req,None); bad=read_json(w.raw); bad['model']='another-model'; wrong=wire(bad)
        self.assertTrue(parse_response(wrong.raw,wrong.evidence,p,t,req,reservation(p,t,req))['halt'])
        self.assertIn('budget',skip_reason(p,t,{'results':{},'reservations':{'pending':{'usd':'.9999'}}}))
        req['messages'][1]['content']='x'*40000
        with self.assertRaises(ValueError):reservation(p,t,req)
        with tempfile.TemporaryDirectory() as d:
            setup(d)
            def gen(t,r,c):return response(t,r,c,cost=2)
            s=execute(d,generate=gen,preflight=preflight,sleep=lambda _:None)
            self.assertEqual(len(s['requests']),2); self.assertTrue(s['results']['hh:1']['halt'])
