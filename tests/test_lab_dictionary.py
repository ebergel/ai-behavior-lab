import hashlib
import json
from pathlib import Path
import unittest

from behaviorlab.lab_dictionary import dictionary_catalog


class DictionaryTests(unittest.TestCase):
    def test_exact_scoring_rubric_is_the_definition_source(self):
        raw = Path('behaviorlab/gem_rubric.json').read_bytes()
        rubric = json.loads(raw)
        data = dictionary_catalog()
        entries = {e['id']: e for e in data['entries']}
        self.assertEqual(data['rubric']['file_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(data['rubric']['version'], rubric['version'])
        for axis in rubric['axes']:
            entry = entries[axis['id']]
            self.assertEqual(entry['rubric'], axis)
            self.assertEqual(entry['scope'], rubric['scope'])
            self.assertIn('25 × returned Score', entry['formula'])

    def test_guide_is_complete_and_cross_references_resolve(self):
        data = dictionary_catalog()
        ids = {e['id'] for e in data['entries']}
        categories = {c['id'] for c in data['categories']}
        self.assertEqual(len(ids), len(data['entries']))
        self.assertEqual({e['id'] for e in data['entries'] if e['category'] == 'measures'},
                         {'surprise', 'contribution', 'connection', 'expression', 'complexity', 'substance', 'profile', 'words'})
        for entry in data['entries']:
            self.assertIn(entry['category'], categories)
            for field in ('definition', 'practical', 'method', 'limits', 'sources'):
                self.assertTrue(entry[field], (entry['id'], field))
            self.assertTrue(set(entry['related']) <= ids)
            for source in entry['sources']:
                self.assertTrue(Path(source.split(':')[0]).is_file(), source)

    def test_catalog_calls_are_independent_and_need_no_workspace(self):
        a = dictionary_catalog()
        a['entries'][0]['rubric']['criteria'][0] = 'Changed in memory'
        b = dictionary_catalog()
        self.assertNotEqual(a, b)
        self.assertNotIn('Changed in memory', json.dumps(b))
