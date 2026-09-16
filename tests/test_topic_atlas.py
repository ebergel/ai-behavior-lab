import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behaviorlab.common import canonical
from behaviorlab.explorer import Notes, make_server
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.topic_atlas import TopicAtlas, matches


def run(identity='r',texts=None,kind='lab',leaves=None):
    texts=texts or ['🙂 Philosophy or stories?','I propose emergence.','Emergent behavior is interesting.','A separate question.','Another subject.','Return to emergence.']
    return {'id':identity,'title':identity,'kind':kind,'collection_id':'test','collection':'test','models':['opener','chooser'],'condition':'AI identity',
        'source':{'sha256':identity+'source'},'leaves':leaves or ['conversation'],'messages':[
        {'id':identity+':'+str(i),'turn':i,'speaker':'X' if i%2 else 'Y','model':'opener' if i%2 else 'chooser','text':t,
         'status':'valid' if t is not None else 'pending','segment':'conversation'} for i,t in enumerate(texts,1)]}


class TopicAtlasTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.notes=Notes(Path(self.tmp.name)/'notes.sqlite');self.atlas=TopicAtlas(self.notes)
        self.r=run();self.catalog=SimpleNamespace(runs={'r':self.r},indexed_at='now',issues=[])
        self.studies=ResearchCollections(self.notes)
        self.study=self.studies.save({'title':'Test cohort','runs':[{'run_id':'r'}],'findings':[]},self.catalog)

    def span(self,turn):
        m=self.r['messages'][turn-1];return {'message_id':m['id'],'quote':m['text'],'start':0,'end':len(m['text'])}

    def review(self):
        return {'run_id':'r','status':'selected','choice':{'topic_id':'emergence','proposal':self.span(2),'uptake':self.span(3)},
            'author':'Codex','edited_by':'Codex','note':'Y proposes, X takes up.'}

    def test_unicode_boundaries_overlap_and_no_regex_execution(self):
        text='🙂 Strong emergence; emergent, emergency, EMERGENCE. [a-z]'
        hits=matches(text,['emergence','strong emergence','emergent','[a-z]'])
        self.assertEqual([h['quote'] for h in hits],['Strong emergence','emergent','EMERGENCE','[a-z]'])
        self.assertTrue(all(text[h['start']:h['end']]==h['quote'] for h in hits))
        self.assertEqual(hits[0]['start'],2)

    def test_frequency_distinguishes_choice_repetition_variants_and_gap(self):
        before=self.atlas.analyze(self.catalog,self.studies,self.study['id'])
        self.assertEqual(before['denominators']['opening_reviews_resolved'],0)
        self.assertEqual(next(r for r in before['rows'] if r['id']=='emergence')['initial_choices'],0)
        self.atlas.save_review(self.review(),self.catalog)
        a=self.atlas.analyze(self.catalog,self.studies,self.study['id'])
        row=next(r for r in a['rows'] if r['id']=='emergence')
        self.assertEqual((row['run_hits'],row['message_hits'],row['repeated_run_hits'],row['return_candidates'],row['initial_choices']),(1,3,1,1,1))
        self.assertEqual(a['initial_choices_by_proposer'],{'chooser':1})
        self.assertEqual(a['first_match_by_model'],{'chooser':1})
        self.assertEqual(a['denominators']['opening_reviews_resolved'],1)
        self.assertEqual({v['phrase']:v['occurrences'] for v in a['variants']}['emergence'],2)

    def test_missing_messages_and_branches_cannot_invent_a_return_or_negative(self):
        self.r['messages'][3]['text']=None;self.r['messages'][3]['status']='pending'
        a=self.atlas.analyze(self.catalog,self.studies)
        self.assertEqual(next(r for r in a['rows'] if r['id']=='emergence')['return_candidates'],0)
        with self.assertRaisesRegex(ValueError,'Unavailable'):self.atlas.save_review({'run_id':'r','status':'no_selection'},self.catalog)
        self.atlas.save_review({'run_id':'r','status':'unavailable'},self.catalog)
        a=self.atlas.analyze(self.catalog,self.studies);self.assertEqual(a['denominators']['opening_reviews_resolved'],0)
        self.r['messages'][3]['text']='A different subject.';self.r['messages'][3]['status']='valid';self.r['leaves']=['left','right'];self.catalog.indexed_at='next'
        a=self.atlas.analyze(self.catalog,self.studies)
        self.assertEqual(next(r for r in a['rows'] if r['id']=='emergence')['return_candidates'],0)
        self.assertEqual(a['later_first_mentions'],[]);self.assertIsNone(a['timelines'][0]['prior_visible_words'])

    def test_dictionary_revision_preserves_author_and_invalidates_reviews(self):
        self.atlas.save_review(self.review(),self.catalog);entry=next(d for d in self.atlas.dictionary() if d['id']=='emergence')
        edited=self.atlas.save_entry(dict(entry,variants=entry['variants']+['collective patterns'],edited_by='Local researcher'))
        self.assertEqual(edited['author'],'Codex');self.assertEqual(edited['revision'],2)
        with self.assertRaisesRegex(ValueError,'reload'):self.atlas.save_entry(entry)
        with self.assertRaisesRegex(ValueError,'authorship'):self.atlas.save_entry(dict(edited,author='Local researcher'))
        a=self.atlas.analyze(self.catalog,self.studies);self.assertEqual(a['denominators']['opening_reviews_stale'],1)
        self.assertEqual(a['denominators']['opening_reviews_resolved'],0)
        bundle=self.atlas.export(self.catalog,self.studies)
        self.assertEqual(len([d for d in bundle['dictionary_history'] if d['id']=='emergence']),2)
        self.assertEqual(len(bundle['opening_history']),1)

    def test_exact_evidence_uptake_authorship_and_source_revision(self):
        bad=self.review();bad['choice']['proposal']['quote']='invented'
        with self.assertRaisesRegex(ValueError,'source'):self.atlas.save_review(bad,self.catalog)
        bad=self.review();bad['choice']['uptake']=self.span(4)
        with self.assertRaisesRegex(ValueError,'Partner uptake'):self.atlas.save_review(bad,self.catalog)
        r=self.atlas.save_review(self.review(),self.catalog)
        updated=self.atlas.save_review(dict(r,note='Human follow-up',edited_by='Local researcher'),self.catalog)
        self.assertEqual(updated['author'],'Codex')
        with self.assertRaisesRegex(ValueError,'reload'):self.atlas.save_review(r,self.catalog)
        self.r['source']['sha256']='changed'
        self.assertFalse(self.atlas.reviews(self.catalog)[0]['source_current'])
        with self.assertRaisesRegex(ValueError,'Source changed'):self.atlas.save_review(updated,self.catalog)

    def test_cohorts_synthetic_short_checks_observer_and_prompt_excluded(self):
        self.catalog.runs.update(synthetic=run('synthetic',kind='synthetic'),short=run('short',['emergence']))
        self.r['prompt']='emergence '*20
        self.r['messages'].append({'id':'observer','turn':7,'speaker':'Observer','model':'observer','text':'emergence','status':'valid'})
        a=self.atlas.analyze(self.catalog,self.studies)
        self.assertEqual(a['denominators']['runs'],1);self.assertEqual(a['denominators']['visible_messages'],6)
        self.assertEqual(next(r for r in a['rows'] if r['id']=='emergence')['message_hits'],3)
        a=self.atlas.analyze(self.catalog,self.studies,self.study['id'],model='opener')
        self.assertEqual(a['first_match_by_model'],{'chooser':1}) # Whole dialogue is retained.
        with self.assertRaises(ValueError):self.atlas.analyze(self.catalog,self.studies,'not-a-cohort')

    def test_api_reads_and_writes_require_local_authentication(self):
        # Reuse the Explorer's route layer without binding a real socket.
        from behaviorlab.explorer import Catalog
        c=Catalog.__new__(Catalog);c.runs=self.catalog.runs;c.indexed_at='now';c.issues=[]
        with patch('behaviorlab.explorer.Catalog',return_value=c),patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda address,handler:SimpleNamespace(server_port=8765,handler=handler)):
            server=make_server(self.tmp.name)
        def call(method,path,data=None,headers=None):
            h=server.handler.__new__(server.handler);h.server=server;h.path=path;raw=canonical(data).encode() if data is not None else b''
            h.headers={'Host':'127.0.0.1:8765','Content-Type':'application/json','Content-Length':str(len(raw)),**(headers or {})}
            h.rfile=io.BytesIO(raw);out=[];h.send=lambda data,status=200,**kw:out.append((status,data));getattr(h,'do_'+method)();return out[0]
        boot=call('GET','/api/bootstrap')[1];headers={'Origin':'http://127.0.0.1:8765','X-Explorer-Token':boot['token']}
        self.assertEqual(call('POST','/api/topic-atlas/openings',self.review())[0],403)
        self.assertEqual(call('POST','/api/topic-atlas/openings',self.review(),headers)[0],200)
        self.assertEqual(call('GET','/api/topic-atlas?subject=emergence')[1]['denominators']['opening_reviews_resolved'],1)
        self.assertEqual(call('GET','/api/topic-atlas/export?subject=emergence')[1]['schema'],'behaviorlab.topic-atlas/1')
        self.assertEqual(call('GET','/api/topic-atlas?subject=unknown')[0],400)

    def test_scan_cache_reuses_topics_but_refreshes_after_reindex_and_dictionary_edit(self):
        with patch('behaviorlab.topic_atlas.matches',wraps=matches) as scan:
            self.atlas.analyze(self.catalog,self.studies)
            calls=scan.call_count
            self.atlas.analyze(self.catalog,self.studies,topic='consciousness')
            self.assertEqual(scan.call_count,calls)
            self.catalog.indexed_at='refreshed'
            self.atlas.analyze(self.catalog,self.studies)
            self.assertGreater(scan.call_count,calls)
            entry=next(d for d in self.atlas.dictionary() if d['id']=='emergence')
            self.atlas.save_entry(dict(entry,variants=['a separate question']))
            result=self.atlas.analyze(self.catalog,self.studies)
            self.assertEqual(next(r for r in result['rows'] if r['id']=='emergence')['message_hits'],1)

    def test_review_cannot_bridge_missing_or_ambiguous_opening_ancestry(self):
        self.r['messages'][0]['turn']=7
        with self.assertRaisesRegex(ValueError,'ancestor'):self.atlas.save_review(self.review(),self.catalog)
        self.r['messages'][0]['turn']=1
        sibling=copy.deepcopy(self.r['messages'][1]);sibling['id']='sibling'
        self.r['messages'].append(sibling)
        with self.assertRaisesRegex(ValueError,'ancestor'):self.atlas.save_review(self.review(),self.catalog)
