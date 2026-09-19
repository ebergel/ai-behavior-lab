from test_discourse_corpus import DiscourseCorpusTests
from behaviorlab import discourse_recovery_v2 as recovery
from behaviorlab.discourse_corpus import run, replay, RESERVE
from behaviorlab.jev_atlas import read_record
from unittest.mock import patch

class RecoveryTests(DiscourseCorpusTests):
    def stopped(self):
        self.freeze(max_workers=1)
        def fail(p,k):raise TimeoutError('synthetic transport timeout')
        run(self.ws,self.dest,send=fail)
        return recovery.prepare_recovery(self.ws,self.dest)

    def test_recovery_preserves_unknown_and_never_repeats(self):
        prep=self.stopped();self.assertEqual(prep['remaining'],3)
        old={str(p):p.read_bytes() for p in self.dest.glob('attempts/*/*.json')}
        with patch('behaviorlab.discourse_recovery_v2.transport',side_effect=self.good) as send, patch('behaviorlab.discourse_recovery_v2.credential',return_value='secret'):
            out=recovery.run(self.ws,self.dest)
            self.assertEqual(out['state'],'complete_with_unknowns');self.assertEqual(send.call_count,3)
            recovery.run(self.ws,self.dest);self.assertEqual(send.call_count,3)
        self.assertEqual(out['completed_assessments'],3)
        self.assertEqual(out['unknown_cost_reserved_usd'],RESERVE/1e9)
        for p,b in old.items():
            from pathlib import Path
            self.assertEqual(Path(p).read_bytes(),b)

    def test_new_unknown_stops_and_cannot_resume(self):
        self.stopped()
        def fail(p,k):raise TimeoutError()
        out=recovery.run(self.ws,self.dest,send=fail)
        self.assertEqual(out['state'],'stopped')
        with patch('behaviorlab.discourse_recovery_v2.transport',side_effect=AssertionError('No retry')) as send:
            out=recovery.run(self.ws,self.dest)
            self.assertEqual(out['state'],'stopped');send.assert_not_called()

    def test_changed_baseline_rejected(self):
        self.stopped();release=read_record(self.dest/'release.json')
        _,_,_,ledger,fatal=replay(self.ws,self.dest)
        record=read_record(self.dest/recovery.RECOVERY)
        ledger[0]['charge_nanodollars']=0
        with self.assertRaises(ValueError):recovery.validate_recovery(record,release,ledger,fatal)

    def test_shared_budget_includes_original_unknown(self):
        self.freeze(max_workers=1,ceiling=RESERVE/1e9*1.5)
        def fail(p,k):raise TimeoutError()
        run(self.ws,self.dest,send=fail);recovery.prepare_recovery(self.ws,self.dest)
        with patch('behaviorlab.discourse_recovery_v2.transport',side_effect=AssertionError('No funds')) as send, patch('behaviorlab.discourse_recovery_v2.credential',return_value='secret'):
            out=recovery.run(self.ws,self.dest)
            self.assertEqual(out['reason'],'Spending ceiling reached');send.assert_not_called()
