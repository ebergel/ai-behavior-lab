import base64
import copy
from pathlib import Path
import tempfile
import unittest

from behaviorlab.backends import WireResponse
from behaviorlab.common import canonical, read_json, sha256
from behaviorlab.journal import read_events
from behaviorlab.participants import create, execute, make_plan, parse_response, payload, replay, report, reservation, validate


class Backend:
    synthetic = True
    def __init__(self, alter=None): self.calls = []; self.alter = alter
    def verify(self, plan): return {}
    def generate(self,p):
        self.calls.append(p)
        d = {'model':p['model'],'provider':'OpenAI' if p['model'].startswith('openai/') else 'Anthropic',
             'usage':{'prompt_tokens':10,'completion_tokens':5,'cost':0.00002},
             'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'[SYNTHETIC] café 🙂'}}]}
        if self.alter: self.alter(d,p)
        raw = canonical(d); b = raw.encode()
        return WireResponse(raw, {'http_status':200,'response_bytes_base64':base64.b64encode(b).decode(),'response_sha256':sha256(b)})


class ParticipantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.path = Path(self.tmp.name)/'campaign'; self.plan = make_plan(1)
    def tearDown(self): self.tmp.cleanup()
    def start(self,plan=None): create(self.path,plan or self.plan,{}, {}, {},synthetic=True)
    def events(self): return read_events(self.path/'events.jsonl')

    def test_plan_rejects_full_gpt4o_unbalanced_jobs_and_overspend(self):
        for change in ('model','jobs','budget'):
            p = copy.deepcopy(self.plan)
            if change=='model': p['models']['mini']['model']='openai/gpt-4o-2024-11-20'
            if change=='jobs': p['jobs'].pop()
            if change=='budget': p['budget_usd']='15'
            with self.assertRaises(ValueError): validate(p)

    def test_explorer_preserves_smoke_replies_without_listing_undispatched_roots(self):
        from behaviorlab.participant_explorer import load_participants
        self.start(); execute(self.path,Backend(),smoke_only=True)
        before=(self.path/'events.jsonl').read_bytes(); runs=load_participants(self.path)
        self.assertEqual(len(runs),2); self.assertTrue(all(r['data_class']=='synthetic_cloud_fixture' for r in runs))
        self.assertTrue(all(r['messages'][0]['request'] and r['messages'][0]['raw_response'] for r in runs))
        self.assertEqual((self.path/'events.jsonl').read_bytes(),before)

    def test_actual_roles_full_history_no_reasoning_and_routing(self):
        j=self.plan['jobs'][2]; results={j['id']+':1':{'status':'valid','text':'one','thinking':'hidden'},j['id']+':2':{'status':'valid','text':'two'}}
        x=payload(self.plan,j,3,results); y=payload(self.plan,j,2,results)
        self.assertEqual([m['role'] for m in x['messages']],['system','user','assistant','user'])
        self.assertEqual([m['content'] for m in y['messages']][1:],['one'])
        self.assertNotIn('hidden',canonical(x)); self.assertFalse(x['provider']['allow_fallbacks'])
        self.assertEqual(x['transforms'],[]); self.assertIn('seed',x)
        h=payload(self.plan,self.plan['jobs'][3],1,{})
        self.assertNotIn('seed',h); self.assertEqual(h['reasoning'],{'enabled':False})

    def test_smoke_gate_resume_and_completed_replay_make_no_duplicate_calls(self):
        self.start(); b=Backend(); r=execute(self.path,b,smoke_only=True)
        self.assertEqual(r['requests'],2); self.assertFalse(r['complete'])
        r=execute(self.path,b); self.assertEqual(r['requests'],122); self.assertTrue(r['complete'])
        count=len(b.calls); execute(self.path,b); self.assertEqual(len(b.calls),count)
        self.assertEqual(sum(j['counts']['valid'] for j in r['jobs']),122)

    def test_saved_request_is_uncertain_and_never_retried(self):
        self.start(); b=Backend()
        def crash(stage,key):
            if stage=='after_request': raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): execute(self.path,b,hook=crash)
        r=execute(self.path,b); self.assertEqual(r['requests'],1); self.assertEqual(len(b.calls),0)
        self.assertGreater(float(r['reserved_unknown_cost_usd']),0)

    def test_raw_response_recovers_without_regenerating(self):
        self.start(); b=Backend(); self.plan['max_inflight']=1
        # Independent smoke calls may already be in flight; each saved request still remains unique.
        def crash(stage,key):
            if stage=='after_response': raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): execute(self.path,b,hook=crash)
        before=len(b.calls); execute(self.path,b,smoke_only=True)
        self.assertEqual(len(b.calls),before)
        self.assertEqual(len(replay(self.events())['results']),1)

    def test_bad_provider_or_missing_cost_halts_before_main(self):
        for kind in ('provider','cost','thinking','overrun'):
            with self.subTest(kind=kind):
                self.path=Path(self.tmp.name)/kind; self.start()
                def alter(d,p):
                    if kind=='provider': d['provider']='Other'
                    if kind=='cost': del d['usage']['cost']
                    if kind=='thinking': d['choices'][0]['message']['reasoning']='trace'
                    if kind=='overrun': d['usage']['cost']=2
                r=execute(self.path,Backend(alter)); self.assertLessEqual(r['requests'],2)
                self.assertFalse(r['complete']); self.assertTrue(any(x['halt'] for x in replay(self.events())['results'].values()))

    def test_caps_block_descendants_while_other_roots_finish(self):
        self.start()
        def alter(d,p):
            if p['max_tokens']==2048 and p['model'].startswith('openai/'):
                d['choices'][0]['finish_reason']='length'
        r=execute(self.path,Backend(alter)); self.assertTrue(r['complete'])
        self.assertEqual(sum(j['counts']['cap'] for j in r['jobs']),2)
        self.assertEqual(sum(j['counts']['blocked'] for j in r['jobs']),58)

    def test_budget_reserved_before_call_and_unknown_transport_kept(self):
        p=copy.deepcopy(self.plan); p['budget_usd']='0.00001'; self.start(p); b=Backend()
        r=execute(self.path,b); self.assertEqual(b.calls,[]); self.assertEqual(r['last_pause']['reason'],'budget_ceiling')
        self.path=Path(self.tmp.name)/'transport'; self.start()
        class Broken(Backend):
            def generate(self,p): raise TimeoutError()
        r=execute(self.path,Broken()); self.assertGreater(float(r['reserved_unknown_cost_usd']),0)
        self.assertEqual(r['responses'],0); self.assertFalse(r['complete'])

    def test_raw_bytes_are_verified(self):
        j=self.plan['jobs'][0]; p=payload(self.plan,j,1,{}); w=Backend().generate(p)
        w.evidence['response_sha256']='0'*64
        with self.assertRaises(ValueError): parse_response(w.raw,w.evidence,self.plan,j,p,reservation(self.plan,j,p))


if __name__=='__main__': unittest.main()
