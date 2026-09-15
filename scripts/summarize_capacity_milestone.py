"""Audit capacity evidence using saved responses; no inference or semantic classifier."""
import argparse
from collections import Counter
from pathlib import Path

from behaviorlab.annotations import mechanical_report, save_new
from behaviorlab.capacity import reconstruct
from behaviorlab.common import fingerprint, read_json, require, sha256, timestamp
from behaviorlab.evidence import completed_campaign
from behaviorlab.journal import read_events


def summarize(base, destination):
    freeze = read_json((base/'freeze.json').read_text())
    require(freeze['schema'] == 'behaviorlab.capacity-freeze/1', 'Wrong capacity freeze')
    for path, digest in freeze['file_sha256'].items():
        require(sha256(Path(path).read_bytes()) == digest, 'Frozen file changed: '+path)
    for path, digest in read_json((base/'historical-journal-hashes.json').read_text()).items():
        require(sha256(Path(path).read_bytes()) == digest, 'Historical journal changed: '+path)
    plan, registries, requests, responses, results = reconstruct(read_events(base/'snapshots/events.jsonl'))
    require(plan == read_json((base/'snapshot-plan.json').read_text()) and len(results) == 6, 'Incomplete snapshot diagnostics')
    pairs = []
    for start in range(0, len(plan['jobs']), 2):
        a,b = plan['jobs'][start:start+2]; pa,pb = requests[a['id']]['preflight'], requests[b['id']]['preflight']
        require(pa['rendered_utf8_sha256'] == pb['rendered_utf8_sha256']
                and pa['prompt_token_ids_sha256'] == pb['prompt_token_ids_sha256'], 'Paired snapshot input differs')
        ta,tb = [read_json(responses[j['id']]['raw_response'])['message']['content'] for j in (a,b)]
        common = 0
        for x,y in zip(ta,tb):
            if x != y: break
            common += 1
        pairs.append({'case':a['matched_group'], 'source':a['source'], 'node':a['source_node'],
            'small_cap':a['request']['options']['num_predict'], 'large_cap':b['request']['options']['num_predict'],
            'small_result':results[a['id']], 'large_result':results[b['id']],
            'same_render_and_tokenization':True, 'same_visible_text':ta==tb, 'common_visible_prefix_characters':common,
            'small_cached_tokens':read_json(responses[a['id']]['raw_response'])['prompt_eval_cached_count'],
            'large_cached_tokens':read_json(responses[b['id']]['raw_response'])['prompt_eval_cached_count']})
    jobs = []; calls = []
    for job in freeze['jobs']:
        path = base/job['name']
        if not path.exists():
            jobs.append({'job':job['name'],'not_run':True,'prerequisite':job['requires']}); continue
        source = completed_campaign(path); state=source.state
        require(not state.retried and len(state.requests) <= job['max_calls'], 'Capacity retry/budget violated')
        rows = []
        for node in source.nodes:
            if node.id not in state.attempts: continue
            attempt=state.attempts[node.id]; saved=state.requests[attempt]; response=state.responses[attempt]
            require(saved['preflight'] == response['transport']['ollama_context'], 'Preflight association differs')
            payload=saved['request']; data=read_json(response['raw_response']); pf=saved['preflight']
            expected=[{'role':'system','content':source.protocol.system}]
            if node.speaker=='X': expected.append({'role':'user','content':source.protocol.opening})
            expected.extend({'role':'assistant' if earlier.speaker==node.speaker else 'user','content':source.turns[earlier.id].content}
                            for earlier in source.nodes if earlier.root==node.root and earlier.turn<node.turn)
            require(payload['messages']==expected, 'Independent visible-history reconstruction failed')
            require(saved['observation']['ollama_files']['content_hash_verified'] is True, 'Unverified files')
            content=data['message']['content']; lines=[line.strip() for line in content.splitlines() if line.strip()]
            suffix=0
            for line in reversed(lines):
                if line != lines[-1]: break
                suffix+=1
            counts=Counter(lines)
            row={'job':job['name'],'node':node.id,'turn':node.turn,'seed':node.seed,
                'input_tokens':pf['input_tokens'],'reported_input_tokens':data['prompt_eval_count'],
                'context_headroom':pf['context_headroom'],'generated_tokens':data['eval_count'],
                'visible_words':len(content.split()),'finish_reason':data['done_reason'],
                'trace_characters':len(data['message'].get('thinking','')),
                'nonempty_lines':len(lines), 'most_frequent_line_count':max(counts.values(),default=0),
                'constant_line_suffix':suffix,'http_seconds':response['transport']['elapsed_seconds']}
            rows.append(row); calls.append(row)
        jobs.append({'job':job['name'],'source':source.identity,'planned':len(source.nodes),'attempts':len(state.requests),
            'valid':len(source.turns),'outcomes':dict(Counter(k for k,_ in state.outcomes.values())),
            'invalid':[p for k,p in state.outcomes.values() if k=='turn_invalid'],
            'above_150_words_valid':sum(len(t.content.split())>150 for t in source.turns.values()),
            'max_input_tokens':max((r['input_tokens'] for r in rows),default=None),
            'minimum_context_headroom':min((r['context_headroom'] for r in rows),default=None),
            'max_generated_tokens':max((r['generated_tokens'] for r in rows),default=None)})
    attempted=len(requests)+sum(j.get('attempts',0) for j in jobs)
    require(attempted<=freeze['maximum_generation_calls'], 'Aggregate capacity budget exceeded')
    passed=all(p['large_result']['invalid_reason'] is None for p in pairs) and all(j.get('valid')==j.get('planned') and not j.get('not_run') for j in jobs)
    result={'schema':'behaviorlab.capacity-audit/1','audited_at':timestamp(),'freeze_sha256':sha256((base/'freeze.json').read_bytes()),
        'maximum_generation_calls':freeze['maximum_generation_calls'],'actual_generation_attempts':attempted,
        'snapshot_pairs':pairs,'jobs':jobs,'calls':calls,'predeclared_technical_pass':passed,'main_pilot_enabled':False,
        'historical_journals_unchanged':True,'frozen_inputs_unchanged':True,
        'technical_scope':'Native render/tokenizer observations and generation count checks, not captured generation input IDs or final samplers.',
        'line_repetition_scope':'Post hoc mechanical description of stripped nonempty lines; not an online stopping rule or semantic classifier.'}
    save_new(destination,result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('directory'); p.add_argument('output'); a=p.parse_args()
    r=summarize(Path(a.directory),Path(a.output))
    print({k:r[k] for k in ['actual_generation_attempts','predeclared_technical_pass','historical_journals_unchanged']})
