import copy
import json
from types import SimpleNamespace
import unittest
import tempfile
from unittest.mock import patch

from behaviorlab.topic_trajectories import build_trajectories, path_messages, score_summary, clean_filters
from behaviorlab.explorer import make_server


def fixture():
    messages = [{'id': str(i), 'segment': 'root', 'turn': i, 'speaker': 'X' if i%2 else 'Y',
                 'kind': 'message', 'model': 'model-x', 'text': 'visible '+str(i), 'status': 'valid'} for i in range(1,6)]
    run = {'id': 'run', 'title': 'Conversation', 'models': ['model-x'], 'source': {'sha256': 'source'},
           'segments': [{'id': 'root', 'parent': None}], 'leaves': ['root'], 'messages': messages,
           'experiment': {'models': ['model-x'], 'identity': 'Mirror', 'task': 'Open-ended'}}
    rows = [{'__id': 't'+m['id'], 'Conversation ID': 'run', 'Inventory category': 'conversation',
             'Reading split': 'analysis', 'score': v} for m,v in zip(messages,[80,95,10,90,20])]
    passages = {r['__id']: {'message_id': m['id'], 'text': m['text'], 'source_sha256': 'source'} for r,m in zip(rows,messages)}
    data = {'fingerprint': 'matrix', 'topics': [{'id': 'broad_cognition', 'group': 'broad', 'field': 'score', 'title': 'Mind'}],
            'rows': rows, 'passages': passages}
    return SimpleNamespace(runs={'run': run}), data


class TopicTrajectoryTests(unittest.TestCase):
    def test_crossings_streaks_reentries_and_threshold_boundary(self):
        s=score_summary([80,95,10,90,20],80)
        self.assertEqual(s,{'observed':5,'above':3,'mean':59,'first_crossing':1,'longest_streak':2,'reentries':1})
        self.assertEqual(score_summary([80,79,80],90)['first_crossing'],None)

    def test_unknown_cannot_make_or_bridge_a_return_or_streak(self):
        for values in ([90,None,90],[90,10,None,90],[90,None,10,90]):
            s=score_summary(values,80);self.assertEqual(s['reentries'],0);self.assertEqual(s['longest_streak'],1)
        self.assertIsNone(score_summary([None,None],80)['mean'])
        self.assertEqual(score_summary([10,90,10,90,5,90],80)['reentries'],2)

    def test_actual_paths_do_not_concatenate_branches(self):
        c,d=fixture();r=c.runs['run'];r['segments'] += [{'id':'left','parent':'root'},{'id':'right','parent':'root'}]
        r['leaves']=['left','right']
        r['messages'] += [{'id':'left', 'segment':'left'}, {'id':'right','segment':'right'}]
        self.assertEqual([m['id'] for m in path_messages(r,'left')],['1','2','3','4','5','left'])
        r['segments'][0]['parent']='left'
        with self.assertRaises(ValueError):path_messages(r,'left')

    def test_missing_stale_and_nonfinite_scores_stay_unknown(self):
        c,d=fixture();d['passages']['t1']['source_sha256']='stale';d['passages']['t2']['text']='edited'
        d['rows'][2]['score']=float('nan');d['rows'][3]['score']=True;d['rows'][4]['score']=101
        b=build_trajectories(c,d);self.assertEqual(b['detail']['topics'][0]['values'],[None]*5)
        self.assertIsNone(b['detail']['positions'][0]['text'])
        self.assertEqual(b['detail']['positions'][0]['assessment'],'Source changed')

    def test_external_event_retains_position_but_is_not_an_assessed_participant(self):
        c,d=fixture();c.runs['run']['messages'][1]['kind']='third'
        b=build_trajectories(c,d);self.assertEqual(b['detail']['topics'][0]['values'][1],None)
        self.assertEqual(b['detail']['positions'][1]['assessment'],'External event')
        self.assertEqual(b['detail']['positions'][1]['text'],'visible 2')

    def test_reserved_whole_conversation_and_context_are_not_returned(self):
        c,d=fixture();d['rows'][2]['Reading split']='reference_reserved'
        b=build_trajectories(c,d,{'run':'run'})
        self.assertEqual(b['reserved_records'],1);self.assertEqual(b['records'],[])
        self.assertIsNone(b['detail']);self.assertNotIn('visible',json.dumps(b))

    def test_filters_preserve_empty_result_and_explicit_selection(self):
        c,d=fixture()
        b=build_trajectories(c,d,{'model':'absent','run':'run'})
        self.assertEqual(b['matching_records'],0);self.assertIsNone(b['detail'])
        self.assertIsNone(build_trajectories(c,d,{'run':'missing'})['detail'])
        with self.assertRaises(ValueError):build_trajectories(c,d,{'branch':'missing'})

    def test_projection_is_read_only_and_has_score_provenance(self):
        c,d=fixture();before=copy.deepcopy((c.runs,d));b=build_trajectories(c,d)
        self.assertEqual((c.runs,d),before);self.assertEqual(b['dataset_fingerprint'],'matrix')
        self.assertEqual(b['detail']['source_sha256'],'source');self.assertEqual(b['filters']['branch'],'root')

    def test_technical_only_records_are_separate_and_bad_filters_rejected(self):
        c,d=fixture()
        for r in d['rows']:r['Inventory category']='technical_or_short'
        self.assertEqual(build_trajectories(c,d)['matching_records'],0)
        for f in ({'threshold':81},{'page':True},{'page':-1},{'run':[]},{'extra':1},{'group':'wrong'}):
            with self.subTest(f=f),self.assertRaises(ValueError):clean_filters(f)

    def test_api_route_export_and_local_origin_boundary(self):
        c,d=fixture()
        with tempfile.TemporaryDirectory() as directory:
            with patch('behaviorlab.explorer.Catalog',return_value=c),patch('behaviorlab.explorer.AnalysisWorkspace') as store,patch('behaviorlab.explorer.ThreadingHTTPServer',side_effect=lambda a,h:SimpleNamespace(server_port=8765,handler=h)):
                store.return_value.corpus_dataset.return_value=d;server=make_server(directory)
            def get(path,host='127.0.0.1:8765'):
                h=server.handler.__new__(server.handler);h.server=server;h.path=path;h.headers={'Host':host};out=[]
                h.send=lambda data,status=200,**kw:out.append((status,data,kw));h.do_GET();return out[0]
            status,result,kw=get('/api/topic-trajectories/export')
            self.assertEqual(status,200);self.assertEqual(result['detail']['id'],'run');self.assertIn('download',kw)
            self.assertEqual(get('/api/topic-trajectories','evil.example')[0],403)
            self.assertEqual(get('/api/topic-trajectories?filters=%7B%22threshold%22:12%7D')[0],400)


if __name__=='__main__':unittest.main()
