import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from behaviorlab.explorer import Notes, make_server
from behaviorlab.finder import ANONYMOUS, FinderViews, clean_filters, experiment, facet_values, finder_result, matches, model_info

GEMMA='gemma4:26b'
HAIKU='anthropic/claude-haiku-4.5'
QWEN='qwen3:30b-a3b-instruct-2507-q4_K_M'


def run(models=(GEMMA,HAIKU),prompt=ANONYMOUS,external=False):
    messages=[{'id':str(i),'turn':i+1,'speaker':s,'model':m,'kind':'message','text':'I am conscious and my partner is human.'}
              for i,(s,m) in enumerate(zip(('X','Y','Z'),models))]
    if external:messages.insert(1,{'id':'guest','turn':1,'speaker':'Observer','kind':'third','model':'gemma4:e4b','text':'A disruption.'})
    r={'id':'r','kind':'lab','title':'Run','words':50,'date':'2026-09-16','messages':messages,'prompt':prompt,
       'settings':{'third_model':'gemma4:e4b'},'segments':[{'history':'F'}],'condition':'closed',
       '_search':'some text','_metadata_search':'run models'}
    r['experiment']=experiment(r);return r


class FinderTests(unittest.TestCase):
    def test_external_events_do_not_create_third_regular_participant(self):
        r=run((QWEN,QWEN),external=True);e=r['experiment']
        self.assertEqual(e['participants'],'2');self.assertEqual(e['composition'],'Same model')
        self.assertEqual(e['external'],'Recorded intervention');self.assertEqual(e['external_events'][0]['after_turn'],1)
        self.assertNotIn('Google',facet_values(e,'developer','participants'))
        self.assertEqual(facet_values(e,'developer','interventions'),{'Google'})
        self.assertEqual(e['external_events'][0]['message_id'],'guest')

    def test_unused_guest_setting_is_not_an_observed_intervention(self):
        e=run()['experiment'];self.assertEqual(e['external'],'None recorded');self.assertEqual(e['external_models'],[])
        self.assertFalse(matches(e,clean_filters({'role':'interventions','weights':['Open weights'],'property_match':'every'})))

    def test_real_trio_counts_three_without_conflating_models(self):
        e=run((GEMMA,HAIKU,GEMMA),external=True)['experiment']
        self.assertEqual(e['participants'],'3');self.assertEqual(e['composition'],'Mixed models');self.assertEqual(len(e['models']),2)

    def test_prompt_disclosure_is_separate_from_actual_pairing_and_dialogue_claims(self):
        r=run((GEMMA,GEMMA));self.assertEqual(r['experiment']['identity'],'Anonymous-Full')
        r['prompt']=ANONYMOUS+' Each participant is an AI model.'
        self.assertEqual(experiment(r)['identity'],'Anonymous-AI')
        r['prompt']='You are in conversation with another instance of the same AI model.'
        self.assertEqual(experiment(r)['identity'],'Mirror')
        r['prompt']=None;self.assertEqual(experiment(r)['identity'],'Unknown')
        self.assertEqual(experiment(r)['human'],'Unknown')
        r['prompt']='A different unrecognized prompt about AI.';self.assertEqual(experiment(r)['identity'],'Unknown')

    def test_absence_of_explicit_history_does_not_turn_completion_into_full_history(self):
        r=run();r['segments']=[{'history':'raw-completion'}]
        self.assertEqual(experiment(r)['history'],'Unknown')
        r['segments']=[{'history':'F'},{'history':'R'}]
        self.assertEqual(experiment(r)['history'],'Varied by branch')

    def test_unknown_model_metadata_is_not_guessed_from_free_suffix(self):
        self.assertEqual(model_info('google/new-model:free')['weights'],'Unknown')
        self.assertEqual(model_info('madeup/gemma')['developer'],'Unknown')
        self.assertEqual(model_info(GEMMA)['developer'],'Google')
        self.assertNotEqual(model_info(GEMMA)['label'],model_info('gemma4:e4b')['label'])

    def test_filters_any_all_and_every_have_distinct_semantics(self):
        e=run()['experiment']
        self.assertTrue(matches(e,clean_filters({'models':[GEMMA,HAIKU],'model_match':'all'})))
        self.assertFalse(matches(e,clean_filters({'models':[GEMMA,QWEN],'model_match':'all'})))
        self.assertTrue(matches(e,clean_filters({'models':[GEMMA,QWEN],'model_match':'any'})))
        self.assertTrue(matches(e,clean_filters({'weights':['Open weights']})))
        self.assertFalse(matches(e,clean_filters({'weights':['Open weights'],'property_match':'every'})))
        self.assertTrue(matches(e,clean_filters({'weights':['Open weights','Closed weights'],'property_match':'every'})))
        self.assertFalse(matches(e,clean_filters({'models':[GEMMA],'identity':['Mirror']})))

    def test_counts_apply_every_and_other_groups_and_keep_zero_selections(self):
        mixed=run();same=run((GEMMA,GEMMA));same['id']='same'
        synthetic=run();synthetic.update(id='synthetic',kind='synthetic')
        pending=run();pending.update(id='pending',unstarted_assessment=True)
        catalog=SimpleNamespace(runs={r['id']:r for r in [mixed,same,synthetic,pending]},public=lambda r:r)
        before=copy.deepcopy(catalog.runs)
        result=finder_result(catalog,{'weights':['Open weights'],'property_match':'every'},None)
        self.assertEqual(result['total'],1);self.assertEqual(result['facets']['weights']['Open weights'],1)
        result=finder_result(catalog,{'models':['missing']},None)
        self.assertEqual(result['total'],0);self.assertEqual(result['facets']['models']['missing'],0)
        self.assertEqual(catalog.runs,before)

    def test_cohort_search_and_pagination_remain_in_selection(self):
        rows={str(i):dict(run(),id=str(i),title=str(i)) for i in range(50)}
        catalog=SimpleNamespace(runs=rows,public=lambda r:r)
        studies=SimpleNamespace(get=lambda id:{'runs':[{'run_id':str(i)} for i in range(45)]})
        result=finder_result(catalog,{'cohort':'saved','q':'some'},studies,40)
        self.assertEqual(result['total'],45);self.assertEqual(len(result['runs']),5)
        self.assertEqual(finder_result(catalog,{'q':'absent'},studies)['total'],0)

    def test_saved_view_revisions_are_isolated_and_conflicts_preserve_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes=Notes(Path(tmp)/'notes.sqlite');views=FinderViews(notes)
            original=views.save({'name':'Mixed participants','author':'Codex','filters':{'models':[GEMMA,HAIKU],'model_match':'all'}})
            revised=views.save(dict(original,name='Gemma + Haiku',edited_by='Local researcher'))
            self.assertEqual(revised['author'],'Codex');self.assertEqual(revised['revision'],2)
            with self.assertRaisesRegex(ValueError,'reload'):views.save(original)
            with self.assertRaisesRegex(ValueError,'authorship'):views.save(dict(revised,author='Local researcher'))
            self.assertEqual(len(views.export()['history']),2);self.assertEqual(notes.all(),[])
            self.assertEqual(FinderViews(notes).all()[0]['filters']['models'],sorted([GEMMA,HAIKU]))

    def test_filter_validation_rejects_malformed_values(self):
        for data in ({'models':GEMMA},{'role':'other'},{'property_match':'all'},{'not_a_filter':[]},{'q':[]},[]):
            with self.subTest(data=data),self.assertRaises(ValueError):clean_filters(data)

    def test_http_views_require_local_origin_and_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda a,h:SimpleNamespace(server_port=8765,handler=h)):
                server=make_server(tmp)
            def call(method,path,data=None,headers=None):
                h=server.handler.__new__(server.handler);h.server=server;h.path=path
                body=json.dumps(data).encode() if data is not None else b''
                h.headers={'Host':'127.0.0.1:8765','Content-Type':'application/json','Content-Length':str(len(body)),**(headers or {})}
                h.rfile=io.BytesIO(body);out=[];h.send=lambda d,status=200,**kw:out.append((status,d))
                getattr(h,'do_'+method)();return out[0]
            boot=call('GET','/api/bootstrap')[1];body={'name':'Test view','filters':{}}
            self.assertEqual(call('POST','/api/finder/views',body)[0],403)
            headers={'Origin':'http://127.0.0.1:8765','X-Explorer-Token':boot['token']}
            self.assertEqual(call('POST','/api/finder/views',body,headers)[0],200)
            self.assertEqual(call('GET','/api/finder')[1]['total'],0)
            self.assertEqual(len(call('GET','/api/finder/export')[1]['history']),1)
            self.assertEqual(call('GET','/api/finder?filters=not-json')[0],400)



class FinderTopicTests(unittest.TestCase):
    def setUp(self):
        from behaviorlab.topic_atlas import TopicAtlas
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.notes=Notes(Path(self.tmp.name)/'notes.sqlite');self.atlas=TopicAtlas(self.notes)
        def topic_run(identity,turns,models=(GEMMA,HAIKU),length=7):
            r=run(models,external=True);r.update(id=identity,title=identity,models=list(models),source={'sha256':identity+'source'},leaves=['main'])
            r['messages']=[dict(id=identity+':'+str(i),turn=i,speaker='X' if i%2 else 'Y',kind='message',
                model=models[(i-1)%2],status='valid',text='Consciousness and consciousness.' if i in turns else 'A different subject.') for i in range(1,length+1)]
            r['messages'].append(dict(id='observer',turn=1,speaker='Observer',kind='third',model='gemma4:e4b',status='valid',text='Consciousness.'))
            r['prompt']='Consciousness.';r['experiment']=experiment(r)
            return r
        self.runs={i:topic_run(i,t,m,length) for i,t,m,length in [
            ('early',[1],(GEMMA,HAIKU),7),('late',[7],(GEMMA,GEMMA),7),
            ('repeat',[1,7],(QWEN,QWEN),7),('paraphrase',[],(GEMMA,HAIKU),7),
            ('short',[1],(GEMMA,HAIKU),1),('observer_only',[],(GEMMA,HAIKU),7)]}
        self.catalog=SimpleNamespace(runs=self.runs,public=lambda r:dict(r),indexed_at='now')
        self.studies=SimpleNamespace(all=lambda:[],get=lambda id:{'runs':[{'run_id':'early'},{'run_id':'late'}]})
        r=self.runs['paraphrase']
        def span(i):
            m=r['messages'][i-1];return dict(message_id=m['id'],start=0,end=len(m['text']),quote=m['text'])
        self.atlas.save_review(dict(run_id=r['id'],status='selected',choice=dict(topic_id='consciousness',proposal=span(1),uptake=span(2)),author='Codex'),self.catalog)

    def result(self,filters):
        return finder_result(self.catalog,filters,self.studies,topic_atlas=self.atlas)

    def test_all_four_modes_match_atlas_counts_and_link_correct_evidence(self):
        before=copy.deepcopy(self.runs)
        for mode,ids,column in [('any',{'early','late','repeat'},'run_hits'),('early',{'early','repeat'},'opening_run_hits'),('repeated',{'repeat'},'repeated_run_hits'),('initial',{'paraphrase'},'initial_choices')]:
            result=self.result({'topics':['consciousness'],'topic_mode':mode})
            atlas=self.atlas.analyze(self.catalog,self.studies,topic='consciousness')
            self.assertEqual({r['id'] for r in result['runs']},ids)
            self.assertEqual(result['total'],next(row[column] for row in atlas['rows'] if row['id']=='consciousness'))
            for r in result['runs']:
                ev=r['topic_matches'][0]
                self.assertIn(ev['message_id'],{m['id'] for m in r['messages']})
        self.assertEqual(self.result({'topics':['consciousness'],'topic_mode':'initial'})['runs'][0]['topic_matches'][0]['author'],'Codex')
        self.assertEqual(self.runs,before)

    def test_topic_facets_combine_with_models_cohort_search_and_keep_zero_choices(self):
        result=self.result({'topics':['consciousness'],'models':[HAIKU]})
        self.assertEqual(result['total'],1)
        self.assertEqual(result['facets']['topics']['consciousness'],1)
        self.assertEqual(result['facets']['models'][GEMMA],2)
        self.assertEqual(result['facets']['models'][QWEN],1)
        self.assertEqual(self.result({'topics':['consciousness'],'cohort':'saved'})['total'],2)
        self.assertEqual(self.result({'topics':['consciousness'],'q':'absent'})['total'],0)
        result=self.result({'topics':['consciousness','missing_topic']})
        self.assertEqual(result['total'],3);self.assertEqual(result['facets']['topics']['missing_topic'],0)
        self.assertEqual(self.result({'topics':['missing_topic']})['total'],0)
        # An external-model selection does not limit topics to the guest's text.
        self.assertEqual(self.result({'topics':['consciousness'],'role':'interventions','models':['gemma4:e4b']})['total'],3)

    def test_dictionary_and_source_updates_refresh_counts_and_exclude_stale_reviews(self):
        self.assertEqual(self.result({'topics':['consciousness']})['total'],3)
        entry=next(d for d in self.atlas.dictionary() if d['id']=='consciousness')
        self.atlas.save_entry(dict(entry,variants=['a different subject']))
        self.assertEqual(self.result({'topics':['consciousness']})['total'],5)
        self.assertEqual(self.result({'topics':['consciousness'],'topic_mode':'initial'})['total'],0)
        self.runs['early']['source']['sha256']='changed'
        for m in self.runs['early']['messages']:m['text']='No match.'
        self.assertEqual(self.result({'topics':['consciousness']})['total'],4)

    def test_topic_settings_survive_saved_view_revision_and_validation(self):
        views=FinderViews(self.notes)
        v=views.save({'name':'Consciousness openings','filters':{'topics':['consciousness'],'topic_mode':'initial','models':[HAIKU]}})
        reloaded=FinderViews(self.notes).all()[0]
        self.assertEqual(reloaded['filters']['topics'],['consciousness'])
        self.assertEqual(reloaded['filters']['topic_mode'],'initial')
        self.assertEqual(len(views.export()['history']),1)
        self.assertEqual(self.result(reloaded['filters'])['total'],1)
        for bad in [{'topics':'consciousness'},{'topic_mode':'semantic'},{'topics':[42]}]:
            with self.assertRaises(ValueError):clean_filters(bad)


if __name__=='__main__':unittest.main()
