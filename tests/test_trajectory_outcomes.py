import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.cli import main
from behaviorlab.common import canonical, read_json
from behaviorlab.evidence import completed_campaign
from behaviorlab.history import Turn
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import FakeBackend, create_campaign, execute
from behaviorlab.trajectory_outcomes import RULES, line_features, repeated_state, report
from scripts.check_trajectory_outcomes import ScenarioBackend

ROOT = Path(__file__).resolve().parents[1]


def history(texts, same_speaker=False):
    return [Turn(str(i), str(i-1) if i else None, 'root', i+1,
                 'X' if same_speaker or i % 2 == 0 else 'Y', text, None)
            for i, text in enumerate(texts)]


class RuleTests(unittest.TestCase):
    def test_exact_rule_needs_six_nonblank_messages_and_both_speakers(self):
        self.assertFalse(repeated_state(history(['...']*5))['active'])
        state = repeated_state(history(['other']+['...']*6))
        self.assertTrue(state['active'])
        self.assertEqual((state['start_node'], state['detection_node']), ('1', '6'))
        self.assertFalse(repeated_state(history(['...']*8, same_speaker=True))['active'])
        self.assertFalse(repeated_state(history([' \n']*8))['active'])
        self.assertFalse(repeated_state(history(['...']*5+['...\n']))['active'])
        self.assertFalse(repeated_state(history(['café']*5+['cafe\u0301']))['active'])
        self.assertEqual(repeated_state(history(['...']*8))['detection_node'], '5')

    def test_partial_line_feature_does_not_infer_semantics(self):
        self.assertIsNone(line_features(None))
        self.assertFalse(line_features('Echo.\n'*9)['repeated_lines_visible'])
        result = line_features((' Echo. \nother\n\n')*10+'unfinished')
        self.assertEqual(result, {'nonempty_lines':21,
            'maximum_identical_line_occurrences':10, 'repeated_lines_visible':True})
        self.assertFalse(line_features('')['repeated_lines_visible'])

    def test_saved_rules_match_instrument(self):
        self.assertEqual(read_json((ROOT/'design/trajectory-outcomes-v1.json').read_text()), RULES)

    def test_new_proposal_cannot_enable_live_factorial_execution(self):
        registry = Registry.load(ROOT/'design/models.json')
        proposal = read_json((ROOT/'design/round0-factorial-v0.2.json').read_text())
        with self.assertRaises(ValueError): Protocol.from_dict(proposal, registry)
        self.assertFalse(proposal['semantic_measurement_status']['revision_active'])


class TrajectoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.base = Path(self.tmp.name)
        self.registry = Registry.load(ROOT/'design/models.json')

    def tearDown(self):
        self.tmp.cleanup()

    def campaign(self, root=1, name='run'):
        data = read_json((ROOT/'examples/outcomes-factorial.fake.json').read_text())
        data['roots'] = [r for r in data['roots'] if r['id'] == f'AA-r0{root}']
        protocol = Protocol.from_dict(data, self.registry)
        path = self.base/name
        create_campaign(path, protocol, self.registry)
        return path, ScenarioBackend(protocol.seed_base)

    def test_actual_ancestry_inherits_repetition_and_deduplicates_shared_events(self):
        path, backend = self.campaign(); execute(path, backend=backend)
        result = report(completed_campaign(path))
        self.assertEqual(backend.calls, 90)
        detected = [e['node'] for e in result['events'] if e['kind']=='exact_repeat_detected']
        self.assertCountEqual(detected, ['AA-r01:prefix:30', 'AA-r01:R:38', 'AA-r01:RF:46'])
        departed = [e['node'] for e in result['events'] if e['kind']=='exact_repeat_departure']
        self.assertCountEqual(departed, ['AA-r01:R:31', 'AA-r01:FR:41', 'AA-r01:RF:41'])
        root = result['roots'][0]
        windows = {w['segment']:w for w in root['windows']}
        self.assertEqual(windows['FF']['endpoint_repeat']['start_node'], 'AA-r01:prefix:25')
        self.assertEqual(windows['RR']['endpoint_repeat']['start_node'], 'AA-r01:R:33')
        boundaries = {b['segment']:b for b in root['boundaries']}
        self.assertEqual(boundaries['RF']['parent_node'], 'AA-r01:R:40')
        self.assertIs(boundaries['RF']['first_departs_parent_repeat'], True)
        self.assertIs(boundaries['FF']['first_departs_parent_repeat'], False)
        # R's input has only three participant messages, but observation follows
        # its actual ancestry; the six-message rule can still detect repetition.
        self.assertTrue(windows['R']['endpoint_repeat']['active'])
        self.assertTrue(root['all_four_terminal_endpoints_valid'])

    def test_caps_block_only_actual_descendants_and_retain_original_event(self):
        cases = [(2, 'prefix', 28, 27, 62), (3, 'F', 37, 66, 23),
                 (4, 'FR', 44, 83, 6), (5, 'R', 40, 69, 20)]
        for root, segment, turn, valid, blocked in cases:
            with self.subTest(root=root):
                path, backend = self.campaign(root, str(root)); execute(path, backend=backend)
                result = report(completed_campaign(path)); origin = f'AA-r0{root}:{segment}:{turn}'
                self.assertEqual(result['summary']['availability'], {'valid':valid,
                    'observed_output_cap':1, 'unavailable_descendant':blocked})
                self.assertEqual(backend.calls, valid+1)
                unavailable = [r for r in result['rows'] if r['availability']!='valid']
                self.assertEqual({r['blocking_event_node'] for r in unavailable}, {origin})
                event = next(e for e in result['events'] if e['kind']=='output_cap')
                self.assertTrue(event['partial_text_lines']['repeated_lines_visible'])
                self.assertEqual(event['partial_text_lines']['maximum_identical_line_occurrences'], 12)
                contrasts = {c['left']:c for c in result['roots'][0]['contrast_availability']}
                if root==2:
                    self.assertFalse(contrasts['F']['parent_valid'])
                elif root==3:
                    self.assertTrue(contrasts['F']['parent_valid'])
                    self.assertFalse(contrasts['F']['both_endpoints_valid'])
                    self.assertTrue(contrasts['RF']['both_endpoints_valid'])
                    self.assertFalse(contrasts['FF']['parent_valid'])
                elif root==4:
                    self.assertTrue(contrasts['FF']['parent_valid'])
                    self.assertFalse(contrasts['FF']['both_endpoints_valid'])
                    self.assertTrue(contrasts['RF']['both_endpoints_valid'])

    def test_malformed_response_is_observed_invalid_not_cap_or_negative(self):
        class Malformed(FakeBackend):
            def generate(self, payload):
                self.calls += 1
                return '{bad json'
        path, _ = self.campaign(); backend = Malformed(); execute(path, backend=backend)
        result = report(completed_campaign(path))
        self.assertEqual(result['summary']['availability'], {
            'observed_invalid_reply':1, 'unavailable_descendant':89})
        self.assertEqual(result['events'][0]['reason'], 'malformed_response')
        self.assertIsNone(result['rows'][0]['lines'])
        self.assertEqual(backend.calls, 1)

    def test_raw_response_recovery_preserves_detection_without_duplicate_generation(self):
        control, control_backend = self.campaign(name='control')
        execute(control, backend=control_backend)
        path, before = self.campaign(name='interrupted')
        def crash(stage, node):
            if stage=='after_response' and node.turn==30:
                raise KeyboardInterrupt('fixture crash at detection boundary')
        with self.assertRaises(KeyboardInterrupt): execute(path, backend=before, hook=crash)
        with self.assertRaises(ValueError): completed_campaign(path)
        after = ScenarioBackend(before.seed_base); execute(path, backend=after)
        self.assertEqual((before.calls, after.calls), (30, 60))
        a = report(completed_campaign(control)); b = report(completed_campaign(path))
        a.pop('source'); b.pop('source'); self.assertEqual(a, b)

    def test_cli_is_read_only_and_does_not_call_inference_or_network(self):
        path, backend = self.campaign(); execute(path, backend=backend)
        original = (path/'events.jsonl').read_bytes()
        output = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=AssertionError('network forbidden')), \
             patch.object(FakeBackend, 'generate', side_effect=AssertionError('generation forbidden')), \
             contextlib.redirect_stdout(output):
            main(['trajectory-report', str(path)])
        result = read_json(output.getvalue())
        self.assertEqual(result['summary']['planned_nodes'], 90)
        self.assertEqual((path/'events.jsonl').read_bytes(), original)
        # Corruption cannot be interpreted as another kind of observed outcome.
        (path/'events.jsonl').write_bytes(original.replace(b'campaign_created', b'campaign_changed', 1))
        with self.assertRaises(ValueError): completed_campaign(path)
