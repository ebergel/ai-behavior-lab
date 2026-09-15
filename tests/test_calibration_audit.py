from pathlib import Path
import tempfile
import unittest

from behaviorlab.annotations import load_packet
from behaviorlab.calibration import create_calibration
from behaviorlab.calibration_audit import target_status, audit_selection, freeze_supplement, build_supplement_packet, create_eligible_panel, RULE
from behaviorlab.common import canonical, fingerprint, read_json
from behaviorlab.legacy import import_corpus


class CalibrationAuditTests(unittest.TestCase):
    def test_cap_before_window_marks_normally_terminated_descendants(self):
        rows = [(i, {'kind':'message', 'turn':i, 'content':'', 'done_reason':'length' if i==1 else 'stop'}) for i in range(1,9)]
        status = target_status(rows)
        self.assertEqual(len(status), 6)
        self.assertTrue(all(t['status']=='ancestor_invalid_or_unknown' for t in status))
        self.assertTrue(all(t['earliest_ancestor_flag']['turn']==1 for t in status))
        rows[0][1]['done_reason'] = 'stop'
        self.assertTrue(all(t['status']=='recorded_stop_chain' and t['empty_visible_text'] for t in target_status(rows)))
        rows[0][1].pop('done_reason')
        self.assertTrue(all(t['status']=='ancestor_invalid_or_unknown' for t in target_status(rows)))

    def test_supplement_is_additive_disjoint_frozen_and_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); source=base/'source'; (source/'data/runs').mkdir(parents=True)
            for i in range(1,9):
                rows=[{'kind':'header','pair_model':'fixture','cond':'A','run':i}]
                rows += [{'kind':'message','speaker':'X' if t%2 else 'Y','turn':t,'content':'café 空',
                          'done_reason':'length' if i==1 and t==1 else 'stop'} for t in range(1,9)]
                rows += [{'kind':'footer','pair_turns':8}]
                (source/'data/runs'/f'A_run{i:02}.jsonl').write_text('\n'.join(map(canonical,rows))+'\n')
            corpus=base/'corpus'; info=import_corpus(source,corpus,'fixture','fixture')
            recipe={'schema':'behaviorlab.calibration-recipe/1','dataset_sha256':info['dataset_sha256'],'seed':3,'window_size':6,
                    'strata':[{'id':'a','stage':1,'prefix':'A','heldout_runs':2}]}
            create_calibration(corpus,base/'original',recipe)
            before={str(p):p.read_bytes() for p in (base/'original').rglob('*.json')}
            selection=read_json((base/'original/selection.json').read_text())
            self.assertEqual(audit_selection(corpus,selection)['groups']['heldout']['targets'],12)
            extension={'schema':'behaviorlab.calibration-supplement-recipe/1','rule':RULE,'window_size':6,'seed':91,
                'dataset_sha256':info['dataset_sha256'],'prior_selection_sha256':fingerprint(selection),
                'strata':[{'id':'a','stage':1,'prefix':'A','runs':2}]}
            frozen=freeze_supplement(corpus,selection,extension,base/'supplement')
            raw=(base/'supplement/selection.json').read_bytes()
            summary=build_supplement_packet(corpus,base/'supplement')
            self.assertEqual(summary['targets'],12)
            packet,key=load_packet(base/'supplement')
            self.assertTrue(all(t['status']=='recorded_stop_chain' for t in key['legacy_technical_metadata'].values()))
            self.assertNotIn('data/runs',canonical(packet))
            self.assertEqual(raw,(base/'supplement/selection.json').read_bytes())
            self.assertTrue(all(p.read_bytes()==before[str(p)] for p in (base/'original').rglob('*.json')))
            self.assertNotIn('data/runs/A_run01.jsonl',[r['source_path'] for r in frozen['selected']])
            audit=audit_selection(corpus,selection)
            result=create_eligible_panel(base/'original/heldout',base/'supplement',audit,base/'panel',3)
            eligible=audit['groups']['heldout']['counts'].get('recorded_stop_chain',0)
            self.assertEqual(result['targets'],eligible+12)
            panel,panel_key=load_packet(base/'panel')
            self.assertTrue(all(t['status']=='recorded_stop_chain' for t in panel_key['legacy_technical_metadata'].values()))
            self.assertEqual(result['excluded_original_targets'],12-eligible)
            bad=dict(audit,selection_sha256='0'*64)
            with self.assertRaises(ValueError): create_eligible_panel(base/'original/heldout',base/'supplement',bad,base/'bad-panel',3)
            with self.assertRaises(FileExistsError): freeze_supplement(corpus,selection,extension,base/'supplement')


if __name__ == '__main__': unittest.main()
