import copy
from pathlib import Path
import unittest

from behaviorlab.common import read_json
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.seeds import audit, protocol_entries, require_clean

ROOT = Path(__file__).resolve().parents[1]


class SeedTests(unittest.TestCase):
    def test_detects_actual_reference_common_overlap_across_profiles(self):
        entries = []
        for name, p, r in [('reference', 'qwen-reference', 'qwen-reference'),
                            ('common', 'common-prompt', 'ollama-context')]:
            registry = Registry.load(ROOT/('design/'+r+'-models.json'))
            protocol = Protocol.load(ROOT/('design/'+p+'.qualification.json'), registry)
            entries += protocol_entries(name, protocol, registry)
        result = audit(entries)
        self.assertEqual(result['unexpected_collisions'], 30)
        with self.assertRaisesRegex(ValueError, 'Unplanned'): require_clean(entries)

    def test_explicit_branch_pairing_and_historical_overlap_are_separate(self):
        registry = Registry.load(ROOT/'design/models.json')
        protocol = Protocol.load(ROOT/'examples/history-factorial.fake.json', registry)
        plain = protocol_entries('pilot', protocol, registry)
        self.assertGreater(audit(plain)['unexpected_collisions'], 0)
        paired = protocol_entries('pilot', protocol, registry, paired_branches=True)
        self.assertEqual(require_clean(paired)['unexpected_collisions'], 0)
        with self.assertRaisesRegex(ValueError, 'historical'): require_clean(paired, [plain[0]])

    def test_renamed_model_labels_cannot_hide_reuse(self):
        r = Registry.load(ROOT/'design/models.json')
        p = Protocol.load(ROOT/'examples/history-factorial.fake.json', r)
        entries = protocol_entries('one', p, r)[:1]
        other = copy.deepcopy(entries[0]); other['id'] = 'two/renamed-node'
        self.assertEqual(audit(entries+[other])['unexpected_collisions'], 1)
        other['model'] = 'different-digest'
        self.assertEqual(require_clean(entries+[other])['unexpected_collisions'], 0)
        other['seed'] = True
        with self.assertRaises(ValueError): audit([other])


if __name__ == '__main__': unittest.main()
