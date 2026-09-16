import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behaviorlab.explorer import Notes, make_server
from behaviorlab.lab_musings import LabMusings


class LabMusingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)
        self.notes=Notes(self.path/'notes.sqlite');self.musings=LabMusings(self.notes)

    def tearDown(self):self.tmp.cleanup()

    def test_seed_preserves_researcher_words_and_separates_synthesis(self):
        entries=self.musings.all();self.assertEqual(len(entries),4)
        quotes=[m for m in entries if m['author']=='Local researcher']
        self.assertEqual(len(quotes),2)
        for m in quotes:
            self.assertEqual(m['body'],m['source']['original_text']);self.assertEqual(m['recorded_by'],'Codex')
        self.assertEqual({m['slot'] for m in entries if m['author']=='Codex'},{'purpose','map'})
        self.assertEqual(self.notes.all(),[])

    def test_restart_does_not_replace_edited_purpose_or_duplicate_seeds(self):
        m=next(m for m in self.musings.all() if m['slot']=='purpose')
        revised=self.musings.save(dict(m,body='An evolving purpose.',edited_by='Local researcher'))
        restarted=LabMusings(self.notes)
        self.assertEqual(len(restarted.all()),4)
        self.assertEqual(restarted.history(m['id'])[0],revised)
        self.assertEqual(len(restarted.export()['history']),5)

    def test_revision_conflicts_and_attribution_cannot_be_overwritten(self):
        m=next(m for m in self.musings.all() if m['slot']=='purpose')
        revised=self.musings.save(dict(m,body='A new direction.',edited_by='Local researcher'))
        self.assertEqual(revised['author'],'Codex');self.assertEqual(revised['edited_by'],'Local researcher')
        with self.assertRaisesRegex(ValueError,'reload'):self.musings.save(m)
        with self.assertRaisesRegex(ValueError,'authorship'):self.musings.save(dict(revised,author='Local researcher'))
        self.assertEqual(self.musings.history(m['id'])[1]['body'],m['body'])

    def test_edit_keeps_original_quote_and_prevents_source_or_slot_injection(self):
        m=next(m for m in self.musings.all() if m['source'].get('original_text'))
        changed=self.musings.save(dict(m,body='My revised reflection.',source={'original_text':'fabricated'},slot='purpose'))
        self.assertEqual(changed['source'],m['source']);self.assertIsNone(changed['slot'])
        new=self.musings.save({'title':'Fresh question','body':'What happens with a different partner?','source':{'original_text':'not supplied'},'slot':'purpose'})
        self.assertIsNone(new['source']);self.assertIsNone(new['slot'])

    def test_saved_reflection_links_to_known_collection_and_keeps_parked_history(self):
        data={'title':'Partner influence','body':'A literal <script> marker and café 🙂.','kind':'question','tags':['Partner','sampling'],'study_id':'known'}
        with self.assertRaisesRegex(ValueError,'collection'):self.musings.save(data)
        saved=self.musings.save(data,{'known'});self.assertEqual(saved['body'],data['body'])
        parked=self.musings.save(dict(saved,status='parked'),{'known'})
        self.assertEqual(parked['status'],'parked');self.assertEqual(len(self.musings.history(saved['id'])),2)
        self.assertEqual(self.notes.all(),[])

    def test_invalid_payloads_do_not_write_partial_revisions(self):
        n=len(self.musings.export()['history'])
        for data in ({'title':'','body':'x'},{'title':'x','body':''},{'title':'x','body':'y','kind':'result'},
                     {'title':'x','body':'y','author':'someone else'},{'title':'x','body':'y','tags':'not a list'},
                     {'id':'missing','title':'x','body':'y'}):
            with self.subTest(data=data),self.assertRaises(ValueError):self.musings.save(data)
        self.assertEqual(len(self.musings.export()['history']),n)

    def test_api_requires_local_write_token_and_exports_history(self):
        with patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda a,h:SimpleNamespace(server_port=8765,handler=h)):
            server=make_server(self.path)
        def call(method,path,data=None,headers=None):
            h=server.handler.__new__(server.handler);h.server=server;h.path=path
            raw=json.dumps(data).encode() if data is not None else b''
            h.headers={'Host':'127.0.0.1:8765','Content-Type':'application/json','Content-Length':str(len(raw)),**(headers or {})}
            h.rfile=io.BytesIO(raw);out=[];h.send=lambda d,status=200,**kw:out.append((status,d))
            getattr(h,'do_'+method)();return out[0]
        boot=call('GET','/api/bootstrap')[1];data={'title':'A question','body':'What changes with temperature?'}
        self.assertEqual(call('POST','/api/musings',data)[0],403)
        headers={'Origin':'http://127.0.0.1:8765','X-Explorer-Token':boot['token']}
        code,saved=call('POST','/api/musings',data,headers);self.assertEqual(code,200)
        self.assertEqual(saved['author'],'Local researcher')
        self.assertEqual(call('GET','/api/musings/history/'+saved['id'])[1]['history'][0],saved)
        self.assertEqual(call('GET','/api/musings/export')[1]['schema'],'behaviorlab.lab-musings/1')
        self.assertEqual(call('GET','/api/musings/history/missing')[0],400)


if __name__=='__main__':unittest.main()
