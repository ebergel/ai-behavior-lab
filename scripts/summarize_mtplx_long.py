"""Offline audit of the long MTPLX engineering trial and preserved failures."""
import argparse
from datetime import datetime
from pathlib import Path
from statistics import median

from behaviorlab.common import canonical, read_json, require, sha256, timestamp
from behaviorlab.journal import read_events
from behaviorlab.runner import campaign_documents
from scripts.summarize_mtplx_qualification import summarize
from scripts.reassess_mtplx_parser import assess


def audit_main(directory):
    directory = Path(directory)
    result = summarize(directory)  # validates saved outcomes/captures; no live calls
    protocol, registry, state = campaign_documents(read_events(directory / 'events.jsonl'))
    require(result['committed_turns'] == 50 and len(protocol.roots) == 1, 'Expected a complete 50-turn main trajectory')
    require(state.meta['parser_version'] == 'http-chat/2', 'The main trajectory requires the corrected parser')
    require([(s.start, s.stop, s.history) for s in protocol.segments] == [(1, 30, 'F'), (31, 40, 'R'), (41, 50, 'F')],
            'Unexpected history schedule')
    nodes = protocol.nodes()
    rows = []
    for node, call in zip(nodes, result['calls']):
        require(node.id == call['node'], 'Call order differs from the trajectory')
        saved = state.requests[state.attempts[node.id]]
        payload = saved['request']
        response = read_json(state.responses[state.attempts[node.id]]['raw_response'])
        content = state.outcomes[node.id][1]['content']
        # Independently compare every saved message to the selected committed
        # utterance, then rely on engine token captures for the rendered form.
        history_nodes = list(nodes[:node.turn-1])
        selected = history_nodes if node.history == 'F' else history_nodes[-3:]
        expected = [{'role': 'system', 'content': protocol.system}]
        if node.speaker == 'X' and node.history == 'F':
            expected.append({'role': 'user', 'content': protocol.opening})
        expected.extend({'role': 'assistant' if n.speaker == node.speaker else 'user',
                         'content': state.outcomes[n.id][1]['content']} for n in selected)
        require(payload['messages'] == expected, 'Selected ancestry or participant roles changed')
        trace = response['choices'][0]['message'].get('reasoning_content', '')
        rows.append(dict(call, turn=node.turn, speaker=node.speaker,
            visible_words=len(content.split()), visible_chars=len(content), reasoning_chars=len(trace),
            retained_turns=[n.turn for n in selected], message_count=len(payload['messages']),
            http_deadline_seconds=state.responses[state.attempts[node.id]]['transport']['timeout_seconds'],
            http_started_at=state.responses[state.attempts[node.id]]['transport']['started_at'],
            http_finished_at=state.responses[state.attempts[node.id]]['transport']['finished_at'],
            output_reserve=payload['max_tokens'],
            context_headroom=saved['preflight']['context_window']-saved['preflight']['input_tokens']-payload['max_tokens']))
    require(all(c['input_token_ids_match'] and c['cache_bypassed'] and c['cached_tokens'] == 0 for c in rows),
            'Input or cache bypass contract failed')
    require(all(c['context_headroom'] >= 0 and c['finish_reason'] == 'stop' and not c['possible_stats_footer'] for c in rows),
            'Context, completion or footer check failed')
    require(all(c['requested_output_limit'] == c['effective_output_limit'] == c['server_output_cap'] == 8192
                and c['server_cap_applied'] is False for c in rows), 'Output allowances were not aligned')
    periods = []
    for start, stop in [(1, 10), (11, 20), (21, 30), (31, 40), (41, 50)]:
        subset = [c for c in rows if start <= c['turn'] <= stop]
        periods.append({'turns': [start, stop], 'history': subset[0]['history'],
            'input_tokens_min': min(c['prompt_tokens'] for c in subset),
            'input_tokens_max': max(c['prompt_tokens'] for c in subset),
            'median_http_seconds': median(c['http_seconds'] for c in subset),
            'total_http_seconds': sum(c['http_seconds'] for c in subset),
            'median_visible_words': median(c['visible_words'] for c in subset),
            'median_decode_tokens_per_second': median(c['server_decode_tokens_per_second'] for c in subset)})
    return {'campaign': result, 'turns': rows, 'periods': periods,
            'history_transition_checks': [rows[n-1] for n in (30, 31, 40, 41, 50)],
            'max_input_tokens': max(c['prompt_tokens'] for c in rows),
            'max_output_tokens': max(c['completion_tokens'] for c in rows),
            'min_context_headroom': min(c['context_headroom'] for c in rows),
            'visible_words_min': min(c['visible_words'] for c in rows),
            'visible_words_median': median(c['visible_words'] for c in rows),
            'visible_words_max': max(c['visible_words'] for c in rows),
            'visible_words_total': sum(c['visible_words'] for c in rows),
            'total_generation_http_seconds': sum(c['http_seconds'] for c in rows),
            'elapsed_first_dispatch_to_last_response_seconds': (
                datetime.fromisoformat(rows[-1]['http_finished_at']) -
                datetime.fromisoformat(rows[0]['http_started_at'])).total_seconds(),
            'wall_time_scope': 'Includes inter-request verification/tokenization and the planned process interruption; excludes initial setup and final audit.',
            'max_server_peak_memory_bytes': max(c['server_peak_memory_bytes'] or 0 for c in rows),
            'visible_word_count_method': 'Whitespace-separated words via Python str.split(); descriptive, not a strict word-limit adjudication.'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    p.add_argument('--main-campaign', required=True, help='explicitly select the completed trajectory to audit')
    args = p.parse_args()
    base = Path(args.directory)
    main = audit_main(base / args.main_campaign)
    failures = [summarize(f.parent, allow_incomplete=True) for f in sorted(base.glob('*/events.jsonl'))
                if f.parent.name != args.main_campaign]
    reassessed = [assess(base / f['directory']) for f in failures]
    recovery = read_json((base / 'recovery-result.json').read_text())
    guard = read_json((base / 'oversize-guard.json').read_text())
    guard = {k: v for k, v in guard.items() if k != 'request'}
    originals = set()
    for campaign in [main['campaign']] + failures:
        for call in campaign['calls']:
            request_id = call['request_id']
            safe_id = ''.join(c if c.isalnum() or c in '-_' else '_' for c in request_id)[:80]
            matches = list((base / 'captures').glob('req-*-' + safe_id + '.json'))
            require(len(matches) == 1, 'Missing or ambiguous original engine capture')
            require(sha256(matches[0].read_bytes()) == call['capture_sha256'], 'Original capture file differs from journal')
            require(request_id not in originals, 'Duplicate response identity across campaigns')
            originals.add(request_id)
    total_calls = main['campaign']['requests'] + sum(f['requests'] for f in failures)
    require(len(originals) == total_calls, 'Missing engine generation captures')
    # Other clients might use this local server. Count unassigned files without
    # inspecting their contents or treating them as laboratory evidence.
    unassigned = len(list((base / 'captures').glob('req-*.json'))) - len(originals)
    report = {'schema': 'behaviorlab.mtplx-long-validation/1', 'created_at': timestamp(),
              'data_class': 'local_engineering_not_behavioral_findings', 'main': main,
              'preserved_other_campaigns': failures, 'total_generation_calls_including_failures': total_calls,
              'preserved_other_campaign_reassessments': reassessed,
              'current_parser_accepted_including_development': 50 + sum(
                  r['current_counts'].get('turn_committed', 0) for r in reassessed),
              'current_parser_invalid_including_development': sum(
                  r['current_counts'].get('turn_invalid', 0) for r in reassessed),
              'recovery': recovery, 'oversize_guard': guard,
              'all_original_engine_capture_files_verified': True,
              'unassigned_capture_files_not_inspected': unassigned,
              'limits': ['One RF trajectory on one reasoning-on checkpoint; no mixed-model or full factorial qualification.',
                         'Development included three output-cap failures and four responses with a silently clamped allowance.',
                         'Observed input sizes, not the full configured 32768-token window, are qualified.',
                         'Engine timing and memory telemetry do not measure all machine resource use.',
                         'Task-directed engineering prompts do not test spontaneous experiential or nondual discourse.']}
    print(canonical(report))


if __name__ == '__main__':
    main()
