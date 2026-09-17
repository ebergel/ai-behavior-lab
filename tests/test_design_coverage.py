import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.design_coverage import build_coverage, clean_filters, project, PLAN_PATH
from behaviorlab.explorer import make_server


def record(identity='r', models=('qwen3:30b-a3b-instruct-2507-q4_K_M',), **overrides):
    r = {'id': identity, 'title': identity, 'kind': 'lab', 'data_class': 'local_qualification',
         'models': list(models), 'complete': True, 'condition': 'baseline',
         'prompt': 'Each participant is an AI model. open-ended', 'collection_id': 'fixture',
         'source': {'sha256': 'shared-campaign-hash', 'protocol_sha256': 'p'*64},
         'settings': {'decoding': {'temperature': .8, 'top_p': .9}},
         'segments': [{'id': 'main', 'parent': None, 'history': 'F'}], 'leaves': ['main'],
         'messages': [{'id': str(i), 'kind': 'message', 'speaker': 'X' if i%2 else 'Y',
                       'model': models[(i-1)%len(models)], 'turn': i, 'text': 'visible',
                       'parent': str(i-1) if i>1 else None, 'status': 'valid'} for i in range(1,7)]}
    r.update(overrides); return r


class DesignCoverageTests(unittest.TestCase):
    def build(self, runs, filters=None):
        return build_coverage(SimpleNamespace(runs={r['id']:r for r in runs}),filters)

    def test_same_campaign_roots_are_not_deduplicated_and_branches_are_not_replicates(self):
        a,b=record('a'),record('b')
        a['messages'].append(dict(a['messages'][-1],id='7',parent='4'))
        a['messages'].append(a['messages'][0])  # Shared node appears twice in projection.
        a['leaves']=['left','right'];a['segments']*=3
        d=self.build([a,b]);self.assertEqual(d['summary']['records'],2)
        self.assertEqual(d['summary']['visible'],13);self.assertEqual(d['summary']['branched'],1)
        self.assertEqual(d['grid'][0]['records'],2)

    def test_guest_event_cannot_create_a_participant_or_increase_message_exposure(self):
        r=record();r['messages'].append({'id':'guest','kind':'third','speaker':'X','model':'external',
                                        'turn':4,'text':'disruption','status':'intervention'})
        d=self.build([r]);self.assertEqual(d['summary']['models'],1)
        self.assertEqual(d['summary']['visible'],6)
        self.assertEqual(d['records'][0]['dimensions']['external'],'Recorded intervention')

    def test_no_output_unavailable_slots_and_flags_remain_in_inventory(self):
        r=record('none')
        for m in r['messages']:m.update(text=None,status='blocked')
        d=self.build([r]);self.assertEqual(d['summary']['records'],1)
        self.assertEqual(d['summary']['no_visible'],1);self.assertEqual(d['summary']['unavailable'],6)
        self.assertEqual(d['summary']['flagged'],1)
        self.assertEqual(self.build([r],{'scope':'atlas'})['summary']['records'],0)

    def test_mixed_record_membership_and_actual_speaker_exposure(self):
        r=record(models=('anthropic/claude-haiku-4.5','gemma4:26b'))
        d=self.build([r]);self.assertEqual(d['summary']['records'],1)
        self.assertEqual(sum(g['records'] for g in d['grid']),2)
        self.assertEqual(sum(g['visible'] for g in d['grid']),6)
        self.assertEqual([g['visible'] for g in d['grid']],[3,3])
        self.assertEqual(self.build([r],{'group':'family'})['summary']['families'],2)

    def test_presence_matches_corpus_even_for_whitespace_only_reply(self):
        r=record();r['messages'][0]['text']='  '
        d=self.build([r],{'scope':'atlas'})
        self.assertEqual(d['summary']['visible'],6);self.assertEqual(d['summary']['whitespace'],1)

    def test_nested_decoding_and_speaker_overrides_preserve_unknowns(self):
        r=record();self.assertEqual(project(r)['dimensions']['temperature'],'0.8')
        self.assertEqual(project(r)['requested_top_p'],'0.9')
        r['settings_by_speaker']={'Y':{'temperature':1.0}}
        self.assertEqual(project(r)['dimensions']['temperature'],'Mixed: 0.8 / 1.0')
        r['settings_by_speaker']['Y']['temperature']=None
        self.assertEqual(project(r)['dimensions']['temperature'],'Unknown')

    def test_scope_separation_and_technical_failure_is_not_a_behavioural_negative(self):
        cases=[record(),record('synthetic',kind='synthetic'),record('unstarted',unstarted_assessment=True),
               record('technical',data_class='cloud_model_assessment')]
        d=self.build(cases);self.assertEqual(d['summary']['records'],1)
        self.assertEqual(d['omitted_synthetic'],1)
        self.assertEqual(d['scope_counts']['unstarted'],1);self.assertEqual(d['scope_counts']['technical'],1)
        self.assertEqual(self.build(cases,{'scope':'technical'})['records'][0]['id'],'technical')

    def test_zero_cells_selection_unknown_settings_and_pagination(self):
        rs=[record(str(i)) for i in range(23)]
        rs[0]['settings']={}
        d=self.build(rs,{'page':999});self.assertEqual(d['filters']['page'],1)
        self.assertEqual(len(d['records']),3)
        d=self.build(rs,{'column':'Mirror'});self.assertEqual(d['selection']['records'],0)
        self.assertTrue(all(next(c for c in g['cells'] if c['value']=='Mirror')['records']==0 for g in d['grid']))
        d=self.build(rs,{'axis':'temperature'});self.assertIn('Unknown',d['columns'])

    def test_projection_does_not_mutate_or_export_transcript_text(self):
        rs=[record()];before=copy.deepcopy(rs);d=self.build(rs)
        self.assertEqual(rs,before)
        self.assertNotIn('"text":',json.dumps(d));self.assertNotIn('"thinking":',json.dumps(d))
        self.assertEqual(self.build(rs)['inventory_sha256'],d['inventory_sha256'])

    def test_protocol_prefix_collision_does_not_merge_distinct_designs(self):
        a,b=record('a'),record('b')
        a['source']['protocol_sha256']='a'*12+'1'*52
        b['source']['protocol_sha256']='a'*12+'2'*52
        d=self.build([a,b],{'axis':'block'})
        self.assertEqual(len(d['columns']),2)
        self.assertEqual([c['records'] for c in d['grid'][0]['cells']],[1,1])

    def test_invalid_filters_rejected_and_draft_arithmetic_is_consistent(self):
        for f in ({'axis':'hacked'},{'page':-1},{'page':True},{'scope':[]},{'extra':1}):
            with self.subTest(f=f),self.assertRaises(ValueError):clean_filters(f)
        p=json.loads(PLAN_PATH.read_text());n=len(p['models'])*len(p['disclosures'])*p['factors']['fresh_roots_per_cell']
        self.assertEqual(n,p['allocation']['fresh_conversations'])
        self.assertEqual(n*p['allocation']['scheduled_messages_per_root'],p['allocation']['main_generation_slots'])
        self.assertFalse(p['execution_enabled']);self.assertIsNone(p['spending_ceiling_usd'])

    def test_api_export_and_host_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog=SimpleNamespace(runs={'r':record()})
            with patch('behaviorlab.explorer.Catalog',return_value=catalog),patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda a,h:SimpleNamespace(server_port=8765,handler=h)):
                server=make_server(directory)
            def get(path,host='127.0.0.1:8765'):
                h=server.handler.__new__(server.handler);h.server=server;h.path=path;h.headers={'Host':host};out=[]
                h.send=lambda d,status=200,**kw:out.append((status,d,kw));h.do_GET();return out[0]
            status,d,kw=get('/api/design-coverage/export');self.assertEqual(status,200)
            self.assertEqual(d['summary']['records'],1);self.assertIn('download',kw)
            self.assertEqual(get('/api/design-coverage','evil.example')[0],403)
            self.assertEqual(get('/api/design-coverage?filters=%7B%22axis%22:%22missing%22%7D')[0],400)


if __name__=='__main__':unittest.main()
