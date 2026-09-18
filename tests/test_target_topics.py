import copy
import unittest
from unittest.mock import patch

from behaviorlab.target_topics import attach_target_topics


class TargetTopicTests(unittest.TestCase):
    def setUp(self):
        self.sample = {'id':'s', 'kind':'transcript', 'run_id':'r', 'message_id':'m',
                       'source_sha256':'hash', 'text':'exact target', 'source_current':True}
        self.dataset = {'fingerprint':'matrix', 'topics':[
            {'id':'consciousness', 'field':'Score · Consciousness', 'title':'Consciousness', 'group':'focused'},
            {'id':'zero', 'field':'Score · Zero', 'title':'Zero', 'group':'broad'}],
            'rows':[{'__id':'target', 'Score · Consciousness':80, 'Score · Zero':0}],
            'passages':{'target':{'run_id':'r', 'message_id':'m', 'text':'exact target',
                                  'source_sha256':'hash', 'source_current':True}}}

    def test_exact_join_preserves_raw_zero_and_evidence_without_network(self):
        originals=copy.deepcopy((self.sample,self.dataset))
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('No inference')):
            samples,meta=attach_target_topics([self.sample],self.dataset)
        self.assertEqual(samples[0]['topic_scores'],{'consciousness':80,'zero':0})
        self.assertEqual(samples[0]['topic_status'],'matched')
        self.assertEqual(meta['dataset_fingerprint'],'matrix')
        self.assertTrue(meta['available'])
        self.assertEqual((self.sample,self.dataset),originals)

    def test_neighbouring_changed_unverified_or_reserved_sources_never_match(self):
        cases=[dict(self.sample,message_id='other'), dict(self.sample,source_sha256='changed'),
               dict(self.sample,text='different text'),dict(self.sample,source_current=False),
               dict(self.sample,source_current=None),dict(self.sample,kind='synthetic')]
        for sample in cases:
            with self.subTest(sample=sample):
                joined,_=attach_target_topics([sample],self.dataset)
                self.assertEqual(joined[0]['topic_scores'],{})
        for mutation in ('stale','reserved','duplicate'):
            data=copy.deepcopy(self.dataset)
            if mutation=='stale':data['passages']['target']['source_current']=False
            if mutation=='reserved':data['rows'][0]['Reading split']='reference_reserved'
            if mutation=='duplicate':data['rows'].append(dict(data['rows'][0]))
            joined,_=attach_target_topics([self.sample],data)
            self.assertEqual(joined[0]['topic_scores'],{})

    def test_missing_invalid_scores_remain_unknown(self):
        for value in (None, True, float('nan'), float('inf'), -1, 101, '80'):
            data=copy.deepcopy(self.dataset);data['rows'][0]['Score · Consciousness']=value
            joined,_=attach_target_topics([self.sample],data)
            self.assertNotIn('consciousness',joined[0]['topic_scores'])
            self.assertEqual(joined[0]['topic_scores']['zero'],0)
        joined,meta=attach_target_topics([self.sample])
        self.assertFalse(meta['available']);self.assertEqual(joined[0]['topic_scores'],{})
