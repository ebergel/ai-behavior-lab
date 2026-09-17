import copy
import math
import unittest
from scripts.replication_precision import calculate


def rows(rid,values,**kwargs):
    return [{'Conversation ID':rid,'Lineage':rid,'Inventory category':'conversation','Reading split':'analysis',
             'Model ID':'model','Task':'Open-ended','Composition':'Same model','Assessment status':'Complete',
             'Observed history':'Clean recorded path','Turn':i,'Score · Mind & cognition':v,
             'Score · Philosophy & knowledge':v,**kwargs} for i,v in enumerate(values,1)]


class ReplicationPrecisionTests(unittest.TestCase):
    def test_one_opening_mean_per_root_not_six_independent_units(self):
        data={'fingerprint':'matrix','rows':rows('a',[0,10,20,30,40,50])+rows('b',[50,60,70,80,90,100])}
        before=copy.deepcopy(data);out=calculate(data)['models'][0]['outcomes'][0]
        self.assertEqual(out['n'],2);self.assertEqual(out['mean'],50);self.assertAlmostEqual(out['sd'],math.sqrt(1250))
        self.assertEqual(data,before)

    def test_reserved_partial_flagged_and_duplicate_openings_do_not_increase_n(self):
        data={'fingerprint':'matrix','rows':rows('a',[10]*6)+rows('copy',[10]*6,Lineage='a')+
              rows('partial',[10]*5)+rows('reserved',[99]*6,**{'Reading split':'reference_reserved'})+
              rows('flagged',[99]*6,**{'Observed history':'Flagged / unavailable'})}
        out=calculate(data);self.assertEqual(out['models'][0]['outcomes'][0]['n'],1)
        self.assertIsNone(out['models'][0]['outcomes'][0]['sd']);self.assertEqual(sum(out['excluded'].values()),4)

    def test_single_interval_scenario_formula(self):
        out=calculate({'fingerprint':'empty','rows':[]})
        scenario=next(x for x in out['scenarios'] if x['sd']==25 and x['mean_half_width']==10)
        self.assertEqual(scenario['roots_per_cell_mean'],25);self.assertEqual(scenario['roots_per_cell_two_cell_difference'],49)
