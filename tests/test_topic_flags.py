import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behaviorlab.common import canonical
from behaviorlab.explorer import Catalog, Notes, base_summary, make_server
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.topic_flags import TopicFlags


class TopicFlagTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.notes=Notes(Path(self.tmp.name)/'notes.sqlite');self.flags=TopicFlags(self.notes)
        message=dict(id='m1',turn=1,speaker='X',text='🙂 Do we have subjective experience?',status='recorded',
                     segment='conversation',kind='message',thinking_recorded=False,repeat=False)
        run=dict(id='r1',title='Example',kind='reference',collection_id='test',collection='test',models=['model'],condition='anonymous',
                 model_kind='test',source={'sha256':'original'},messages=[message],date='2026-09-16',complete=True,
                 prompt='Open conversation',opening=None,settings={},segments=[],leaves=[],data_class='test')
        self.catalog=Catalog.__new__(Catalog);self.catalog.runs={'r1':base_summary(run)}
        self.data=dict(run_id='r1',message_id='m1',start=2,end=len(message['text']),quote=message['text'][2:],
            topics=['experience'],referent='participants',stance='question',origin='model_introduced',author='Codex',edited_by='Codex')

    def test_exact_unicode_passage_and_topic_filter_include_broader_discussion(self):
        self.flags.save(self.data,self.catalog);rows=self.flags.all(self.catalog)
        self.assertEqual(self.catalog.search({'topic':['any']},[],rows)['total'],1)
        self.assertEqual(self.catalog.search({'topic':['experience']},[],rows)['total'],1)
        self.assertEqual(self.catalog.search({'topic':['nonduality']},[],rows)['total'],0)
        self.assertEqual(self.catalog.search({},[],[])['total'],1) # Unannotated still browsable.
        for change in ({'start':3},{'quote':'invented'},{'start':True},{'source_sha256':'changed'}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.flags.save(dict(self.data,**change),self.catalog)

    def test_nonduality_is_in_umbrella_without_becoming_an_experience_claim(self):
        saved=self.flags.save(dict(self.data,topics=['nonduality'],stance='metaphor',referent='general'),self.catalog)
        self.assertEqual(saved['topics'],['nonduality'])
        self.assertEqual(self.catalog.search({'topic':['any']},[],self.flags.all(self.catalog))['total'],1)
        for change in ({'topics':[]},{'topics':['mystical_truth']},{'stance':'proven_conscious'},{'origin':'spontaneous_without_context'},{'referent':'realized_AI'}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.flags.save(dict(self.data,**change),self.catalog)

    def test_stale_or_missing_sources_remain_flagged_for_review_but_not_filter_positives(self):
        saved=self.flags.save(self.data,self.catalog)
        self.catalog.runs['r1']['source']['sha256']='new'
        rows=self.flags.all(self.catalog);self.assertFalse(rows[0]['source_current'])
        self.assertEqual(self.catalog.search({'topic':['any']},[],rows)['total'],0)
        with self.assertRaisesRegex(ValueError,'Source changed'):self.flags.save(saved,self.catalog)
        self.catalog.runs.clear();self.assertEqual(self.flags.all(self.catalog)[0]['run_title'],'Source unavailable')

    def test_authorship_concurrency_and_removed_history_preserve_personal_notes(self):
        note=self.notes.save(dict(run_id='r1',text='My observation',tags=[]),self.catalog)
        first=self.flags.save(self.data,self.catalog)
        second=self.flags.save(dict(first,note='Human interpretation',edited_by='Local researcher'),self.catalog)
        self.assertEqual(second['author'],'Codex');self.assertEqual(second['edited_by'],'Local researcher')
        with self.assertRaisesRegex(ValueError,'reload'):self.flags.save(first,self.catalog)
        with self.assertRaisesRegex(ValueError,'authorship'):self.flags.save(dict(second,author='Local researcher'),self.catalog)
        with self.assertRaisesRegex(ValueError,'reload'):self.flags.delete(dict(id=first['id'],revision=1))
        self.flags.delete(dict(id=second['id'],revision=2))
        reopened=TopicFlags(Notes(self.notes.path));self.assertEqual(reopened.all(self.catalog),[])
        self.assertEqual(len(reopened.export(self.catalog)['history']),3)
        self.assertEqual(self.notes.all(),[note])

    def test_collection_export_joins_flags_without_changing_collection_revision(self):
        store=ResearchCollections(self.notes);c=store.save(dict(title='Reading',runs=[{'run_id':'r1'}],findings=[]),self.catalog)
        self.flags.save(self.data,self.catalog);bundle=store.export(c['id'],self.catalog)
        self.assertEqual(len(bundle['topic_flags']),1);self.assertEqual(store.get(c['id']),c)
        self.assertEqual(bundle['topic_flags'][0]['method'],'assistant_exploration_not_independent_rating')

    def test_api_authentication_export_and_library_filter(self):
        with patch('behaviorlab.explorer.Catalog',return_value=self.catalog),patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda address,handler:SimpleNamespace(server_port=8765,handler=handler)):
            self.catalog.indexed_at='now';self.catalog.issues=[]
            server=make_server(Path(self.tmp.name))
        def call(method,path,data=None,headers=None):
            h=server.handler.__new__(server.handler);h.server=server;h.path=path
            raw=canonical(data).encode() if data is not None else b''
            h.headers={'Host':'127.0.0.1:8765','Content-Type':'application/json','Content-Length':str(len(raw)),**(headers or {})}
            h.rfile=io.BytesIO(raw);out=[];h.send=lambda data,status=200,**kwargs:out.append((status,data,kwargs))
            getattr(h,'do_'+method)();return out[0]
        boot=call('GET','/api/bootstrap')[1]
        self.assertEqual(call('POST','/api/topics',self.data)[0],403)
        headers={'Origin':'http://127.0.0.1:8765','X-Explorer-Token':boot['token']}
        self.assertEqual(call('POST','/api/topics',self.data,headers)[0],200)
        self.assertEqual(call('GET','/api/runs?topic=experience')[1]['total'],1)
        self.assertEqual(len(call('GET','/api/runs/r1')[1]['topic_flags']),1)
        self.assertEqual(call('GET','/api/topics/export')[1]['schema'],'behaviorlab.topic-flags/1')
        self.assertEqual(call('GET','/api/runs?topic=unknown')[0],400)
