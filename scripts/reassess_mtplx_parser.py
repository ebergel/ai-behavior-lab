"""Apply the current parser to saved responses without rewriting historical journals."""
import argparse
from collections import Counter
from pathlib import Path

from behaviorlab.backends import LIVE_PARSER
from behaviorlab.common import canonical, sha256, timestamp
from behaviorlab.journal import read_events
from behaviorlab.runner import campaign_documents, outcome


def assess(directory):
    path = Path(directory) / 'events.jsonl'
    before = path.read_bytes()
    protocol, registry, state = campaign_documents(read_events(path))
    nodes = {n.id: n for n in protocol.nodes()}
    rows = []
    for attempt, response in state.responses.items():
        request = state.requests[attempt]
        node = nodes[request['node_id']]
        kind, result = outcome(node, attempt, response['raw_response'], request['request'],
                               registry.model(node.model), response['transport'], LIVE_PARSER)
        old = state.outcomes.get(node.id)
        rows.append({'node': node.id, 'attempt': attempt,
                     'original_outcome': old[0] if old else 'uncommitted',
                     'current_parser_outcome': kind, 'reason': result.get('reason'), 'detail': result.get('detail')})
    assert path.read_bytes() == before, 'Reassessment altered source journal'
    return {'directory': str(Path(directory)), 'journal_sha256': sha256(before),
            'original_parser': state.meta['parser_version'], 'assessment_parser': LIVE_PARSER,
            'journal_unchanged': True, 'responses_assessed': len(rows),
            'original_counts': dict(Counter(r['original_outcome'] for r in rows)),
            'current_counts': dict(Counter(r['current_parser_outcome'] for r in rows)), 'rows': rows}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('campaigns', nargs='+')
    args = p.parse_args()
    print(canonical({'schema': 'behaviorlab.parser-reassessment/1', 'at': timestamp(),
                     'scope': 'Current response-contract assessment; original parser outcomes and journals remain intact.',
                     'campaigns': [assess(c) for c in args.campaigns]}))


if __name__ == '__main__':
    main()
