import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behaviorlab.explorer import Notes, make_server, REPORTS
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.lab_musings import LabMusings
from behaviorlab.lab_tasks import LabTasks
from behaviorlab.research_bundle import export_notebook, restore_notebook


class LabTasksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.notes = Notes(self.root/'notes.sqlite')
        self.musings = LabMusings(self.notes)
        self.studies = ResearchCollections(self.notes)
        self.catalog = SimpleNamespace(runs={'run1': {'id':'run1', 'title':'A <mirror>',
                     'messages':[{'id':'m1'}], 'segments':[{'id':'left'}]}})
        self.before = export_notebook(self.root/'notes.sqlite')
        self.tasks = LabTasks(self.notes,self.musings,self.studies,self.catalog,REPORTS)

    def tearDown(self): self.temp.cleanup()

    def test_seed_idempotence_and_old_notebook_preservation(self):
        self.assertEqual(len(self.tasks.all()),5)
        c=self.tasks.all()[0]
        saved=self.tasks.save(dict(c,title='Changed locally',archived=True,edited_by='Local researcher'))
        restarted=LabTasks(self.notes,self.musings,self.studies,self.catalog,REPORTS)
        self.assertEqual(restarted.history(c['id'])[0],saved)
        self.assertEqual(len(restarted.all()),5)
        after=export_notebook(self.root/'notes.sqlite')
        for name,table in self.before.items(): self.assertEqual(after[name],table)

    def test_quick_capture_revision_conflicts_and_original_author(self):
        c=self.tasks.save({'title':'One sentence'})
        self.assertEqual((c['status'],c['stream'],c['author']),('ideas','','Local researcher'))
        revised=self.tasks.save(dict(c,status='active',edited_by='Codex'))
        self.assertEqual(revised['author'],'Local researcher')
        with self.assertRaisesRegex(ValueError,'reload'): self.tasks.save(c)
        with self.assertRaisesRegex(ValueError,'authorship'): self.tasks.save(dict(revised,author='Codex'))
        self.assertEqual(self.tasks.history(c['id']),[revised,c])

    def test_musing_source_frozen_on_create_and_kept_after_edits(self):
        m=next(m for m in self.musings.all() if m['source'].get('original_text'))
        c=self.tasks.save({'title':'Explore this idea','from_musing':m['id'],'musing_revision':m['revision']})
        self.assertEqual(c['source']['body'],m['body'])
        self.assertEqual(c['source']['author'],m['author'])
        self.assertEqual(c['links'][0]['kind'],'musing')
        self.musings.save(dict(m,body='A revised idea'))
        revised=self.tasks.save(dict(c,notes='A different plan',source={'body':'fake'},from_musing='missing'))
        self.assertEqual(revised['source'],c['source'])
        with self.assertRaisesRegex(ValueError,'Musing changed'):
            self.tasks.save({'title':'Stale copy','from_musing':m['id'],'musing_revision':m['revision']})
        plain=self.tasks.save({'title':'No fabricated source','source':{'body':'fake'}})
        self.assertIsNone(plain['source'])

    def test_done_requires_note_archive_restore_and_reopen_keep_history(self):
        c=self.tasks.save({'title':'A task'})
        with self.assertRaisesRegex(ValueError,'completion'): self.tasks.save(dict(c,status='done'))
        done=self.tasks.save(dict(c,status='done',completion='Verified the view; report linked.'))
        archived=self.tasks.save(dict(done,archived=True))
        restored=self.tasks.save(dict(archived,archived=False,status='ideas'))
        self.assertEqual(restored['completion'],done['completion'])
        self.assertEqual(len(self.tasks.history(c['id'])),4)

    def test_priority_and_move_preserve_other_cards(self):
        a=self.tasks.save({'title':'First','status':'next'})
        b=self.tasks.save({'title':'Second','status':'next'})
        promoted=self.tasks.save(dict(b,placement='top'))
        self.assertEqual([c['id'] for c in self.tasks.all() if c['status']=='next'][0],b['id'])
        self.assertEqual(self.tasks.history(a['id']),[a])
        moved=self.tasks.save(dict(promoted,status='active'))
        self.assertEqual(moved['position'],0)

    def test_links_validate_identity_and_escape_boundaries(self):
        c=self.tasks.save({'title':'Read this','links':[{'kind':'url','url':'http://127.0.0.1:8765/?ui=x#run=run1&message=m1&branch=left'}]})
        self.assertEqual(c['links'],[{'kind':'passage','id':'run1','message':'m1','branch':'left','label':'A <mirror> · m1'}])
        for link in [{'kind':'url','url':'javascript:alert(1)'},{'kind':'url','url':'https://evil.invalid/#run=run1'},
                     {'kind':'passage','id':'run1','message':'missing'},{'kind':'passage','id':'run1','branch':'missing'},
                     {'kind':'musing','id':'missing'},{'kind':'view','id':'javascript:alert(1)'}]:
            with self.subTest(link=link),self.assertRaises(ValueError):
                self.tasks.save({'title':'Bad link','links':[link]})

    def test_invalid_payloads_do_not_create_revisions(self):
        before=self.tasks.export()
        for data in [{'title':''},{'title':'x','status':[]},{'title':'x','stream':[]},{'title':'x','archived':'true'},
                     {'title':'x','links':{}},{'title':'x','placement':'outside'},{'id':'missing','title':'x'}]:
            with self.subTest(data=data),self.assertRaises(ValueError):self.tasks.save(data)
        self.assertEqual(self.tasks.export(),before)

    def test_portable_notebook_roundtrip_captures_tasks_and_histories(self):
        c=self.tasks.save({'title':'Portable card'})
        self.tasks.save(dict(c,status='next'))
        tables=export_notebook(self.root/'notes.sqlite')
        restore_notebook(tables,self.root/'restored.sqlite')
        self.assertEqual(export_notebook(self.root/'restored.sqlite'),tables)

    def test_api_authentication_export_and_static_assets(self):
        with patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda a,h:SimpleNamespace(server_port=8765,handler=h)):
            server=make_server(self.root/'api')
        def call(method,path,data=None,headers=None):
            h=server.handler.__new__(server.handler);h.server=server;h.path=path
            raw=json.dumps(data).encode() if data is not None else b''
            h.headers={'Host':'127.0.0.1:8765','Content-Type':'application/json','Content-Length':str(len(raw)),**(headers or {})}
            h.rfile=io.BytesIO(raw);out=[];h.send=lambda d,status=200,**kw:out.append((status,d))
            getattr(h,'do_'+method)();return out[0]
        boot=call('GET','/api/bootstrap')[1]
        self.assertEqual(call('POST','/api/tasks',{'title':'x'})[0],403)
        headers={'Origin':'http://127.0.0.1:8765','X-Explorer-Token':boot['token']}
        status,c=call('POST','/api/tasks',{'title':'API task'},headers)
        self.assertEqual(status,200)
        self.assertEqual(call('GET','/api/tasks/history/'+c['id'])[1]['history'],[c])
        self.assertEqual(len(call('GET','/api/planning/export')[1]['tasks']['entries']),6)
        self.assertEqual(call('GET','/tasks.js')[0],200)
        self.assertEqual(call('GET','/api/tasks/history/missing')[0],400)


if __name__=='__main__': unittest.main()
