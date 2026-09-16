"""Read-only replay, accounting and preservation audit for a closed mixed pilot."""
import argparse
from collections import Counter
from decimal import Decimal
from pathlib import Path
from statistics import median

from behaviorlab.common import canonical, read_json, require, sha256
from behaviorlab.journal import read_events
from behaviorlab.mixed_dialogue import replay, summary
from behaviorlab.mixed_explorer import load_mixed


def check(directory):
    d=Path(directory); original=(d/'events.jsonl').read_bytes(); events=read_events(d/'events.jsonl'); s=replay(events)
    require(s['finished'],'Batch not closed'); h=events[0]['payload']; runs=load_mixed(d)
    prior=h.get('prior_evidence_hashes',{})
    if (d/'preserved-baseline.json').exists():prior=dict(prior,**read_json((d/'preserved-baseline.json').read_text()))
    changed=[p for p,v in prior.items() if not Path(p).exists() or sha256(Path(p).read_bytes())!=v]
    require(not changed,'Prior evidence changed')
    require(all(sha256(Path(p).read_bytes())==v for p,v in h['code_hashes'].items()),'Frozen executable source changed')
    models={}
    for label in ('G','H'):
        tasks=[t for t in s['plan']['tasks'] if t['participant']==label and t['id'] in s['requests']]
        results=[s['results'][t['id']] for t in tasks]; wires=[s['responses'][t['id']] for t in tasks if t['id'] in s['responses']]
        usage=[r['usage'] for r in results if r.get('usage')]
        models[label]={'calls':len(tasks),'cost_usd':str(sum((Decimal(r['cost_usd']) for r in results if r.get('cost_usd') is not None),Decimal(0))),
            'prompt_tokens':sum(u['prompt_tokens'] for u in usage),'completion_tokens':sum(u['completion_tokens'] for u in usage),
            'cached_prompt_tokens':sum((u.get('prompt_tokens_details') or {}).get('cached_tokens') or 0 for u in usage),
            'median_wall_seconds':median(w['transport']['elapsed_seconds'] for w in wires) if wires else None,
            'statuses':dict(Counter(r['status'] for r in results))}
    contexts=[w['transport']['ollama_context'] for w in s['responses'].values() if w['transport'].get('ollama_context')]
    require((d/'events.jsonl').read_bytes()==original,'Read-only audit changed source')
    return dict(summary(s),journal_sha256=sha256(original),journal_head=events[-1]['hash'],plan_sha256=h['plan_sha256'],
        forecast=s['plan']['metadata'].get('forecast'),models=models,prior_artifacts_preserved=len(prior),
        frozen_code_files_verified=len(h['code_hashes']),local_context_checks=len(contexts),
        maximum_local_input_tokens=max((x['input_tokens'] for x in contexts),default=None),
        minimum_local_context_headroom=min((x['context_headroom'] for x in contexts),default=None),
        returned_reasoning=sum(bool(r.get('thinking')) for r in s['results'].values()),
        exact_adjacent_repeats={r['title']:r['repeat_count'] for r in runs},
        run_ids={root['id']:r['id'] for root,r in zip(s['plan']['roots'],runs)})


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('directory',type=Path); a=p.parse_args()
    print(canonical(check(a.directory)))
