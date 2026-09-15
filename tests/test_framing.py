import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.common import canonical, fingerprint
from behaviorlab.framing import MODEL, MIRROR, execute, make_plan, replay, request_for, skip_reason, validate
from behaviorlab.journal import Journal, read_events
from test_assessment import wire


def fixture():
    route={'tag':'nvidia/nvfp4','provider_name':'Nvidia','status':0,'pricing':{'prompt':'0','completion':'0'},
           'supported_parameters':['temperature','max_tokens','reasoning'],'context_length':32768,'max_completion_tokens':1024}
    return make_plan({'models':[{'id':MODEL,'name':'Nemotron','canonical_slug':MODEL.removesuffix(':free')}]},
                     {'data':{'endpoints':[route]}})


def setup(directory, plan):
    with Journal(directory,create=True) as j:
        j.append('framing_comparison_created',{'plan':plan,'plan_sha256':fingerprint(plan),'code_hashes':{},'synthetic':True})


class FramingTests(unittest.TestCase):
    def test_read_only_explorer_and_exact_quote_validation(self):
        from behaviorlab.explorer import Catalog
        from behaviorlab.framing_explorer import load_framing
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)/'framing'; directory.mkdir(); setup(directory,fixture())
            execute(directory,generate=lambda _:wire(MODEL,'A café 🙂 conversation.',provider='Nvidia'),sleep=lambda _:None)
            before=(directory/'events.jsonl').read_bytes()
            with patch('behaviorlab.framing.http_request',side_effect=AssertionError('Reader dispatched')):
                runs,screen=load_framing(directory); catalog=Catalog(d)
            self.assertEqual(len(runs),4); self.assertEqual(screen['calls'],48)
            self.assertEqual(len(catalog.runs),4); self.assertEqual(len(catalog.assessments),1)
            self.assertEqual(runs[1]['prompt'],MIRROR)
            reading={'journal_head':screen['source']['journal_head'],'author':'Codex','method':'Synthetic fixture review',
                     'findings':[{'evidence':[{'run_id':runs[0]['id'],'message_id':'anonymous-01:1','start':2,'end':8,'quote':'café 🙂'}]}]}
            (directory/'reading.json').write_text(canonical(reading))
            self.assertIsNotNone(load_framing(directory)[1]['reading'])
            reading['findings'][0]['evidence'][0]['quote']='invented'
            (directory/'reading.json').write_text(canonical(reading))
            with self.assertRaisesRegex(ValueError,'span differs'):load_framing(directory)
            self.assertEqual((directory/'events.jsonl').read_bytes(),before)

    def test_contrast_budget_route_and_isolated_history(self):
        p=validate(fixture())
        self.assertTrue(MIRROR.startswith(p['prompts']['anonymous']+' '))
        self.assertEqual(len(p['tasks']),48)
        bad=copy.deepcopy(p); bad['candidates'][0]['route']['pricing']['completion']='1'
        with self.assertRaises(ValueError):validate(bad)
        t=next(t for t in p['tasks'] if t['id']=='mirror-01:3')
        history={'mirror-01:1':{'status':'valid','text':'first','thinking':'hidden'},
                 'mirror-01:2':{'status':'valid','text':'second'},
                 'anonymous-01:1':{'status':'valid','text':'other root'}}
        req=request_for(p,t,history)
        self.assertEqual([m['content'] for m in req['messages']],[MIRROR,p['opening'],'first','second'])
        self.assertEqual([m['role'] for m in req['messages']],['system','user','assistant','user'])
        self.assertEqual(req['provider']['max_price'],{'prompt':0,'completion':0})
        self.assertFalse(req['provider']['allow_fallbacks']); self.assertNotIn('seed',req)
        history['mirror-01:2']['text']='a'*40000
        self.assertIn('context',skip_reason(p,t,history))

    def test_complete_batch_and_closed_resume(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d,fixture()); calls=[]
            def generate(req):
                calls.append(req); return wire(MODEL,'Short reply '+str(len(calls)),provider='Nvidia')
            s=execute(d,generate=generate,sleep=lambda _:None)
            self.assertTrue(s['finished']); self.assertEqual(len(calls),48)
            self.assertEqual(len(s['results']),48)
            self.assertEqual(calls[4]['messages'][1]['content'],'Short reply 4')
            self.assertEqual(calls[5]['messages'][1]['content'],'Short reply 3')
            execute(d,generate=lambda _:self.fail('Closed batch retried'))

    def test_cap_blocks_only_its_root(self):
        with tempfile.TemporaryDirectory() as d:
            setup(d,fixture()); calls=[]
            def generate(req):
                calls.append(req); return wire(MODEL,'Visible partial',finish='length' if len(calls)==1 else 'stop',provider='Nvidia')
            s=execute(d,generate=generate,sleep=lambda _:None)
            self.assertEqual(len(calls),37)
            self.assertEqual(s['results']['anonymous-01:12']['status'],'not_dispatched')
            self.assertEqual(s['results']['mirror-01:12']['status'],'valid')

    def test_quota_and_transport_stop_all_without_retry(self):
        for raw_saved in (False,True):
            with tempfile.TemporaryDirectory() as d:
                p=fixture(); setup(d,p); t=p['tasks'][0]
                with Journal(d) as j:
                    j.append('framing_request',{'id':t['id'],'request':request_for(p,t,{})})
                    if raw_saved:
                        w=wire(MODEL,status=429,provider='Nvidia')
                        j.append('framing_response',{'id':t['id'],'raw':w.raw,'transport':w.evidence})
                s=execute(d,generate=lambda _:self.fail('Unknown or quota request retried'),sleep=lambda _:None)
                self.assertEqual(len(s['requests']),1); self.assertTrue(s['finished'])
                self.assertEqual(s['results'][t['id']]['status'],'invalid' if raw_saved else 'unresolved')
                self.assertEqual(s,replay(read_events(Path(d)/'events.jsonl')))

    def test_replay_rejects_false_skip_or_cross_root_request(self):
        for skip in (False,True):
            with tempfile.TemporaryDirectory() as d:
                p=fixture(); setup(d,p); t=p['tasks'][0]
                with Journal(d) as j:
                    if skip:j.append('framing_skipped',{'id':t['id'],'reason':'Unavailable root ancestor'})
                    else:
                        req=request_for(p,t,{}); req['messages'][0]['content']=MIRROR
                        j.append('framing_request',{'id':t['id'],'request':req})
                with self.assertRaises(ValueError):replay(read_events(Path(d)/'events.jsonl'))
