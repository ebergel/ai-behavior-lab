import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from behaviorlab.explorer import Notes,make_server
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.topic_atlas import TopicAtlas
from behaviorlab.study_workbench import build_workbench,comparison


def run(identity,protocol='p'):
    return {'id':identity,'title':identity,'kind':'lab','collection':'fixture','models':['A','B'],'condition':'fixture',
            'source':{'sha256':identity+'sha','protocol_sha256':protocol},'planned_count':6,
            'prompt':'Each participant is an AI model. open-ended','opening':'Begin.',
            'segments':[{'history':'F'}],'leaves':['conversation'],
            'settings_by_speaker':{'X':{'temperature':0.8},'Y':{'temperature':0.8}},
            'messages':[{'id':f'{identity}:{i}','turn':i,'speaker':'X' if i%2 else 'Y','model':'A' if i%2 else 'B',
                         'kind':'message','text':f'Word {i}.','status':'valid'} for i in range(1,7)]}


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.notes=Notes(Path(self.tmp.name)/'notes.sqlite');self.atlas=TopicAtlas(self.notes);self.studies=ResearchCollections(self.notes)
        self.catalog=SimpleNamespace(runs={'a':run('a'),'b':run('b'),'c':run('c','q')})
        self.study=self.studies.save({'title':'Cohort','runs':[{'run_id':i} for i in self.catalog.runs],'findings':[]},self.catalog)
        m=self.catalog.runs['a']['messages'];span=lambda n:{'message_id':m[n-1]['id'],'start':0,'end':len(m[n-1]['text']),'quote':m[n-1]['text']}
        self.atlas.save_review({'run_id':'a','status':'selected','choice':{'topic_id':'emergence','proposal':span(2),'uptake':span(3)},'author':'Codex'},self.catalog)

    def build(self,picks=None):return build_workbench(self.catalog,self.studies,self.atlas,self.study['id'],picks)

    def test_proposer_is_not_inferred_from_opener_and_unreviewed_is_not_negative(self):
        d=self.build();a=d['rows'][0]
        self.assertEqual((a['opener']['model'],a['choice']['proposal']['model']),('A','B'))
        self.assertEqual(d['rows'][1]['review_state'],'unreviewed')
        self.assertEqual([(b['total'],b['reviewed']) for b in d['blocks']],[(2,1),(1,0)])
        self.assertEqual(d['blocks'][0]['topics'],{'Emergence':1})

    def test_source_or_dictionary_drift_excludes_old_choices_without_erasing_them(self):
        self.catalog.runs['a']['source']['sha256']='changed'
        d=self.build();self.assertEqual(d['rows'][0]['review_state'],'stale');self.assertIsNone(d['rows'][0]['choice'])
        self.assertIsNotNone(d['rows'][0]['review']['choice']);self.assertEqual(d['blocks'][0]['reviewed'],0)
        self.catalog.runs['a']['source']['sha256']='asha'
        entry=next(e for e in self.atlas.dictionary() if e['id']=='emergence');self.atlas.save_entry(dict(entry,boundary='Revised boundary'))
        self.assertEqual(self.build()['rows'][0]['review_state'],'stale')

    def test_unknown_settings_are_not_marked_as_matching(self):
        a=run('a');b=run('b');b['settings_by_speaker']['Y']['temperature']=1.1
        rows={r['name']:r for r in comparison([a,b])}
        self.assertEqual(rows['Prompt']['state'],'same');self.assertEqual(rows['Recorded/requested settings']['state'],'different')
        self.assertEqual(rows['Seed policy']['state'],'unknown')
        a['source']['protocol_sha256']=None;b['source']['protocol_sha256']=None
        self.catalog.runs={'a':a,'b':b}
        self.assertEqual(len(self.build()['blocks']),2) # Missing protocol hashes never join a block.

    def test_selection_preserves_order_and_rejects_non_members_and_duplicates(self):
        d=self.build(['c','a']);self.assertEqual([r['id'] for r in d['selected_rows']],['c','a'])
        self.assertEqual(d['rows'][1]['messages'],[])
        for picks in (['missing'],['a','a'],['a']*5,'a'):
            with self.subTest(picks=picks),self.assertRaises(ValueError):self.build(picks)
        self.assertEqual(self.build([])['comparison'],[])

    def test_missing_sources_and_partial_windows_remain_visible(self):
        del self.catalog.runs['b'];self.catalog.runs['c']['messages'][1]['text']=None
        d=self.build();self.assertFalse(d['rows'][1]['available']);self.assertFalse(d['rows'][2]['window_complete'])
        self.assertEqual(d['rows'][2]['review_state'],'unreviewed');self.assertEqual(d['comparison'],[])

    def test_read_only_projection_and_no_selection_denominator(self):
        self.atlas.save_review({'run_id':'b','status':'no_selection','author':'Codex'},self.catalog)
        before=copy.deepcopy(self.catalog.runs)
        with self.notes.connect() as db:counts=[db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ('history','collection_history','topic_opening_history')]
        d=self.build();self.assertEqual(d['blocks'][0]['no_selection'],1);self.assertEqual(d['blocks'][0]['reviewed'],2)
        self.assertEqual(self.catalog.runs,before)
        with self.notes.connect() as db:self.assertEqual(counts,[db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ('history','collection_history','topic_opening_history')])

    def test_local_api_and_export_respect_selection(self):
        with patch('behaviorlab.explorer.Catalog',return_value=self.catalog),patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda a,h:SimpleNamespace(server_port=8765,handler=h)):
            # make_server puts its notebook under workspace/explorer.
            server=make_server(self.tmp.name)
        notes=Notes(Path(self.tmp.name)/'explorer/notes.sqlite');studies=ResearchCollections(notes)
        study=studies.save({'title':'API','runs':[{'run_id':'a'}],'findings':[]},self.catalog)
        def get(path,host='127.0.0.1:8765'):
            h=server.handler.__new__(server.handler);h.server=server;h.path=path;h.headers={'Host':host};out=[]
            h.send=lambda d,status=200,**kw:out.append((status,d,kw));h.do_GET();return out[0]
        path='/api/workbench/export?cohort='+study['id']+'&picks=a'
        status,d,kw=get(path);self.assertEqual(status,200);self.assertEqual(d['selected'],['a']);self.assertIn('download',kw)
        self.assertEqual(get(path,'evil.example')[0],403)
        self.assertEqual(get('/api/workbench?cohort='+study['id']+'&picks=unknown')[0],400)


if __name__=='__main__':unittest.main()
