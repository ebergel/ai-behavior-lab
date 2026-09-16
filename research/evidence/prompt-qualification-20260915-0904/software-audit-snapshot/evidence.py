"""Read-only reconstruction of completed campaigns for derived work."""
from pathlib import Path
from types import SimpleNamespace

from .common import read_json, require, sha256
from .history import request
from .journal import read_events
from .runner import campaign_documents, outcome, turn_from


def completed_campaign(directory):
    path = Path(directory) / 'events.jsonl'
    raw = path.read_bytes()
    events = read_events(path)
    protocol, registry, state = campaign_documents(events)
    require(state.complete, 'Derived work requires a completed campaign snapshot')
    turns = {}
    nodes = protocol.nodes()
    for node in nodes:
        kind, result = state.outcomes[node.id]
        if kind == 'node_blocked':
            require(node.parent in state.outcomes and state.outcomes[node.parent][0] != 'turn_committed'
                    and result['parent_id'] == node.parent, 'Invalid blocked ancestry')
            continue
        payload = request(protocol, registry, node, turns)
        attempt = state.attempts[node.id]
        saved, response = state.requests[attempt], state.responses[attempt]
        require(saved['request'] == payload and saved['model_digest'] == registry.model(node.model).digest,
                'Saved request differs from reconstructed history/model')
        live = state.meta['backend'] != 'deterministic-fake/1'
        if live:
            require(saved['model_identity'] == read_json(registry.model(node.model).metadata_json),
                    'Saved model identity differs from source registry')
        expected = outcome(node, attempt, response['raw_response'], payload,
                           registry.model(node.model) if live else None,
                           response.get('transport'), state.meta['parser_version'])
        require(expected == (kind, result), 'Saved outcome differs from raw evidence')
        if kind == 'turn_committed':
            turns[node.id] = turn_from(node, result)
    require(path.read_bytes() == raw, 'Source changed during snapshot validation')
    return SimpleNamespace(protocol=protocol, registry=registry, state=state, turns=turns,
        nodes=nodes, identity={'journal_sha256': sha256(raw), 'journal_bytes': len(raw),
            'journal_head': events[-1]['hash'], 'protocol_sha256': protocol.digest,
            'registry_sha256': registry.digest, 'data_class': state.meta['data_class']})
