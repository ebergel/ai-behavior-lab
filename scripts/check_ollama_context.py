"""Exercise actual recipient rendering/tokenization without generation."""
import argparse
from pathlib import Path

from behaviorlab.backends import HTTPBackend, prepare_request
from behaviorlab.common import canonical, read_json, require, sha256, timestamp
from behaviorlab.ollama_context import ContextLimitError
from behaviorlab.protocol import Registry


def main():
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    p.add_argument('--registry', required=True)
    p.add_argument('--protocol', required=True)
    args = p.parse_args()
    base = Path(args.directory)
    registry = Registry.load(args.registry)
    settings = read_json(Path(args.protocol).read_text())['settings']['by_model']
    system = {'role': 'system', 'content': 'Engineering rendering check. Keep each reply to at most 150 words. Do not use tools.'}
    cases = {
        'unicode-empty': [system, {'role': 'user', 'content': 'Check calibration: 20 °C, café, 空.'},
                          {'role': 'assistant', 'content': ''}, {'role': 'user', 'content': 'Name one source of uncertainty.'}],
        'long': [system] + [{'role': 'user' if i % 2 == 0 else 'assistant', 'content':
                 'Observation ' + str(i) + ': ' + ('Record temperature, calibration, location, time, missing values, and uncertainty. ' * 10)}
                for i in range(51)],
        'oversize': [system, {'role': 'user', 'content': 'calibration record ' * 18000}],
    }
    backend = HTTPBackend(); rows = []
    for model in registry.models:
        observation = backend.verify(model)
        for name, messages in cases.items():
            payload = prepare_request(model, settings[model.label], messages, 915211701)
            try:
                evidence = backend.preflight(payload, model)
                rejected = False
            except ContextLimitError as exc:
                evidence = exc.evidence
                rejected = True
            require(rejected == (name == 'oversize'), 'Unexpected fixture context decision')
            record = {'at': timestamp(), 'case': name, 'model': model.label, 'generation_calls': 0,
                      'request': payload, 'observation': observation, 'preflight': evidence,
                      'oversize_rejected': rejected}
            file = base / ('render-' + model.label + '-' + name + '.json')
            with file.open('x') as f:
                f.write(canonical(record) + '\n')
            rows.append({'model': model.label, 'case': name, 'message_count': len(messages),
                         'input_tokens': evidence['input_tokens'], 'context_headroom': evidence['context_headroom'],
                         'oversize_rejected': rejected, 'file': file.name, 'sha256': sha256(file.read_bytes())})
    report = {'schema': 'behaviorlab.ollama-context-fixtures/1', 'created_at': timestamp(),
              'generation_calls': 0, 'cases': rows}
    with (base/'render-fixtures.json').open('x') as f:
        f.write(canonical(report) + '\n')
    print(canonical(report))


if __name__ == '__main__':
    main()
