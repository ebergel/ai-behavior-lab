"""Read-only trajectory outcomes, with observed events and unavailable follow-up separate.

These rules describe text and recorded failures. They neither stop generation nor
infer a semantic label, a wish to end, or an absorbing model state.
"""
from collections import Counter

from .common import fingerprint, read_json, require
from .history import ancestry

RULES = {
    'schema': 'behaviorlab.trajectory-rules/1', 'id': 'trajectory-events-v1',
    'exact_repeat_messages': 6,
    'exact_repeat_text': 'Byte-equivalent Unicode strings; nonempty after whitespace check; both speakers in actual ancestry.',
    'repeat_action': 'Observe and continue; no online stopping or replacement.',
    'repeated_line_minimum': 10,
    'line_rule': 'Strip each line and omit empty lines; count occurrences of identical lines, including nonadjacent ones.',
    'cap_rule': 'Recorded output_cap is observed; capped text is partial; descendants remain unavailable.',
    'semantic_rule': 'No semantic labels. Valid repetition is observable text; invalid and blocked messages are not semantic negatives.',
    'scope': 'Prospective mechanical definitions informed by development evidence; retrospective applications are descriptive.',
}


def line_features(text):
    if text is None:
        return None
    counts = Counter(line.strip() for line in text.splitlines() if line.strip())
    maximum = max(counts.values(), default=0)
    return {'nonempty_lines': sum(counts.values()), 'maximum_identical_line_occurrences': maximum,
            'repeated_lines_visible': maximum >= RULES['repeated_line_minimum']}


def repeated_state(history):
    if not history or not history[-1].content.strip():
        return {'active': False, 'suffix_messages': 0, 'text_sha256': None, 'start_node': None, 'detection_node': None}
    text = history[-1].content; suffix = []
    for turn in reversed(history):
        if turn.content != text:
            break
        suffix.append(turn)
    suffix.reverse()
    active = len(suffix) >= RULES['exact_repeat_messages'] and len({t.speaker for t in suffix}) == 2
    return {'active': active, 'suffix_messages': len(suffix), 'text_sha256': fingerprint(text),
            'start_node': suffix[0].node_id,
            'detection_node': suffix[RULES['exact_repeat_messages']-1].node_id if active else None}


def invalid_visible_text(source, node):
    response = source.state.responses[source.state.attempts[node.id]]
    try:
        data = read_json(response['raw_response'])
        if isinstance(data.get('message'), dict):
            content = data['message'].get('content')
        elif isinstance(data.get('choices'), list) and len(data['choices']) == 1:
            content = data['choices'][0]['message'].get('content')
        else:
            return None
        return content if isinstance(content, str) else None
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def report(source):
    require(source.state.complete, 'Trajectory report requires a completed, verified snapshot')
    nodes = {n.id: n for n in source.nodes}; rows = []; events = []; lookup = {}
    for node in source.nodes:
        kind, outcome = source.state.outcomes[node.id]
        row = {'node': node.id, 'root': node.root, 'segment': node.segment, 'turn': node.turn,
               'speaker': node.speaker, 'model': node.model, 'reason': outcome.get('reason'),
               'blocking_event_node': None, 'repeat': None, 'lines': None}
        if kind == 'turn_committed':
            history = ancestry(node.id, source.turns)
            current = repeated_state(history); previous = repeated_state(history[:-1])
            row.update(availability='valid', repeat=current, lines=line_features(history[-1].content))
            if current['active'] and not previous['active']:
                events.append({'kind': 'exact_repeat_detected', 'node': node.id,
                    'start_node': current['start_node'], 'text_sha256': current['text_sha256']})
            if previous['active'] and current['text_sha256'] != previous['text_sha256']:
                events.append({'kind': 'exact_repeat_departure', 'node': node.id,
                    'from_detection_node': previous['detection_node'], 'from_text_sha256': previous['text_sha256']})
        elif kind == 'turn_invalid':
            is_cap = outcome['reason'] == 'output_cap'
            row.update(availability='observed_output_cap' if is_cap else 'observed_invalid_reply',
                       blocking_event_node=node.id)
            # Partial text remains an observation, never a completed semantic reply.
            row['lines'] = line_features(invalid_visible_text(source, node))
            events.append({'kind': 'output_cap' if is_cap else 'invalid_reply', 'node': node.id,
                           'reason': outcome['reason'], 'partial_text_lines': row['lines']})
        else:
            require(kind == 'node_blocked' and node.parent in lookup, 'Unexpected unaccounted node')
            row.update(availability='unavailable_descendant', blocking_event_node=lookup[node.parent]['blocking_event_node'])
            require(row['blocking_event_node'] is not None, 'Missing original blocking event')
        lookup[node.id] = row; rows.append(row)
    roots = []
    for root in source.protocol.roots:
        group = [r for r in rows if r['root'] == root.name]
        windows = []; boundaries = []
        for segment in source.protocol.segments:
            members = [r for r in group if r['segment'] == segment.name]
            targets = members[-6:]
            leaf = members[-1]
            windows.append({'segment': segment.name, 'planned_targets': len(targets),
                'availability': dict(Counter(r['availability'] for r in targets)),
                'active_repeat_targets': sum(r['repeat'] is not None and r['repeat']['active'] for r in targets),
                'endpoint_node': leaf['node'], 'endpoint_availability': leaf['availability'],
                'endpoint_repeat': leaf['repeat'], 'blocking_event_node': leaf['blocking_event_node']})
            if segment.parent is not None:
                parent = nodes[members[0]['node']].parent
                first = members[0]
                boundaries.append({'segment': segment.name, 'parent_node': parent,
                    'parent_valid': lookup[parent]['availability'] == 'valid',
                    'parent_repeat': lookup[parent]['repeat'], 'first_node': first['node'],
                    'first_availability': first['availability'],
                    'first_departs_parent_repeat': None if lookup[parent]['repeat'] is None or
                        not lookup[parent]['repeat']['active'] or first['availability'] != 'valid' else
                        first['repeat']['text_sha256'] != lookup[parent]['repeat']['text_sha256']})
        contrasts = []
        segments = {w['segment']: w for w in windows}
        for left, right in [('F', 'R'), ('FF', 'FR'), ('RF', 'RR')]:
            if left not in segments or right not in segments:
                continue
            left_first = next(n for n in source.nodes if n.root == root.name and n.segment == left)
            right_first = next(n for n in source.nodes if n.root == root.name and n.segment == right)
            require(left_first.parent == right_first.parent, 'Contrast must share actual parent')
            parent = left_first.parent
            contrasts.append({'left': left, 'right': right, 'shared_parent': parent,
                'parent_valid': lookup[parent]['availability'] == 'valid',
                'both_endpoints_valid': all(segments[s]['endpoint_availability'] == 'valid' for s in (left, right)),
                'endpoint_availability': {s: segments[s]['endpoint_availability'] for s in (left, right)}})
        roots.append({'root': root.name, 'pairing': [root.x_model, root.y_model],
            'availability': dict(Counter(r['availability'] for r in group)), 'windows': windows,
            'boundaries': boundaries, 'contrast_availability': contrasts,
            'all_four_terminal_endpoints_valid': all(segments[s]['endpoint_availability'] == 'valid' for s in ('FF','FR','RF','RR'))
                if all(s in segments for s in ('FF','FR','RF','RR')) else None})
    pairings = []
    for pairing in sorted({tuple(r['pairing']) for r in roots}):
        group = [r for r in roots if tuple(r['pairing']) == pairing]
        endpoints = []
        for segment in source.protocol.segments:
            windows = [w for r in group for w in r['windows'] if w['segment'] == segment.name]
            endpoints.append({'segment': segment.name, 'allocated_roots': len(group),
                'availability': dict(Counter(w['endpoint_availability'] for w in windows)),
                'valid_exact_repeat': sum(w['endpoint_repeat'] is not None and w['endpoint_repeat']['active'] for w in windows)})
        contrasts = []
        for left, right in [('F', 'R'), ('FF', 'FR'), ('RF', 'RR')]:
            eligible = [c for r in group for c in r['contrast_availability'] if c['left'] == left]
            if eligible:
                contrasts.append({'left': left, 'right': right, 'allocated_roots': len(group),
                    'valid_parent_roots': sum(c['parent_valid'] for c in eligible),
                    'both_endpoints_valid_roots': sum(c['both_endpoints_valid'] for c in eligible)})
        pairings.append({'pairing': list(pairing), 'allocated_roots': len(group),
            'endpoints': endpoints, 'contrast_denominators': contrasts,
            'all_four_terminal_endpoints_valid_roots': sum(r['all_four_terminal_endpoints_valid'] is True for r in group)
                if all(r['all_four_terminal_endpoints_valid'] is not None for r in group) else None})
    kinds = Counter(e['kind'] for e in events)
    return {'schema': 'behaviorlab.trajectory-report/1', 'source': source.identity,
        'rules': RULES, 'rules_sha256': fingerprint(RULES), 'rows': rows, 'events': events, 'roots': roots, 'pairings': pairings,
        'summary': {'planned_nodes': len(rows), 'independent_roots': len(roots),
            'availability': dict(Counter(r['availability'] for r in rows)), 'events': dict(kinds),
            'capped_replies_with_repeated_lines': sum(r['availability']=='observed_output_cap' and
                r['lines'] is not None and r['lines']['repeated_lines_visible'] for r in rows)},
        'interpretation': 'Repeat departure is a text change, not semantic or cognitive recovery. Counts deduplicate shared nodes; branches remain correlated. Endpoint-valid subsets are selected samples, not unconditional causal effects.'}
