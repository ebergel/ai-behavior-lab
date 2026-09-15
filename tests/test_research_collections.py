import copy
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

from behaviorlab.explorer import Notes
from behaviorlab.exploration_collections import ResearchCollections


class ResearchCollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.notes=Notes(Path(self.tmp.name)/'notes.sqlite'); self.store=ResearchCollections(self.notes)
        run={'id':'r1','title':'Example','models':['model'],'condition':'closed','prompt':'Prompt','opening':None,'settings':{},
             'source':{'sha256':'original'},'kind':'reference','message_count':1,'cap_count':0,'repeat_count':0,
             'segments':[],'messages':[{'id':'m1','turn':1,'speaker':'X','text':'A 🙂 café passage','status':'recorded'}]}
        self.catalog=SimpleNamespace(runs={'r1':run})
        self.document={'title':'A question','question':'What happens?','summary':'Preliminary reading.',
            'author':'Codex','edited_by':'Codex','runs':[{'run_id':'r1','status':'passages_reviewed','reviewed_by':'Codex'}],
            'findings':[{'id':'f1','title':'A finding','text':'Interpretation.','kind':'observation','evidence':[
                {'run_id':'r1','message_id':'m1','start':2,'end':8,'quote':'🙂 café'}]}]}

    def test_sources_and_attribution_survive_reopen_and_export(self):
        d=self.store.save(self.document,self.catalog)
        reopened=ResearchCollections(Notes(self.notes.path)); result=reopened.export(d['id'],self.catalog)
        self.assertEqual(result['collection']['author'],'Codex')
        self.assertEqual(result['collection']['method'],'assistant_exploration_not_independent_rating')
        self.assertEqual(result['sources']['r1']['messages'][0]['text'],'A 🙂 café passage')
        self.assertTrue(result['collection']['findings'][0]['evidence'][0]['source_current'])
        self.assertEqual(self.notes.all(),[])

    def test_quote_validation_and_changed_source(self):
        bad=copy.deepcopy(self.document); bad['findings'][0]['evidence'][0]['quote']='invented'
        with self.assertRaisesRegex(ValueError,'exact source'): self.store.save(bad,self.catalog)
        d=self.store.save(self.document,self.catalog); self.catalog.runs['r1']['source']['sha256']='changed'
        self.assertFalse(self.store.detail(d['id'],self.catalog)['collection']['findings'][0]['evidence'][0]['source_current'])
        with self.assertRaisesRegex(ValueError,'source changed'): self.store.save(d,self.catalog)

    def test_revision_conflicts_and_original_attribution(self):
        first=self.store.save(self.document,self.catalog)
        second=self.store.save(dict(first,summary='Human edit',edited_by='Local researcher'),self.catalog)
        self.assertEqual(second['author'],'Codex'); self.assertEqual(second['edited_by'],'Local researcher')
        with self.assertRaisesRegex(ValueError,'reload'): self.store.save(first,self.catalog)
        with self.assertRaisesRegex(ValueError,'authorship'): self.store.save(dict(second,author='Local researcher'),self.catalog)
        with self.notes.connect() as db: self.assertEqual(db.execute('SELECT count(*) FROM collection_history').fetchone()[0],2)

    def test_membership_and_review_states(self):
        for mutation in ('unknown','duplicate','bad_status','outside'):
            bad=copy.deepcopy(self.document)
            if mutation=='unknown': bad['runs'][0]['run_id']='absent'
            if mutation=='duplicate': bad['runs'].append(bad['runs'][0])
            if mutation=='bad_status': bad['runs'][0]['status']='human_validated'
            if mutation=='outside': bad['findings'][0]['evidence'][0]['run_id']='absent'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError): self.store.save(bad,self.catalog)

    def test_personal_notes_join_collection_without_becoming_assistant_findings(self):
        d=self.store.save(self.document,self.catalog)
        n=self.notes.save({'run_id':'r1','text':'My own observation','study_id':d['id'],'tags':['reading']},self.catalog)
        result=self.store.detail(d['id'],self.catalog)
        self.assertEqual(result['notes'],[n]); self.assertEqual(n['author'],'Local researcher')
        self.assertEqual(len(result['collection']['findings']),1)
        with self.assertRaisesRegex(ValueError,'collection first'): self.notes.save(dict(run_id='r1',text='Invalid',study_id='absent'),self.catalog)

    def test_missing_source_stays_visible_and_original_saved_collection_is_retained(self):
        d=self.store.save(self.document,self.catalog); self.catalog.runs.clear()
        result=self.store.detail(d['id'],self.catalog)
        self.assertEqual(result['sources'],{}); self.assertEqual(len(result['collection']['runs']),1)
        self.assertFalse(result['collection']['findings'][0]['evidence'][0]['source_current'])
        self.assertNotIn('source_current',self.store.get(d['id'])['findings'][0]['evidence'][0])

    def test_invalid_structure_and_unsupported_semantic_promotion_are_rejected(self):
        for change in ({'runs':'bad'},{'author':'Independent human panel'},{'title':''},{'findings':[{}]}):
            with self.subTest(change=change),self.assertRaises(ValueError): self.store.save(dict(self.document,**change),self.catalog)


if __name__=='__main__': unittest.main()
