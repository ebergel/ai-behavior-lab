import copy
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from behaviorlab.lab_summary import inventory, assessment, build_summary, percent, source_label
from behaviorlab.explorer import make_server
from test_topic_atlas import run


def source(identity='r', kind='lab', texts=None):
    r=run(identity, texts=['one','two','three','four','five','six'],kind=kind)
    r.update(data_class='fixture',prompt='Open',settings={},complete=True,segments=[],probes=[])
    r['source']['path']='/workspace/experiment-'+identity
    for m in r['messages']: m['kind']='message'
    if texts is not None:
        r['messages']=r['messages'][:len(texts)]
        for m,text in zip(r['messages'],texts):m['text']=text
    return r


class SummaryTests(unittest.TestCase):
    def test_source_labels_distinguish_same_folder_names_in_different_experiments(self):
        self.assertEqual(source_label('/workspace/a/campaign','/workspace'),'a/campaign')
        self.assertEqual(source_label('/workspace/b/campaign','/workspace'),'b/campaign')

    def test_inventory_preserves_empty_texts_counts_z_and_deduplicates_branch_nodes(self):
        real=source(texts=['',None,'  ','z'])
        real['messages'][3]['speaker']='Z'
        real['messages'].append(copy.deepcopy(real['messages'][3]))
        real['messages'].append(dict(real['messages'][0],id='external',kind='third',text='guest',speaker='Observer'))
        synthetic=source('fake','synthetic',texts=['fixture'])
        pending=source('pending',texts=['not generated']);pending['unstarted_assessment']=True
        c=SimpleNamespace(runs={r['id']:r for r in [real,synthetic,pending]})
        before=copy.deepcopy(c.runs);data,index=inventory(c)
        self.assertEqual(c.runs,before)
        self.assertEqual((data['real_messages'],data['synthetic_messages'],data['messages']),(3,1,4))
        self.assertEqual(data['empty_messages']['real'],1);self.assertEqual(data['whitespace_messages']['real'],1)
        self.assertEqual((data['run_count'],data['unstarted']),(2,1))
        self.assertEqual(data['real_share'],75)
        self.assertEqual(sum(g['share_all'] for g in data['experiments']),100)
        self.assertEqual(sum(g['messages'] for g in data['experiments']),4)
        self.assertEqual(sum(g['interventions'] for g in data['experiments']),1)
        self.assertIn(('r','r:4'),index);self.assertNotIn(('pending','pending:1'),index)

    def test_assessments_use_source_identity_and_keep_control_texts_out_of_denominators(self):
        data,index=inventory(SimpleNamespace(runs={'r':source(texts=['one','two'])}))
        def sample(mid,**kw):return dict(id=mid,run_id='r',message_id='r:'+mid,source_sha256='rsource',text='one' if mid=='1' else 'two',complete=True,**kw)
        samples=[sample('1'),sample('1'),dict(sample('2'),source_sha256='old'),{'id':'control','kind':'synthetic','complete':True}]
        row,keys=assessment('a','A',samples,index,questions=53,packs=2)
        self.assertEqual((row['real_sample'],row['real_complete'],row['controls'],row['controls_complete']),(2,2,1,1))
        self.assertEqual((row['covered_messages'],row['coverage'],row['stale_messages']),(1,50,1))
        self.assertEqual(keys,{('r','r:1')});self.assertEqual(row['status'],'Source changed')
        # Two partially completed wordings cannot count as a fully assessed message.
        partial,_=assessment('a','A',[sample('1'),dict(sample('1'),complete=False)],index,questions=2,wordings=2)
        self.assertEqual(partial['real_complete'],0);self.assertEqual(partial['covered_messages'],0)
        self.assertIsNone(percent(0,0))

    def test_union_does_not_add_overlapping_batches_or_turn_errors_into_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp);root=w/'jev-atlas'
            for name in ['a','b','broken']:
                (root/'batches'/name).mkdir(parents=True);(root/'batches'/name/'plan.json').touch()
            real=source(texts=['one','two']);c=SimpleNamespace(runs={'r':real},issues=[],probes=[],indexed_at='now')
            def plan(name):
                if name=='broken':raise ValueError('Cannot verify receipt')
                return {'id':name,'title':name,'questions':{'q':{}}}
            def results(p):return [{'id':'i','run_id':'r','message_id':'r:1','source_sha256':'rsource','text':'one','status':'complete'}]
            jev=SimpleNamespace(root=root,plan=plan,results=results)
            d=build_summary(w,c,None,SimpleNamespace(batches=lambda:[]),jev)
            self.assertEqual(d['assessment_union'],{'covered_messages':1,'denominator':2,'coverage':50})
            self.assertEqual(len(d['issues']),1)
            missing=next(r for r in d['assessments'] if r['id']=='broken')
            self.assertEqual(missing['status'],'Unavailable');self.assertNotIn('coverage',missing)

    def test_prepared_corpus_without_execution_release_remains_visible(self):
        from behaviorlab.jev_atlas import write_record
        from behaviorlab import analysis_corpus
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp);root=w/analysis_corpus.CORPUS;root.mkdir(parents=True)
            write_record(root/'plan.json',{'targets':[{'id':'t','run_id':'r','message_id':'r:1','source_sha256':'rsource','text':'one'}], 'packs':{'broad':{'questions':{'a':{}}},'detail':{'questions':{'b':{}}}}})
            c=SimpleNamespace(runs={'r':source(texts=['one'])},issues=[],probes=[])
            d=build_summary(w,c,None,SimpleNamespace(batches=lambda:[]),SimpleNamespace(root=w/'jev-atlas'))
            row=d['assessments'][0]
            self.assertEqual(row['status'],'Unassessed');self.assertEqual(row['real_sample'],1)
            self.assertEqual(row['covered_messages'],0);self.assertIsNone(row['href'])
            self.assertEqual((row['questions'],row['packs']),(2,2))

    def test_endpoint_handles_empty_workspace_and_export_without_inference(self):
        with tempfile.TemporaryDirectory() as tmp,patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda a,h:SimpleNamespace(server_port=8765,handler=h)):
            server=make_server(Path(tmp))
            for path in ['/api/lab-summary','/api/lab-summary/export']:
                h=server.handler.__new__(server.handler);h.server=server;h.path=path;h.headers={'Host':'127.0.0.1:8765'};h.rfile=io.BytesIO()
                out=[];h.send=lambda d,status=200,**kw:out.append((status,d,kw))
                with patch('urllib.request.urlopen',side_effect=AssertionError('No inference/network')):h.do_GET()
                status,data,meta=out[0];self.assertEqual(status,200)
                self.assertEqual(data['inventory']['messages'],0);self.assertIsNone(data['assessment_union']['coverage'])
                self.assertEqual(data['assessments'],[])
                if path.endswith('export'):self.assertEqual(meta['download'],'behavior-lab-summary.json')
