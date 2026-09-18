import copy
import unittest

from behaviorlab.population import catalog_population


class PopulationTests(unittest.TestCase):
    def test_inventory_separates_records_messages_controls_and_unstarted_slots(self):
        runs = [{'kind':'reference','message_count':3},
                {'kind':'lab','message_count':0},
                {'kind':'synthetic','message_count':12},
                {'kind':'lab','message_count':0,'unstarted_assessment':True}]
        before = copy.deepcopy(runs)
        result = catalog_population(iter(runs), 'indexed')
        self.assertEqual((result['records'],result['recorded_messages']), (2,3))
        self.assertEqual((result['synthetic_records'],result['synthetic_messages']), (1,12))
        self.assertEqual(result['unstarted_records'], 1)
        self.assertEqual(result['by_kind']['lab'], {'records':1,'recorded_messages':0})
        self.assertEqual(result['indexed_at'], 'indexed')
        self.assertEqual(runs,before)

    def test_empty_inventory_has_true_zero_counts(self):
        result = catalog_population([])
        self.assertEqual(result['records'], 0)
        self.assertEqual(result['recorded_messages'], 0)
        self.assertEqual(result['synthetic_records'], 0)

    def test_unknown_message_count_does_not_become_zero_or_drop_the_record(self):
        result = catalog_population([{'kind':'reference','message_count':3}, {'kind':'lab'}])
        self.assertEqual(result['records'], 2)
        self.assertIsNone(result['recorded_messages'])
        self.assertEqual(result['by_kind']['reference']['recorded_messages'], 3)
        self.assertIsNone(result['by_kind']['lab']['recorded_messages'])
