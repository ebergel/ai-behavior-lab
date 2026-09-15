import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behaviorlab.common import canonical, read_json, sha256
from behaviorlab.explorer import Catalog, Notes, load_campaign, load_legacy, make_server
from behaviorlab.legacy import import_corpus
from behaviorlab.runner import FakeBackend, create_campaign, execute
from test_core import setup_protocol


class ExplorerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.base=Path(self.tmp.name); self.workspace=self.base/'workspace'; self.workspace.mkdir()
        _,self.registry,self.protocol=setup_protocol()
        self.campaign=self.workspace/'trial'; create_campaign(self.campaign,self.protocol,self.registry)
        execute(self.campaign)
        self.raw=(self.campaign/'events.jsonl').read_bytes()
        self.source=self.base/'source'; path=self.source/'data'/'runs'; path.mkdir(parents=True)
        rows=[{'kind':'header','cond':'A','cond_name':'closed','pair_model':'historical:model','run':1,'turns':3,'system':'A historical prompt.','seed':10},
              {'kind':'message','turn':1,'speaker':'X','content':'Understanding 🙂 café <script>alert(1)</script>','done_reason':'stop'},
              {'kind':'third','after_turn':1,'content':'An outside intervention.'},
              {'kind':'message','turn':2,'speaker':'Y','content':'An unfinished reply','done_reason':'length','thinking':''},
              {'kind':'message','turn':3,'speaker':'X','content':'After the cap','done_reason':'stop'},
              {'kind':'footer','pair_turns':3}]
        (path/'A_run01.jsonl').write_text('\n'.join(canonical(r) for r in rows)+'\n')
        import_corpus(self.source,self.workspace/'corpus','https://example.test/source','fixture')

    def tearDown(self):
        self.assertEqual((self.campaign/'events.jsonl').read_bytes(),self.raw)
        self.tmp.cleanup()

    def test_discovery_separates_fixtures_and_searches_visible_text_only(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network')),patch.object(FakeBackend,'generate',side_effect=AssertionError('No inference')):
            c=Catalog(self.workspace)
        self.assertEqual(len(c.runs),2); self.assertEqual(c.search({},[])['total'],1)
        self.assertEqual(c.search({'scope':['synthetic']},[])['total'],1)
        found=c.search({'q':['UNDERSTANDING']},[])
        self.assertEqual(found['total'],1); self.assertEqual(found['runs'][0]['match_count'],1)
        self.assertEqual(c.search({'model':['absent']},[])['total'],0)
        self.assertEqual(c.search({'q':['A historical prompt.']},[])['total'],0)
        self.assertEqual(c.search({'q':['An outside intervention.']},[])['total'],1)
        self.assertEqual(c.search({'signal':['capped']},[])['total'],1)

    def test_original_interventions_caps_missing_settings_and_unicode_are_preserved(self):
        r=load_legacy(self.workspace/'corpus')[0]
        self.assertEqual([m['status'] for m in r['messages']],['recorded','intervention','cap','after_cap'])
        self.assertIn('<script>',r['messages'][0]['text'])
        self.assertIsNone(r['messages'][0]['thinking']); self.assertFalse(r['messages'][0]['thinking_recorded'])
        self.assertEqual(r['messages'][2]['thinking'],''); self.assertTrue(r['messages'][2]['thinking_recorded'])
        self.assertNotIn('temperature',r['settings'])
        self.assertEqual(r['cap_count'],1)

    def test_actual_restored_branch_and_request_are_exposed(self):
        run=load_campaign(self.campaign)[0]
        self.assertTrue(run['date']); self.assertEqual(len(run['messages']),14)
        restored=next(m for m in run['messages'] if m['id']=='AB-r01:RF:5')
        self.assertEqual(restored['parent'],'AB-r01:R:4')
        text=next(m['text'] for m in run['messages'] if m['id']=='AB-r01:R:4')
        self.assertEqual(restored['request']['messages'][-1]['content'],text)
        self.assertEqual(run['settings_by_speaker']['X'],read_json(self.protocol.settings_json))
        self.assertEqual(run['model_identities'][0]['digest'],self.registry.model('A').digest)

    def test_mixed_request_settings_are_not_flattened_to_one_model(self):
        from test_live import setup, FixtureHTTPBackend
        from behaviorlab.protocol import Protocol
        registry,data,_=setup()
        data['settings']['by_model']['A']['options']['temperature']=0.3
        data['settings']['by_model']['B']['options']['temperature']=0.7
        protocol=Protocol.from_dict(data,registry)
        path=self.workspace/'mixed'; create_campaign(path,protocol,registry)
        execute(path,backend=FixtureHTTPBackend())
        r=load_campaign(path)[0]
        self.assertEqual(r['settings_by_speaker']['X']['options']['temperature'],0.3)
        self.assertEqual(r['settings_by_speaker']['Y']['options']['temperature'],0.7)
        self.assertEqual(r['messages'][0]['request']['options']['temperature'],0.3)
        self.assertEqual(r['messages'][1]['request']['options']['temperature'],0.7)

    def test_cap_descendants_are_unavailable_and_link_to_original_failure(self):
        class Cap(FakeBackend):
            def generate(self,p):
                d=read_json(super().generate(p))
                if self.calls==2: d['done_reason']='length'
                return canonical(d)
        directory=self.workspace/'cap'; create_campaign(directory,self.protocol,self.registry); execute(directory,backend=Cap())
        r=load_campaign(directory)[0]
        self.assertEqual(r['cap_count'],1); self.assertEqual(r['unavailable_count'],12)
        blocked=[m for m in r['messages'] if m['status']=='blocked']
        self.assertEqual({m['blocking_node'] for m in blocked},{'AB-r01:prefix:2'})
        self.assertTrue(all(m['text'] is None for m in blocked))

    def test_uncertain_and_saved_uncommitted_outputs_remain_distinct(self):
        for stage,status,text_missing in [('after_request','unresolved',True),('after_response','uncommitted',False)]:
            with self.subTest(stage=stage):
                path=self.workspace/stage; create_campaign(path,self.protocol,self.registry)
                def crash(point,node):
                    if point==stage: raise KeyboardInterrupt()
                with self.assertRaises(KeyboardInterrupt): execute(path,hook=crash)
                before=(path/'events.jsonl').read_bytes(); r=load_campaign(path)[0]
                self.assertFalse(r['complete']); self.assertEqual(r['messages'][0]['status'],status)
                self.assertEqual(r['messages'][0]['text'] is None,text_missing)
                self.assertEqual((path/'events.jsonl').read_bytes(),before)

    def test_private_sources_are_excluded_and_corruption_is_visible(self):
        private=self.workspace/'private'/'hidden'; private.mkdir(parents=True); (private/'events.jsonl').write_bytes(self.raw)
        broken=self.workspace/'broken'; broken.mkdir(); (broken/'events.jsonl').write_bytes(self.raw.replace(b'campaign_created',b'campaign_changed',1))
        c=Catalog(self.workspace)
        self.assertEqual(len(c.runs),2); self.assertEqual(len(c.issues),1)
        self.assertIn('broken',c.issues[0]['source'])

    def note(self,c):
        run=next(r for r in c.runs.values() if r['kind']=='reference'); m=run['messages'][0]; start=m['text'].index('🙂')
        return {'run_id':run['id'],'message_id':m['id'],'quote':'🙂 café','start':start,'end':start+6,'text':'A question to revisit.','tags':['Reading','reading']}

    def test_notes_validate_codepoint_spans_survive_reopen_and_filter_runs(self):
        c=Catalog(self.workspace); path=self.workspace/'explorer'/'notes.sqlite'; n=Notes(path)
        data=self.note(c); saved=n.save(data,c)
        self.assertEqual(saved['tags'],['reading']); self.assertEqual(saved['method'],'personal_exploration_not_formal_annotation')
        self.assertEqual(Notes(path).all(),[saved])
        self.assertEqual(c.search({'tag':['reading']},n.all())['total'],1)
        bad=dict(data,quote='invented')
        with self.assertRaisesRegex(ValueError,'exact source'): n.save(bad,c)
        bad=dict(data,start=data['start']+1)
        with self.assertRaises(ValueError): n.save(bad,c)
        self.assertEqual(path.stat().st_mode&0o777,0o600)

    def test_note_conflicts_and_removal_keep_revision_history(self):
        c=Catalog(self.workspace); n=Notes(self.workspace/'explorer'/'notes.sqlite')
        first=n.save(self.note(c),c); second=n.save(dict(first,text='Revised thought.'),c)
        self.assertEqual(second['revision'],2)
        with self.assertRaisesRegex(ValueError,'reload'): n.save(first,c)
        with self.assertRaisesRegex(ValueError,'reload'): n.delete({'id':first['id'],'revision':1})
        n.delete({'id':second['id'],'revision':2}); self.assertEqual(n.all(),[])
        with n.connect() as db: self.assertEqual(db.execute('SELECT count(*) FROM history').fetchone()[0],3)

    def test_http_local_origin_limits_and_note_export_contract(self):
        def construct(address,handler): return SimpleNamespace(server_port=8765,handler=handler)
        with patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=construct): server=make_server(self.workspace)
        def call(method,path,body=None,headers=None):
            h=server.handler.__new__(server.handler); h.server=server; h.path=path
            raw=canonical(body).encode() if body is not None else b''
            h.headers={'Host':'127.0.0.1:8765','Content-Type':'application/json','Content-Length':str(len(raw)),**(headers or {})}
            h.rfile=io.BytesIO(raw); captured=[]
            h.send=lambda data,status=200,**kwargs:captured.append((status,data,kwargs))
            getattr(h,'do_'+method)(); return captured[0]
        code,boot,_=call('GET','/api/bootstrap'); self.assertEqual(code,200)
        self.assertEqual(call('GET','/api/assessments')[1],{'assessments':[],'prior_checks':[]})
        self.assertEqual(call('POST','/api/assessments',{})[0],403)
        self.assertEqual(boot['counts'],{'reference':1,'synthetic':1}); self.assertNotIn('lab',boot['collections'])
        self.assertEqual(call('GET','/api/bootstrap',headers={'Host':'attacker.test'})[0],403)
        self.assertEqual(call('GET','/api/runs',headers={'Origin':'https://attacker.test'})[0],403)
        note=self.note(server.catalog)
        self.assertEqual(call('POST','/api/notes',note)[0],403)
        headers={'Origin':'http://127.0.0.1:8765','X-Explorer-Token':boot['token']}
        self.assertEqual(call('POST','/api/notes',note,headers)[0],200)
        code,data,meta=call('GET','/api/notes/export'); self.assertEqual(len(data['notes']),1)
        self.assertEqual(meta['download'],'behavior-lab-notebook.json')
        self.assertEqual(call('GET','/../../private/webui-token')[0],404)
        collection={'title':'HTTP collection','author':'Codex','edited_by':'Codex','runs':[{'run_id':note['run_id']}],'findings':[]}
        self.assertEqual(call('POST','/api/studies',collection)[0],403)
        code,saved,_=call('POST','/api/studies',collection,headers); self.assertEqual(code,200)
        code,bundle,meta=call('GET','/api/studies/'+saved['id']+'/export')
        self.assertEqual(code,200); self.assertEqual(bundle['schema'],'behaviorlab.research-collection/1')
        self.assertIn(note['run_id'],bundle['sources']); self.assertIn('research-collection-',meta['download'])
        self.assertEqual(call('GET','/api/studies/'+saved['id']+'/unknown')[0],400)



if __name__=='__main__': unittest.main()
