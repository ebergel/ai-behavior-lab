"""Audit the frozen qualification jobs and prepare masked review packets.

Uses saved evidence only. It neither rates semantics nor generates replacements.
"""
import argparse
from collections import Counter
from pathlib import Path

from behaviorlab.annotations import create_packet, mechanical_report, save_new
from behaviorlab.common import fingerprint, read_json, require, sha256, timestamp
from behaviorlab.evidence import completed_campaign
from behaviorlab.ollama_context import profile


def main():
    p = argparse.ArgumentParser(); p.add_argument('directory'); args = p.parse_args()
    base = Path(args.directory); freeze = read_json((base/'freeze.json').read_text())
    rows = []; total = 0
    for job in freeze['jobs']:
        path = base/job['name']
        if not path.exists():
            rows.append({'job': job['name'], 'not_run': True, 'prerequisite': job['requires']}); continue
        source = completed_campaign(path); state = source.state
        require(len(state.requests) <= job['max_calls'] and not state.retried, 'Frozen budget/retry rule violated')
        total += len(state.requests)
        raw = [read_json(response['raw_response']) for response in state.responses.values()]
        call_rows = []
        for node in source.nodes:
            if node.id not in state.attempts: continue
            attempt = state.attempts[node.id]
            saved, response = state.requests[attempt], state.responses[attempt]
            payload, transport = saved['request'], response['transport']
            require(saved['preflight'] == transport['ollama_context'], 'Saved preflight/response evidence differs')
            model = source.registry.model(node.model)
            require(saved['observation']['weight_digest'] == model.digest
                    and saved['observation']['ollama_files']['content_hash_verified'] is True
                    and saved['observation']['ollama_files']['files_fingerprint'] == fingerprint(profile(model)['files']),
                    'Pinned model/runtime observation differs')
            earlier = [n for n in source.nodes if n.root == node.root and n.turn < node.turn]
            expected = [{'role': 'system', 'content': source.protocol.system}]
            if node.speaker == 'X': expected.append({'role': 'user', 'content': source.protocol.opening})
            expected.extend({'role': 'assistant' if n.speaker == node.speaker else 'user',
                             'content': source.turns[n.id].content} for n in earlier)
            require(payload['messages'] == expected, 'Independent visible-history/role audit failed')
            data = read_json(response['raw_response']); pf = saved['preflight']
            call_rows.append({'node': node.id, 'seed': payload['options']['seed'], 'input_tokens': pf['input_tokens'],
                'reported_input_tokens': data['prompt_eval_count'], 'cached_tokens': data['prompt_eval_cached_count'],
                'reserved_output_tokens': pf['reserved_output_tokens'], 'context_headroom': pf['context_headroom'],
                'generated_tokens': data['eval_count'], 'visible_words': len(data['message']['content'].split()),
                'trace_characters': len(data['message'].get('thinking', '')), 'finish_reason': data['done_reason'],
                'response_sha256': transport['response_sha256'], 'http_seconds': transport['elapsed_seconds']})
        save_new(path/'call-audit.json', {'source': source.identity, 'calls': call_rows,
                                        'independent_history_and_trace_isolation_check': True})
        timings = [r['total_duration']/1e9 for r in raw if 'total_duration' in r]
        metrics = mechanical_report(source)
        save_new(path/'mechanics-audit.json', metrics)
        root_rows = []
        for root in source.protocol.roots:
            nodes = [n for n in source.nodes if n.root == root.name]
            valid = [n for n in nodes if n.id in source.turns]
            target = [n for n in nodes if 25 <= n.turn <= 30]
            root_rows.append({'root': root.name, 'model': root.x_model, 'valid_messages': len(valid),
                'first_invalid': [{'node': n.id, 'turn': n.turn, 'reason': state.outcomes[n.id][1].get('reason')}
                                  for n in nodes if state.outcomes[n.id][0] == 'turn_invalid'],
                'available_window_targets': [n.id for n in target if n.id in source.turns],
                'unavailable_window_targets': [n.id for n in target if n.id not in source.turns]})
        review = None
        if read_json(source.protocol.document_json)['schema'] == 'behaviorlab.protocol/3':
            review = create_packet(path, base/(job['name']+'-review'), seed=9150904)
        rows.append({'job': job['name'], 'source': source.identity, 'attempts': len(state.requests),
            'valid_messages': len(source.turns), 'outcomes': dict(Counter(k for k, _ in state.outcomes.values())),
            'server_duration_seconds': sum(timings), 'max_input_tokens': max(r['prompt_eval_count'] for r in raw),
            'minimum_context_headroom': min(r['context_headroom'] for r in call_rows),
            'max_generated_tokens': max(r['eval_count'] for r in raw),
            'messages_with_trace': sum(bool(r['message'].get('thinking')) for r in raw),
            'above_150_words': sum(r['metrics']['above_150_words'] for r in metrics['rows'] if r['metrics']),
            'roots': root_rows, 'review_packet': review})
    require(total <= freeze['maximum_generation_calls'], 'Total budget exceeded')
    report = {'schema': 'behaviorlab.prompt-qualification-audit/1', 'audited_at': timestamp(),
        'freeze_sha256': sha256((base/'freeze.json').read_bytes()), 'maximum_generation_calls': freeze['maximum_generation_calls'],
        'actual_generation_attempts': total, 'jobs': rows, 'main_pilot_enabled': False,
        'semantic_status': 'Unrated here; attributed review is a separate sidecar. No automatic semantic classifier.',
        'technical_scope': 'Per-call saved native render/tokenizer evidence checked against generation prompt counts. No captured generation input IDs or final sampler telemetry.'}
    save_new(base/'technical-audit.json', report)
    print(read_json((base/'technical-audit.json').read_text()))


if __name__ == '__main__': main()
