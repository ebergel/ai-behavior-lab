import json
import unittest
from unittest.mock import patch

import test_jev_corpus as fixtures
from test_jev_atlas import reply
from behaviorlab.jev_atlas import read_record, write_record
from behaviorlab.jev_corpus import run_qualification
from behaviorlab.jev_recovery import prepare, run, checked


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        fixtures.CorpusTests.setUp(self)
        fixtures.CorpusTests.prepare(self)
        with patch('behaviorlab.jev_runner.credential', return_value='test'), patch('behaviorlab.jev_runner.transport', side_effect=reply):
            run_qualification(self.ws, self.dest, 1)
        with patch('behaviorlab.jev_runner.credential', return_value='test'), patch('behaviorlab.jev_runner.transport', return_value=(529, 'overload')):
            run_qualification(self.ws, self.dest, 1)
        self.recovery = self.ws / 'recovery'

    def test_exact_inputs_reuse_and_resume_without_duplicates(self):
        release = prepare(self.ws, self.dest, self.recovery, 'Please retry')
        self.assertEqual(len(release['reused']), 1)
        _, protocol, plans, _ = checked(self.ws, self.recovery)
        old = read_record(self.dest / 'qualification.json')
        originals = {a['variant']: self.store.plan(a['batch']) for a in old['allocations']}
        for variant, plan in plans.items():
            original = originals[variant]
            for item in plan['items']:
                before = next(i for i in original['items'] if i['id'] == item['id'])
                self.assertEqual(self.store.payload(plan, item), self.store.payload(original, before))
        with patch('behaviorlab.jev_runner.credential', return_value='test'), patch('behaviorlab.jev_runner.transport', side_effect=reply) as send:
            pause = unittest.mock.Mock()
            run(self.ws, self.recovery, 1, pause=pause)
            result = run(self.ws, self.recovery, pause=pause)
            run(self.ws, self.recovery, pause=pause)
            self.assertEqual(send.call_count, protocol['max_calls'])
            self.assertEqual(pause.call_count, protocol['max_calls'])
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['effective_complete_assessments'], old['max_calls'])
        self.assertEqual(result['cumulative_calls_started'], old['max_calls'] + 1)
        self.assertEqual(result['prior_unknown_cost_calls'], 1)
        self.assertGreater(result['prior_unknown_reserved_usd'], 0)
        checked(self.ws, self.recovery)  # Original immutable request/response receipts still match.

    def test_second_overload_stops_everything_and_cannot_be_retried(self):
        prepare(self.ws, self.dest, self.recovery, 'Please retry')
        with patch('behaviorlab.jev_runner.credential', return_value='test'), patch('behaviorlab.jev_runner.transport', return_value=(529, 'overload')) as send:
            result = run(self.ws, self.recovery, pause=lambda _: None)
            self.assertEqual(result['status'], 'incomplete')
            self.assertEqual(result['cumulative_calls_started'], 3)
            with self.assertRaisesRegex(ValueError, 'Recovery stopped'):
                run(self.ws, self.recovery, pause=lambda _: None)
            self.assertEqual(send.call_count, 1)

    def test_freeze_is_append_only_and_software_change_blocks_dispatch(self):
        prepare(self.ws, self.dest, self.recovery, 'Please retry')
        with self.assertRaisesRegex(ValueError, 'already frozen'):
            prepare(self.ws, self.dest, self.recovery, 'Please retry')
        with patch('behaviorlab.jev_recovery.software', return_value='changed'), patch('behaviorlab.jev_runner.execute') as send:
            with self.assertRaisesRegex(ValueError, 'software changed'):
                run(self.ws, self.recovery, pause=lambda _: None)
            send.assert_not_called()

    def test_corpus_reuses_original_success_without_a_duplicate_call(self):
        from behaviorlab.jev_recovered_corpus import freeze
        prepare(self.ws, self.dest, self.recovery, 'Please retry')
        with patch('behaviorlab.jev_runner.credential', return_value='test'), patch('behaviorlab.jev_runner.transport', side_effect=reply):
            result = run(self.ws, self.recovery, pause=lambda _: None)
        write_record(self.recovery / 'summary.json', result)
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('No corpus dispatch')):
            out = freeze(self.ws, self.catalog, self.coverage, self.recovery, self.ws / 'corpus')
        plan = read_record(self.ws / 'corpus/plan.json')
        original = read_record(self.dest / 'qualification.json')
        self.assertEqual(out['counts']['reuse_requests'], original['max_calls'])
        self.assertEqual(out['counts']['new_calls'] + original['max_calls'], 58)
        self.assertEqual(len(plan['additional_reuse_receipts']), 1)
        self.assertEqual(out['status'], 'prepared_not_dispatched')
        with self.assertRaisesRegex(ValueError, 'already frozen'):
            freeze(self.ws, self.catalog, self.coverage, self.recovery, self.ws / 'corpus')
