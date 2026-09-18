"""Analysis must preserve source evidence and avoid duplicate/reinterpreted rows."""
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from behaviorlab.analysis_workspace import AnalysisWorkspace
from behaviorlab.common import fingerprint, canonical
from behaviorlab.explorer import make_server


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = {'source': {'sha256': 'source'}, 'messages': [{'id':'m','text':'target','model':'anthropic/claude-haiku-4.5'}], 'experiment': {'identity':'Anonymous-AI','models':['anthropic/claude-haiku-4.5']}}
        self.catalog = SimpleNamespace(runs={'r':self.run})
        self.app = AnalysisWorkspace(self.root, self.catalog)
        self.item = {'id':'i','run_id':'r','run_title':'Dialogue','message_id':'m','source_sha256':'source','text':'target','context':[], 'status':'complete','answers':{'topic_a':{'noul':.9},'topic_b':{'noul':0}},'speaker':'Y','turn':2,'condition':'free','message_status':'complete'}
        self.plans = {b:{'id':b,'sha256':b,'dictionary':[{'id':t,'title':t,'group':'broad','definition':'question '+t}], 'topics':[t]} for b,t in [('b1','a'),('b2','b')]}
        self.app.sources = lambda _: [{'batch':'b1','items':None},{'batch':'b2','items':['i']}]
        self.app.store = SimpleNamespace(plan=lambda b:self.plans[b], results=lambda p:[copy.deepcopy(self.item)], batch_path=lambda b:self.root/b)

    def test_join_reused_sources_by_passage_and_keep_zero_and_speaker(self):
        d=self.app.dataset('intact')
        self.assertEqual(len(d['rows']),1)
        r=d['rows'][0]
        self.assertEqual((r['Score · a'],r['Score · b']),(90,0))
        self.assertEqual((r['Model family'],r['Identity']),('Anthropic','Anonymous-AI'))
        self.assertEqual(len(d['provenance']),2)
        self.assertEqual(d['coverage']['questions'],2)
        self.assertEqual(d['fingerprint'],self.app.dataset('intact')['fingerprint'])

    def test_missing_and_changed_sources_are_unknown(self):
        self.item['status']='error'
        d=self.app.dataset('intact'); self.assertIsNone(d['rows'][0]['Score · a'])
        self.assertEqual(d['coverage']['complete'],0)
        self.item['status']='complete';self.run['messages'][0]['text']='modified'
        d=self.app.dataset('intact');self.assertIsNone(d['rows'][0]['Score · b'])
        self.assertFalse(d['passages']['i']['source_current'])

    def test_duplicate_question_and_mismatched_target_are_rejected(self):
        self.plans['b2']=dict(self.plans['b1'],id='b2')
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.app.dataset('intact')
        self.plans['b2']['dictionary']=[{'id':'a','title':'a','group':'broad','definition':'changed'}]
        with self.assertRaisesRegex(ValueError,'definitions'):self.app.dataset('intact')

    def test_versioned_save_keeps_history_and_provenance(self):
        d=self.app.dataset('intact'); before=copy.deepcopy(self.item)
        body={'dataset':'intact','dataset_fingerprint':d['fingerprint'],'title':'Test analysis','author':'Codex','config':{'version':1,'transforms':{'Score · a':{'mode':'binary','threshold':90}},'topicSelector':{'group':'broad','field':'Score · b'}}}
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('No inference')):
            a=self.app.save(body)
            b=self.app.save(dict(body,id=a['id'],revision=1,note='An observation'))
        self.assertEqual(b['revision'],2);self.assertEqual(self.app.views()[0]['note'],'An observation')
        self.assertEqual(len(list((self.root/'analysis'/'views'/a['id']).glob('*.json'))),2)
        self.assertEqual(b['provenance'],d['provenance']);self.assertEqual(self.item,before)
        self.assertEqual(b['config'],body['config'])
        self.assertEqual(self.app.views()[0]['config']['topicSelector'],body['config']['topicSelector'])
        with self.assertRaisesRegex(ValueError,'changed'):self.app.save(dict(body,id=a['id'],revision=1))
        with self.assertRaisesRegex(ValueError,'changed'):self.app.save(dict(body,dataset_fingerprint='old'))

    def test_validation_rejects_unsafe_paths_nonfinite_and_stale_quantiles(self):
        d=self.app.dataset('intact');body={'dataset':'intact','dataset_fingerprint':d['fingerprint'],'title':'x','config':{'version':1,'transforms':{}}}
        for change in [{'id':'../escape'},{'config':{'version':1,'transforms':[]}}, {'config':{'version':1,'transforms':{'Score · a':{'mode':'binary','threshold':float('nan')}}}}, {'config':{'version':1,'transforms':{'Score · a':{'mode':'quantile','cuts':[10,20],'reference':'stale'}}}}]:
            with self.assertRaises(ValueError): self.app.save(dict(body,**change))

    def test_http_routes_enforce_origin_and_keep_inference_unavailable(self):
        with patch('behaviorlab.explorer.ThreadingHTTPServer', side_effect=lambda address, handler: SimpleNamespace(server_port=8765, handler=handler)):
            server=make_server(self.root/'http-fixture')
        def call(method,path,body=None,headers=None):
            h=server.handler.__new__(server.handler);h.server=server;h.path=path
            raw=canonical(body).encode() if body is not None else b''
            h.headers={'Host':'127.0.0.1:8765','Content-Type':'application/json','Content-Length':str(len(raw)),**(headers or {})}
            h.rfile=io.BytesIO(raw);captured=[]
            h.send=lambda data,status=200,**kw:captured.append((status,data))
            getattr(h,'do_'+method)();return captured[0]
        dataset=self.app.dataset('intact')
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('No inference')), patch.object(AnalysisWorkspace,'dataset',return_value=dataset):
            self.assertEqual(call('GET','/api/analysis')[0],200)
            self.assertEqual(call('GET','/api/analysis/dataset?id=intact')[1]['fingerprint'],dataset['fingerprint'])
            self.assertEqual(call('GET','/analysis-widget.js')[0],200)
            self.assertEqual(call('POST','/api/analysis/views',{})[0],403)
            token=call('GET','/api/bootstrap')[1]['token']
            headers={'Origin':'http://127.0.0.1:8765','X-Explorer-Token':token}
            body={'dataset':'intact','dataset_fingerprint':dataset['fingerprint'],'title':'HTTP view','author':'Codex','config':{'version':1,'transforms':{}}}
            code,view=call('POST','/api/analysis/views',body,headers);self.assertEqual(code,200)
            self.assertEqual(call('GET','/api/analysis/export')[1]['history'][0]['id'],view['id'])
            self.assertEqual(call('POST','/api/analysis/run',{},headers)[0],404)

    def test_large_matrix_transport_compression_preserves_exact_json(self):
        import gzip
        with patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda address,handler:SimpleNamespace(server_port=8765,handler=handler)):
            server=make_server(self.root/'gzip-fixture')
        body={'rows':[{'text':'repeated test content '*50,'value':0} for _ in range(100)]}
        for accept,compressed in [('gzip, deflate',True),('gzip;q=0',False),('',False),('gzip;q=0.5',True)]:
            h=server.handler.__new__(server.handler);h.path='/api/analysis/dataset?id=corpus';h.headers={'Accept-Encoding':accept};h.wfile=io.BytesIO()
            headers={};h.send_response=lambda status:None;h.send_header=lambda k,v:headers.update({k:v});h.end_headers=lambda:None
            h.send(body);raw=h.wfile.getvalue()
            self.assertEqual(headers.get('Content-Encoding')=='gzip',compressed)
            self.assertEqual(int(headers['Content-Length']),len(raw))
            self.assertEqual(gzip.decompress(raw) if compressed else raw,canonical(body).encode())
            self.assertEqual(headers['Vary'],'Accept-Encoding')
