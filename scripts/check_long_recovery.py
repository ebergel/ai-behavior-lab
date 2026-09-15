"""Bounded 50-turn local trial with an explicit response-save interruption.

Run 'first' to generate turns 1-25 and interrupt before committing turn 25.
Run 'resume' in a new process to reuse its saved response and generate 26-50.
The server must already match the supplied registry. No automatic retry occurs.
"""
import argparse
import json
from pathlib import Path

from behaviorlab.backends import HTTPBackend
from behaviorlab.common import canonical, read_json, require, sha256, timestamp
from behaviorlab.journal import read_events
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import campaign_documents, create_campaign, execute


class PlannedInterruption(BaseException):
    pass


def save_new(path, document):
    with Path(path).open('x') as f:
        f.write(canonical(document) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=('first', 'resume'))
    p.add_argument('directory')
    p.add_argument('--protocol')
    p.add_argument('--registry')
    p.add_argument('--request-timeout', type=float, default=300,
                   help='client HTTP deadline in seconds; recorded outside model inputs')
    args = p.parse_args()
    directory = Path(args.directory)
    journal = directory / 'events.jsonl'
    checkpoint = directory.parent / 'recovery-checkpoint.json'
    if args.phase == 'first':
        require(args.protocol and args.registry, 'A new trial requires protocol and registry')
        registry = Registry.load(args.registry)
        protocol = Protocol.load(args.protocol, registry)
        require(len(protocol.roots) == 1 and [n.turn for n in protocol.nodes()] == list(range(1, 51)),
                'This check requires one 50-turn trajectory')
        def qualified(model):
            row = read_json(model.metadata_json)
            return row['backend'] == 'mtplx' or (row['backend'] == 'ollama' and
                row['artifact'].get('qualification', {}).get('schema') == 'ollama-local-render/1')
        require(all(qualified(m) for m in registry.models),
                'This qualification driver requires direct models with rendered-context checks')
        create_campaign(directory, protocol, registry)
        def hook(stage, node):
            if stage == 'after_commit':
                print('Recorded turn outcome', node.turn, 'history', node.history, flush=True)
            if stage == 'after_response' and node.turn == 25:
                raise PlannedInterruption()
        try:
            result = execute(directory, backend=HTTPBackend(request_timeout=args.request_timeout), max_calls=25, hook=hook)
        except PlannedInterruption:
            raw = journal.read_bytes()
            _, _, state = campaign_documents(read_events(journal))
            require(len(state.requests) == len(state.responses) == 25 and len(state.outcomes) == 24,
                    'Unexpected state at injected interruption')
            node = protocol.nodes()[24]
            attempt = state.attempts[node.id]
            require(node.id not in state.outcomes, 'Interrupted response was already committed')
            record = {'at': timestamp(), 'injection': 'controlled exception after durable response save, before turn commit',
                      'journal_prefix_bytes': len(raw), 'journal_prefix_sha256': sha256(raw),
                      'node': node.id, 'attempt': attempt,
                      'response_sha256': sha256(state.responses[attempt]['raw_response'].encode()),
                      'requests_before_resume': 25, 'responses_before_resume': 25, 'commits_before_resume': 24}
            save_new(checkpoint, record)
            print(canonical(record), flush=True)
        else:
            raise RuntimeError('Trial ended before planned interruption: ' + canonical(result))
    else:
        require(not args.protocol and not args.registry, 'Resume uses the frozen campaign documents')
        before = read_json(checkpoint.read_text())
        raw = journal.read_bytes()
        require(len(raw) == before['journal_prefix_bytes'] and sha256(raw) == before['journal_prefix_sha256'],
                'Evidence changed since the planned interruption')
        def hook(stage, node):
            if stage == 'after_commit':
                print('Recorded turn outcome', node.turn, 'history', node.history, flush=True)
        result = execute(directory, backend=HTTPBackend(request_timeout=args.request_timeout), max_calls=25, hook=hook)
        require(result['committed_turns'] == 50 and result['requests'] == result['responses'] == 50 and result['complete'],
                'The resumed trajectory did not complete all 50 turns')
        after = journal.read_bytes()
        _, _, state = campaign_documents(read_events(journal))
        require(after.startswith(raw), 'Resume replaced saved journal bytes')
        require(state.attempts[before['node']] == before['attempt'] and
                sha256(state.responses[before['attempt']]['raw_response'].encode()) == before['response_sha256'],
                'Resume changed the saved response')
        record = {'at': timestamp(), 'new_generation_calls': result['requests'] - before['requests_before_resume'],
                  'saved_response_reused': True, 'saved_journal_prefix_preserved': True,
                  'main_calls_total': result['requests'], 'result': result}
        save_new(directory.parent / 'recovery-result.json', record)
        print(canonical(record), flush=True)


if __name__ == '__main__':
    main()
