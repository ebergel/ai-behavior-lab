import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behaviorlab.analysis_workspace import AnalysisWorkspace
from behaviorlab.analysis_corpus import CORPUS, EXECUTION, matrix
from behaviorlab.common import canonical, fingerprint
from behaviorlab.jev_atlas import MODEL, ENDPOINT, PRICE, read_record, write_record
from behaviorlab.jev_campaign import prepare, payload
from test_jev_atlas import reply


class CorpusAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.ws=Path(self.tmp.name)
        self.pack={p:{'questions':{'topic_'+p:{'type':'noul','criteria':'Test'}},'dictionary':[{'id':p,'title':p,'group':'broad' if p=='broad' else 'focused'}]} for p in ['broad','detail']}
        self.plan={'model':MODEL,'endpoint':ENDPOINT,'inventory_sha256':'inventory','budget':{'usd_per_million_input':PRICE},'unavailable_positions':[{'id':'missing'}],
                   'packs':self.pack,'targets':[],'counts':{'new_calls':4,'reuse_requests':0,'logical_requests':4}}
        runs={}
        for n in range(2):
            t={'id':str(n)*24,'run_id':str(n),'message_id':'m','run_title':'Synthetic test','source_sha256':'source','speaker':'X','text':'Test target '+str(n),'context':[],
               'turn':1,'lineage':str(n),'condition':'test','split':'analysis','inventory_category':'conversation' if n==0 else 'technical_or_short','requests':{}}
            for v in self.pack:
                raw=payload(self.plan,t,v);t['requests'][v]={'payload_sha256':fingerprint(raw),'bytes':len(canonical(raw).encode())}
            self.plan['targets'].append(t)
            runs[str(n)]={'source':{'sha256':'source'},'messages':[{'id':'m','text':t['text'],'model':'anthropic/claude-haiku-4.5'}]}
        self.catalog=SimpleNamespace(runs=runs)
        p=self.ws/CORPUS/'plan.json';write_record(p,self.plan)
        self.release=prepare(self.ws,p,self.ws/EXECUTION,'Synthetic offline test')
        self.app=AnalysisWorkspace(self.ws,self.catalog)

    def response(self,n,v,value=.91):
        t=self.plan['targets'][n];p=self.ws/EXECUTION/'attempts'/t['id'];req={'payload':payload(self.plan,t,v),'release_sha256':self.release['sha256'],'target_id':t['id'],'variant':v}
        write_record(p/(v+'-001.request.json'),req);req=read_record(p/(v+'-001.request.json'))
        _,raw=reply(req['payload']);obj=json.loads(raw);obj['answers']['topic_'+v]['noul']=value
        write_record(p/(v+'-001.response.json'),{'http_status':200,'raw_text':json.dumps(obj),'request_sha256':req['sha256']})

    def test_missing_is_unknown_zero_is_observed_and_all_targets_remain(self):
        self.response(0,'broad',0)
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('No inference')):d=self.app.dataset('corpus')
        self.assertEqual(d['coverage']['passages'],2);self.assertEqual(d['coverage']['complete'],0)
        self.assertEqual(d['coverage']['unavailable_positions'],1)
        self.assertEqual(d['rows'][0]['Score · broad'],0);self.assertIsNone(d['rows'][0]['Score · detail'])
        self.assertIsNone(d['rows'][1]['Score · broad']);self.assertEqual(d['rows'][0]['Model family'],'Anthropic')
        self.assertEqual(d['rows'][1]['Inventory category'],'technical_or_short')

    def test_snapshot_stays_fixed_and_saved_view_survives_new_scores_and_restart(self):
        self.response(0,'broad');before=self.app.dataset('corpus')
        body={'dataset':'corpus','dataset_fingerprint':before['fingerprint'],'title':'Partial test','config':{'version':1,'transforms':{}}}
        saved=self.app.save(body)
        self.assertNotIn('receipts',saved['provenance'])
        self.assertEqual(saved['provenance']['receipt_count'],1)
        self.assertEqual(saved['provenance']['receipts_sha256'],fingerprint(before['provenance']['receipts']))
        self.response(0,'detail')
        self.assertEqual(self.app.dataset('corpus')['fingerprint'],before['fingerprint'])
        after=self.app.corpus_dataset(refresh=True);self.assertNotEqual(after['fingerprint'],before['fingerprint'])
        self.assertEqual(after['coverage']['complete'],1)
        restarted=AnalysisWorkspace(self.ws,self.catalog)
        old=restarted.corpus_dataset(saved['dataset_fingerprint'])
        self.assertEqual(old,before);self.assertEqual(restarted.views()[0]['dataset_fingerprint'],before['fingerprint'])
        self.assertEqual(restarted.save(dict(body,id=saved['id'],revision=1))['revision'],2)

    def test_source_change_removes_all_scores_on_refresh(self):
        self.response(0,'broad');self.response(0,'detail');self.app.dataset('corpus')
        self.catalog.runs['0']['messages'][0]['text']='edited'
        d=self.app.corpus_dataset(refresh=True)
        self.assertEqual(d['rows'][0]['Assessment status'],'Source changed / missing')
        self.assertIsNone(d['rows'][0]['Score · broad']);self.assertEqual(d['coverage']['complete'],0)

    def test_corrupt_receipt_rejected(self):
        self.response(0,'broad');self.app.dataset('corpus')
        p=self.ws/EXECUTION/'attempts'/('0'*24)/'broad-001.response.json'
        p.write_text(p.read_text().replace('0.91','0.92'))
        with self.assertRaisesRegex(ValueError,'checksum'):self.app.corpus_dataset(refresh=True)

    def test_snapshot_paths_are_constrained(self):
        for value in ['../plan','x'*64,'a'*64]:
            with self.assertRaises(ValueError):self.app.corpus_dataset(value)

    def test_restored_progress_uses_immutable_summary_and_stale_status_is_explicit(self):
        from behaviorlab.analysis_corpus import progress
        root=self.ws/EXECUTION
        write_record(root/'summaries'/'001.json',{'state':'complete','completed_targets':2})
        self.assertEqual(progress(self.ws)['state'],'complete')
        (root/'.status.json').write_text(json.dumps({'state':'running','at':'2020-01-01T00:00:00+00:00'}))
        self.assertEqual(progress(self.ws)['state'],'status stale')
