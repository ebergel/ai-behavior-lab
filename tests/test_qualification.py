import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab import ollama_context as oc
from behaviorlab.backends import parse_live
from behaviorlab.common import read_json
from behaviorlab.journal import read_events
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import create_campaign, campaign_documents, execute
import test_ollama_context
from test_live import wire

ROOT = Path(__file__).resolve().parents[1]


class QualificationTests(unittest.TestCase):
    def test_frozen_budget_and_schema_cannot_admit_factorial(self):
        r = Registry.load(ROOT/'design/ollama-context-models.json')
        d = read_json((ROOT/'design/common-prompt.qualification.json').read_text())
        p = Protocol.from_dict(d, r)
        self.assertEqual(len(p.nodes()), 120)
        for mutate in (
            lambda x: x.update(execution_class='engineering_local'),
            lambda x: x['qualification']['decisions'].update(main_pilot_enabled=True),
            lambda x: x['qualification']['decisions'].update(no_adaptive_replacements=False),
            lambda x: x['segments'][0].update(stop=50),
            lambda x: x['roots'][0].update(Y='B'),
        ):
            bad = copy.deepcopy(d); mutate(bad)
            with self.assertRaises(ValueError): Protocol.from_dict(bad, r)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'campaign'; create_campaign(path, p, r)
            _, _, state = campaign_documents(read_events(path/'events.jsonl'))
            self.assertEqual(state.meta['data_class'], 'local_qualification_screen_not_factorial_pilot')
            before = (path/'events.jsonl').read_bytes()
            with self.assertRaisesRegex(ValueError, 'replacement'):
                execute(path, max_calls=0, retry_unresolved=True)
            self.assertEqual((path/'events.jsonl').read_bytes(), before)

    def test_thinking_profile_requires_mode_and_parser4(self):
        # Reuse a pure HTTP fixture, not an inference call or a full test subclass.
        f = test_ollama_context.OllamaContextTests(); f.setUp()
        d = read_json(f.registry.document_json)
        d['models'][0]['artifact']['qualification'].update(schema=oc.MODE_SCHEMA, thinking=True)
        f.registry = Registry.from_dict(d); f.model = f.registry.model('A'); f.q = oc.profile(f.model)
        f.payload['think'] = True
        evidence = f.preflight()
        self.assertEqual(evidence['schema'], oc.MODE_SCHEMA)
        data, _ = f.response(evidence)
        data['message']['thinking'] = 'Private trace.'
        response = wire(data); response.evidence['ollama_context'] = evidence
        parsed = parse_live(response.raw, f.payload, f.model, response.evidence)
        self.assertIn('Private trace.', parsed['thinking'])
        self.assertNotIn('Private trace.', parsed['content'])
        with self.assertRaises(ValueError):
            parse_live(response.raw, f.payload, f.model, response.evidence, parser_version='http-chat/3')
        f.payload['think'] = False
        with self.assertRaisesRegex(ValueError, 'pinned thinking'):
            f.preflight()

    def test_reference_controls_are_declared_and_mode_mismatch_rejected(self):
        for name, label, ctx, cap, think in [('qwen', 'A', 12288, 400, False), ('gemma', 'B', 16384, 2500, True)]:
            r = Registry.load(ROOT/('design/'+name+'-reference-models.json'))
            d = read_json((ROOT/('design/'+name+'-reference.qualification.json')).read_text())
            self.assertEqual(len(Protocol.from_dict(d, r).nodes()), 60)
            s = d['settings']['by_model'][label]
            self.assertEqual((s['options']['num_ctx'], s['options']['num_predict'], s['think']), (ctx, cap, think))
            s['think'] = not think
            with self.assertRaises(ValueError): Protocol.from_dict(d, r)


if __name__ == '__main__': unittest.main()
