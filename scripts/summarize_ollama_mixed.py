"""Offline audit of the native Ollama mixed-model engineering qualification."""
import argparse
from datetime import datetime
from pathlib import Path
from statistics import median

from behaviorlab.common import canonical, fingerprint, read_json, require, sha256, timestamp
from behaviorlab.journal import read_events
from behaviorlab.ollama_context import decoded, parameter_values, profile
from behaviorlab.runner import campaign_documents, execute
from scripts.summarize_mtplx_qualification import OfflineBackend


def audit_campaign(directory):
    directory = Path(directory)
    journal = directory / 'events.jsonl'
    before = journal.read_bytes()
    protocol, registry, state = campaign_documents(read_events(journal))
    require(state.complete and state.meta['parser_version'] == 'http-chat/3',
            'Expected a complete parser-3 campaign')
    result = execute(directory, backend=OfflineBackend())
    require(journal.read_bytes() == before, 'Offline replay changed evidence')
    nodes = protocol.nodes()
    require(len(state.requests) == len(state.responses) == len(nodes) == result['committed_turns']
            and not state.errors and not state.retried, 'Expected exactly one valid response per node')
    rows = []
    for node in nodes:
        attempt = state.attempts[node.id]
        saved, response = state.requests[attempt], state.responses[attempt]
        payload, transport = saved['request'], response['transport']
        data = read_json(response['raw_response'])
        preflight = saved['preflight']
        require(preflight == transport['ollama_context'], 'Saved preflight differs from response evidence')
        model = registry.model(node.model)
        q = profile(model)
        observed = saved['observation']
        require(observed['ollama_files']['content_hash_verified'] is True
                and observed['ollama_files']['files_fingerprint'] == fingerprint(q['files'])
                and observed['weight_digest'] == model.digest, 'Missing pinned artifact verification')
        values = parameter_values(observed['parameters_text'])
        require(values == q['parameters'] and fingerprint(values) == observed['parameters_values_sha256']
                and sha256(observed['parameters_text'].encode()) == observed['parameters_sha256'],
                'Default-parameter observation differs from the registry')
        # Independently reconstruct a linear root's selected committed utterances.
        ancestors = [n for n in nodes if n.root == node.root and n.turn < node.turn]
        selected = ancestors if node.history == 'F' else ancestors[-3:]
        expected = [{'role': 'system', 'content': protocol.system}]
        if node.speaker == 'X' and node.history == 'F':
            expected.append({'role': 'user', 'content': protocol.opening})
        expected.extend({'role': 'assistant' if n.speaker == node.speaker else 'user',
                         'content': state.outcomes[n.id][1]['content']} for n in selected)
        require(payload['messages'] == expected, 'History selection or recipient roles differ')
        content = state.outcomes[node.id][1]['content']
        require(data['done_reason'] == 'stop' and not data['message'].get('thinking'),
                'Output cap or unexpected thinking')
        decode_seconds = data['eval_duration'] / 1e9
        rows.append({'node': node.id, 'turn': node.turn, 'model': node.model,
            'tag': model.tag, 'speaker': node.speaker, 'history': node.history,
            'retained_turns': [n.turn for n in selected], 'message_count': len(expected),
            'input_tokens': preflight['input_tokens'], 'reported_input_tokens': data['prompt_eval_count'],
            'cached_tokens': data['prompt_eval_cached_count'],
            'output_tokens': data['eval_count'], 'output_reserve': preflight['reserved_output_tokens'],
            'context_headroom': preflight['context_headroom'], 'visible_words': len(content.split()),
            'visible_chars': len(content), 'finish_reason': data['done_reason'],
            'http_seconds': transport['elapsed_seconds'], 'http_started_at': transport['started_at'],
            'http_finished_at': transport['finished_at'], 'http_deadline_seconds': transport['timeout_seconds'],
            'server_total_seconds': data['total_duration']/1e9,
            'server_load_seconds': data['load_duration']/1e9,
            'server_prompt_eval_seconds': data['prompt_eval_duration']/1e9,
            'server_decode_seconds': decode_seconds,
            'server_decode_tokens_per_second': data['eval_count']/decode_seconds if decode_seconds else None,
            'rendered_utf8_sha256': preflight['rendered_utf8_sha256'],
            'preflight_token_ids_sha256': preflight['prompt_token_ids_sha256'],
            'generation_response_sha256': transport['response_sha256'],
            'defaults_raw_text_sha256': observed['parameters_sha256'],
            'defaults_values_sha256': observed['parameters_values_sha256']})
    result.update(directory=directory.name, journal_sha256=sha256(before), journal_bytes=len(before),
                  parser_version=state.meta['parser_version'], offline_replay_preserved_journal=True)
    return {'campaign': result, 'turns': rows}


def metrics(rows):
    return {'turn_count': len(rows),
        'max_input_tokens': max(c['input_tokens'] for c in rows),
        'max_output_tokens': max(c['output_tokens'] for c in rows),
        'min_context_headroom': min(c['context_headroom'] for c in rows),
        'visible_words_min': min(c['visible_words'] for c in rows),
        'visible_words_median': median(c['visible_words'] for c in rows),
        'visible_words_max': max(c['visible_words'] for c in rows),
        'replies_above_150_words': sum(c['visible_words'] > 150 for c in rows),
        'total_generation_http_seconds': sum(c['http_seconds'] for c in rows),
        'median_generation_http_seconds': median(c['http_seconds'] for c in rows),
        'median_server_decode_tokens_per_second': median(c['server_decode_tokens_per_second'] for c in rows),
        'calls_reporting_cached_tokens': sum(c['cached_tokens'] > 0 for c in rows),
        'cached_tokens_total': sum(c['cached_tokens'] for c in rows)}


def audit(base):
    base = Path(base)
    main, smoke = audit_campaign(base/'trajectory'), audit_campaign(base/'smoke')
    rows = main['turns']
    require([c['turn'] for c in rows] == list(range(1, 51)), 'Expected a 50-turn trajectory')
    require([c['history'] for c in rows] == ['F']*30 + ['R']*10 + ['F']*10, 'History schedule changed')
    require([c['model'] for c in rows] == ['A', 'B']*25, 'Recipient sequence changed')
    require([c['model'] for c in smoke['turns']] == ['A', 'B'], 'Expected two model smoke calls')
    require({p.parent.name for p in base.glob('*/events.jsonl')} == {'trajectory', 'smoke'},
            'Additional campaigns must be accounted for explicitly')
    checkpoint = read_json((base/'recovery-checkpoint.json').read_text())
    recovery = read_json((base/'recovery-result.json').read_text())
    raw = (base/'trajectory/events.jsonl').read_bytes()
    require(sha256(raw[:checkpoint['journal_prefix_bytes']]) == checkpoint['journal_prefix_sha256'],
            'Saved recovery prefix changed')
    _, _, state = campaign_documents(read_events(base/'trajectory/events.jsonl'))
    require(state.attempts[checkpoint['node']] == checkpoint['attempt']
            and sha256(state.responses[checkpoint['attempt']]['raw_response'].encode()) == checkpoint['response_sha256']
            and checkpoint['requests_before_resume'] == checkpoint['responses_before_resume'] == 25
            and checkpoint['commits_before_resume'] == 24
            and recovery['new_generation_calls'] == 25 and recovery['main_calls_total'] == 50
            and recovery['saved_response_reused'] and recovery['saved_journal_prefix_preserved'],
            'Recovery accounting failed')
    fixtures = read_json((base/'render-fixtures.json').read_text())
    require(len(fixtures['cases']) == 6 and fixtures['generation_calls'] == 0, 'Expected six non-generating fixtures')
    for case in fixtures['cases']:
        raw = (base/case['file']).read_bytes()
        require(sha256(raw) == case['sha256'], 'Fixture evidence changed')
        record = read_json(raw.decode())
        e = record['preflight']
        require(record['generation_calls'] == 0 and record['oversize_rejected'] == case['oversize_rejected'],
                'Fixture generation/rejection record differs')
        require(len(decoded(e['tokenization'])['tokens']) == case['input_tokens'] == e['input_tokens']
                and (e['context_headroom'] < 0) == case['oversize_rejected'], 'Fixture accounting differs')
    main['metrics'] = metrics(rows)
    main['metrics']['elapsed_first_dispatch_to_last_response_seconds'] = (
        datetime.fromisoformat(rows[-1]['http_finished_at']) - datetime.fromisoformat(rows[0]['http_started_at'])).total_seconds()
    main['by_model'] = {m: metrics([c for c in rows if c['model'] == m]) for m in ('A', 'B')}
    main['periods'] = [{'turns': [a, b], **metrics([c for c in rows if a <= c['turn'] <= b])}
                       for a, b in [(1, 30), (31, 40), (41, 50)]]
    main['history_transitions'] = [rows[n-1] for n in (30, 31, 40, 41, 50)]
    return {'schema': 'behaviorlab.ollama-mixed-validation/1', 'created_at': timestamp(),
        'data_class': 'local_engineering_not_behavioral_findings',
        'main': main, 'smoke': smoke, 'total_generation_calls': 52,
        'checkpoint': checkpoint, 'recovery': recovery, 'render_fixtures': fixtures,
        'word_count_method': 'Whitespace-separated words via str.split(); outputs are never trimmed.',
        'limits': ['One AB RF trajectory with a task-directed engineering prompt, not the research factorial or phenotype stimulus.',
            'Recipient render/token preflight and generation token-count agreement; no capture of generation input token IDs or final sampler values.',
            'Native runner caching remains enabled; reported cached tokens are recorded, with no cache-equivalence claim.',
            'Observed inputs qualify only the exercised sizes, not the entire configured 32768-token context window.',
            'Server durations and HTTP times do not measure all machine resource use; /props sampler values are defaults, not effective request telemetry.']}


def main():
    p = argparse.ArgumentParser(); p.add_argument('directory')
    print(canonical(audit(p.parse_args().directory)))


if __name__ == '__main__':
    main()
