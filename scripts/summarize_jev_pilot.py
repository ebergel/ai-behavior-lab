"""Read saved JEV evidence; never dispatch inference or replace an existing report.

Run from the repository with PYTHONPATH=. python3 scripts/summarize_jev_pilot.py.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics

from behaviorlab.common import require
from behaviorlab.jev_atlas import JevAtlas, read_record, write_record, now


def summarize(workspace, identity):
    store = JevAtlas(workspace); plan = store.plan(identity); rows = store.results(plan)
    complete = [r for r in rows if r['status'] == 'complete']
    require(len(complete) == len(rows), 'Only report a fully resolved batch; preserve partial outcomes separately')
    high = plan['thresholds']['candidate']; low = plan['thresholds']['unlikely']
    topics = {}
    for topic in plan['topics']:
        def p(row): return row['answers']['topic_' + topic]['noul']
        candidates = [r for r in complete if p(r) >= high]
        topics[topic] = {
            'candidate': len(candidates),
            'uncertain': sum(low < p(r) < high for r in complete),
            'unlikely': sum(p(r) <= low for r in complete),
            'literal_hit': sum(bool(r['literal'][topic]) for r in complete),
            'candidate_without_phrase': sum(not r['literal'][topic] for r in candidates),
            'phrase_but_unlikely': sum(bool(r['literal'][topic]) and p(r) <= low for r in complete),
            'candidate_conversations': len({r['run_id'] for r in candidates}),
            'candidate_item_ids': [r['id'] for r in candidates],
        }
    extra = {key: {'candidate': sum(r['answers'][key]['noul'] >= high for r in complete),
                   'uncertain': sum(low < r['answers'][key]['noul'] < high for r in complete),
                   'unlikely': sum(r['answers'][key]['noul'] <= low for r in complete)}
             for key in ('self_inquiry', 'self_assertion', 'outside_dictionary')}
    responses = [read_record(store.batch_path(identity) / 'responses' / (r['id'] + '.json')) for r in complete]
    usage = [json.loads(r['raw_text'])['usage'] for r in responses]
    latencies = [r['elapsed_seconds'] for r in responses]
    return {
        'schema': 'behaviorlab.jev-pilot-summary/1', 'created_at': now(), 'author': 'Codex',
        'batch': identity, 'plan_sha256': plan['sha256'],
        'integration_revision': (store.integration_revision(plan) or {}).get('sha256'),
        'summary': store.summary(plan, rows), 'denominator': len(complete),
        'conversations': len({r['run_id'] for r in complete}),
        'split_counts': dict(Counter(r['split'] for r in complete)),
        'sample_model_combinations': dict(Counter(' + '.join(r['models']) for r in complete)),
        'topics': topics, 'additional_questions': extra,
        'experience_referents': dict(Counter(r['answers']['experience_referent']['choice'] for r in complete)),
        'rounded_response_ids': [r['id'] for r in complete if r.get('validation_note')],
        'input_tokens': sum(u['input_tokens'] for u in usage),
        'output_tokens': sum(u.get('output_tokens', 0) for u in usage),
        'latency_seconds': {'median': statistics.median(latencies), 'min': min(latencies),
                            'max': max(latencies), 'sum': sum(latencies)},
        'scope': 'Descriptive counts in the frozen passage sample. Multi-label assessments overlap. '
                 'No accuracy, calibration, initial-topic preference, or population prevalence estimate. '
                 'The corpus and conversation lengths are imbalanced; sampled messages within conversations are dependent.',
        'human_validation': 'Pending. Codex development readings, when present, are separate attributed observations.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='workspace'); parser.add_argument('--batch', required=True)
    parser.add_argument('--output', required=True); args = parser.parse_args()
    report = summarize(args.workspace, args.batch)
    write_record(Path(args.output), report)
    print(json.dumps({k: report[k] for k in ('summary', 'topics', 'additional_questions', 'input_tokens', 'latency_seconds')}, indent=2))
