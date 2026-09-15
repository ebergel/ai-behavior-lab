from pathlib import Path
import tempfile
import unittest

from behaviorlab.annotations import load_packet, validate_submission
from behaviorlab.calibration import create_calibration
from behaviorlab.common import canonical, read_json
from behaviorlab.legacy import import_corpus


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.base = Path(self.tmp.name)
        source = self.base/'reference'; (source/'data/runs').mkdir(parents=True)
        for i in range(1, 5):
            rows = [{'kind': 'header', 'pair_model': 'fixture', 'cond': 'A', 'run': i}]
            rows += [{'kind': 'message', 'speaker': 'X' if t % 2 else 'Y', 'turn': t,
                      'content': '' if t == 6 else 'café 空 '+str(i),
                      'thinking': 'NEVER IN PACKET', 'done_reason': 'length' if t == 6 else 'stop'} for t in range(1, 7)]
            rows += [{'kind': 'footer', 'pair_turns': 6}]
            (source/'data/runs'/('A_run0'+str(i)+'.jsonl')).write_text('\n'.join(map(canonical, rows))+'\n')
        self.corpus = self.base/'corpus'
        meta = import_corpus(source, self.corpus, 'fixture', 'fixture-revision')
        self.recipe = {'schema': 'behaviorlab.calibration-recipe/1', 'dataset_sha256': meta['dataset_sha256'],
            'seed': 91, 'window_size': 6, 'strata': [{'id': 'a', 'stage': 1, 'prefix': 'A', 'heldout_runs': 2}]}

    def tearDown(self): self.tmp.cleanup()

    def test_selection_is_repeatable_run_disjoint_and_preserves_empty_capped_text(self):
        for name in ('one', 'two'): create_calibration(self.corpus, self.base/name, self.recipe)
        a = read_json((self.base/'one/selection.json').read_text())
        b = read_json((self.base/'two/selection.json').read_text())
        self.assertEqual(a['groups'], b['groups'])
        paths = [r['source_path'] for rows in a['groups'].values() for r in rows]
        self.assertEqual(len(set(paths)), 3)
        for name, count in [('development', 6), ('heldout', 12)]:
            folder = self.base/'one'/name; packet, key = load_packet(folder)
            text = canonical(packet)
            self.assertNotIn('NEVER IN PACKET', text)
            self.assertNotIn('A_run', text)
            self.assertEqual(sum(len(w['messages']) for w in packet['windows']), count)
            self.assertTrue(any(m['text'] == '' for w in packet['windows'] for m in w['messages']))
            self.assertTrue(any(v['done_reason'] == 'length' for v in key['legacy_technical_metadata'].values()))
            template = read_json((folder/'ratings.template.json').read_text())
            with self.assertRaises(ValueError): validate_submission(template, packet)

    def test_wrong_corpus_and_reusing_destination_are_rejected(self):
        destination = self.base/'packet'
        create_calibration(self.corpus, destination, self.recipe)
        with self.assertRaises(ValueError): create_calibration(self.corpus, destination, self.recipe)
        self.recipe['dataset_sha256'] = '0'*64
        with self.assertRaises(ValueError): create_calibration(self.corpus, self.base/'other', self.recipe)
        self.assertFalse((self.base/'other').exists())


if __name__ == '__main__': unittest.main()
