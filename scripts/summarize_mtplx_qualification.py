"""Offline audit of completed MTPLX engineering campaigns; emits JSON to stdout.

Usage: python3 -m scripts.summarize_mtplx_qualification workspace/qualification
This never contacts a server, replays generations, or edits campaign journals.
"""
import argparse
from pathlib import Path
from statistics import median

from behaviorlab.backends import LIVE_BACKEND
from behaviorlab.common import canonical, fingerprint, read_json, require, sha256, timestamp
from behaviorlab.journal import read_events
from behaviorlab.runner import campaign_documents, execute


class OfflineBackend:
    identity = LIVE_BACKEND
    def verify(self, model):
        raise AssertionError('Offline audit cannot verify a live service or make new calls')
    def generate(self, payload, model):
        raise AssertionError('Offline audit cannot generate')


def summarize(directory):
    directory = Path(directory)
    journal = directory / 'events.jsonl'
    before = journal.read_bytes()
    events = read_events(journal)
    protocol, registry, state = campaign_documents(events)
    require(state.complete, 'Audit requires a completed campaign')
    result = execute(directory, backend=OfflineBackend())
    require(journal.read_bytes() == before, 'Completed audit altered journal')
    calls = []
    for request in state.requests.values():
        response = state.responses[request['attempt_id']]
        data = read_json(response['raw_response'])
        c = response['transport']['mtplx']['capture']
        obs, out = c['observability'], c['outcome']
        stats = data.get('mtplx_stats', {})
        usage = data['usage']
        kind, outcome = state.outcomes[request['node_id']]
        calls.append({'node': request['node_id'], 'backend': request['model_identity']['backend'],
            'history': request['history_policy'], 'request_id': data['id'],
            'thinking_requested': request['request']['enable_thinking'],
            'thinking_effective': obs['request_enable_thinking'],
            'cache_requested': request['request']['metadata']['cache_mode'],
            'cache_bypassed': obs['request_session_bank_bypass'],
            'session_restore_mode': c['session_restore_mode'],
            'cached_tokens': usage.get('prompt_tokens_details', {}).get('cached_tokens', 0),
            'prompt_tokens': usage['prompt_tokens'], 'completion_tokens': usage['completion_tokens'],
            'reasoning_tokens': usage.get('completion_tokens_details', {}).get('reasoning_tokens'),
            'input_token_ids_match': fingerprint(c['prompt_token_ids']) == request['preflight']['prompt_token_ids_sha256'],
            'seed_requested': request['request']['seed'], 'seed_resolved': out['resolved_seed'],
            'attempts': out['attempts'], 'blank_retries': out['blank_retries'],
            'http_seconds': response['transport']['elapsed_seconds'],
            'server_decode_tokens_per_second': stats.get('decode_tok_s'),
            'server_peak_memory_bytes': stats.get('peak_memory_bytes'),
            'finish_reason': data['choices'][0]['finish_reason'],
            'possible_stats_footer': '⚡ **MTPLX TPS:**' in data['choices'][0]['message']['content'],
            'outcome': kind, 'invalid_detail': outcome.get('detail'),
            'capture_sha256': response['transport']['mtplx']['capture_sha256']})
    result.update(directory=directory.name, journal_sha256=sha256(before),
                  offline_replay_preserved_journal=True, calls=calls)
    return result


def compare_cache(cold_directory, cached_directory):
    _, _, cold = campaign_documents(read_events(Path(cold_directory) / 'events.jsonl'))
    _, _, cached = campaign_documents(read_events(Path(cached_directory) / 'events.jsonl'))
    pairs = []
    for node, (_, outcome) in cached.outcomes.items():
        a = cold.requests[cold.attempts[node]]['request']
        b = cached.requests[cached.attempts[node]]['request']
        require(a['metadata'] == {'cache_mode': 'off'} and b['metadata'] == {'cache_mode': 'auto'},
                'Expected an explicit cache off/auto comparison')
        data = read_json(cached.responses[cached.attempts[node]]['raw_response'])
        pairs.append({'node': node,
            'request_except_cache_identical': {k: v for k, v in a.items() if k != 'metadata'} ==
                                             {k: v for k, v in b.items() if k != 'metadata'},
            'visible_content_identical': cold.outcomes[node][1].get('content') == outcome.get('content'),
            'reasoning_identical': cold.outcomes[node][1].get('thinking') == outcome.get('thinking'),
            'cached_tokens': data['usage'].get('prompt_tokens_details', {}).get('cached_tokens', 0)})
    return {'pairs': pairs, 'matched_requests': sum(p['request_except_cache_identical'] for p in pairs),
            'different_visible_outputs_at_matched_requests': sum(p['request_except_cache_identical'] and
                not p['visible_content_identical'] for p in pairs),
            'scope': 'Same root/turn seeds and explicit controls except cache policy. Later histories may diverge. '
                     'Not a distribution-equivalence or mechanism test.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    args = parser.parse_args()
    base = Path(args.directory)
    campaigns = [summarize(p.parent) for p in sorted(base.glob('*/events.jsonl'))]
    require(campaigns, 'No campaigns found')
    calls = [c for p in campaigns for c in p['calls']]
    speeds = [c['server_decode_tokens_per_second'] for c in calls if c['server_decode_tokens_per_second'] is not None]
    report = {'schema': 'behaviorlab.mtplx-qualification-report/1', 'created_at': timestamp(),
              'data_class': 'local_engineering_inference_not_behavioral_findings',
              'campaigns': campaigns, 'total_generation_calls': len(calls),
              'total_committed': sum(p['committed_turns'] for p in campaigns),
              'total_invalid': sum(p['invalid_turns'] for p in campaigns),
              'max_prompt_tokens': max(c['prompt_tokens'] for c in calls),
              'max_completion_tokens': max(c['completion_tokens'] for c in calls),
              'max_server_peak_memory_bytes': max(c['server_peak_memory_bytes'] or 0 for c in calls),
              'total_generation_http_seconds': sum(c['http_seconds'] for c in calls),
              'median_server_decode_tokens_per_second': median(speeds) if speeds else None,
              'cache_hit_calls': sum(c['cached_tokens'] > 0 for c in calls),
              'all_rendered_inputs_match': all(c['input_token_ids_match'] for c in calls),
              'any_stats_footer': any(c['possible_stats_footer'] for c in calls),
              'timing_scope': 'Short engineering calls; HTTP timing excludes artifact verification and tokenizer preflight. Not a sustained benchmark.'}
    if (base / 'history').is_dir() and (base / 'cached-history').is_dir():
        report['cache_comparison'] = compare_cache(base / 'history', base / 'cached-history')
    print(canonical(report))


if __name__ == '__main__':
    main()
