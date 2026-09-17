"""Fixed question packs for intact windows; bounded qualification and corpus freeze.

The corpus manifest is a prepared research artifact, not an executable allocation.
Only the separate, at-most-60-call long-window qualification can dispatch here.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics

from .common import canonical, fingerprint, require, sha256
from .jev_atlas import (JevAtlas, MODEL, ENDPOINT, PRICE, MAX_INPUT, locked, now,
                        read_record, write_record, software_identity)
from .jev_coverage import build_inventory
from .topic_atlas import matches

SOURCE_BATCH = '7f665a93c90cb1c2e1253d36'
PACKS = {'broad': ['broad'], 'detail': ['focused', 'form', 'stance', 'coverage']}
SEED = 'jev-corpus-fixed-packs-20260917-v1'


def software():
    return {name: sha256(Path(__file__).with_name(name).read_bytes())
            for name in ('jev_corpus.py', 'jev_coverage.py', 'common.py', 'topic_atlas.py')}


def packs_for(source):
    packs = {}
    for name, groups in PACKS.items():
        entries = [t for t in source['dictionary'] if t['group'] in groups]
        ids = {'topic_' + t['id'] for t in entries}
        packs[name] = {'dictionary': entries,
                       'questions': {k: v for k, v in source['questions'].items() if k in ids}}
    keys = [k for pack in packs.values() for k in pack['questions']]
    require(len(keys) == len(set(keys)) and set(keys) == set(source['questions']),
            'Packs must partition every frozen question exactly once')
    require(all(p['questions'] for p in packs.values()), 'Empty question pack')
    return packs


def checked_sources(workspace, catalog, coverage, source_batch):
    source = JevAtlas(workspace).plan(source_batch)
    prior = read_record(Path(coverage) / 'inventory.json')
    inventory, items = build_inventory(catalog)
    require(fingerprint(inventory) == prior['sha256'], 'Corpus changed since coverage inventory; freeze a new revision')
    return source, prior, items


def prepare_qualification(workspace, catalog, coverage, destination, source_batch=SOURCE_BATCH):
    destination = Path(destination)
    require(not destination.exists(), 'Qualification already frozen; do not overwrite')
    store = JevAtlas(workspace)
    source, inventory, items = checked_sources(workspace, catalog, coverage, source_batch)
    packs = packs_for(source)
    long_ids = sorted(t['id'] for t in inventory['targets'] if t['visible'] and t['window_bytes'] > 18000)
    controls = [i['id'] for i in source['items'] if i['sampling_stratum'] == 'root_sample'][:12]
    require(not set(long_ids) & set(controls), 'Control and long-window sets overlap')
    selected = long_ids + controls
    require(0 < 2 * len(selected) <= 60, 'Qualification exceeds fixed 60-call capacity')
    plans = []; allocations = []; sizes = {}
    for variant, pack in packs.items():
        identity = fingerprint([SEED, inventory['sha256'], source['sha256'], variant, selected])[:24]
        frozen = []
        for iid in selected:
            item = dict(items[iid], sampling_stratum='long_window' if iid in long_ids else 'matched_control')
            item['literal'] = {t['id']: matches(item['text'], t['variants'])
                               for t in pack['dictionary'] if t.get('variants')}
            payload = store.payload({'model': MODEL, 'questions': pack['questions']}, item)
            size = len(canonical(payload).encode())
            require(size < 60000, 'An intact window still exceeds the unchanged byte screen')
            frozen.append(item); sizes[variant + ':' + iid] = size
        plan = {k: source[k] for k in ('schema', 'model', 'endpoint', 'dictionary_origin',
                    'dictionary_version', 'topic_groups', 'thresholds', 'coverage_summary')}
        plan.update(id=identity, created_at=now(), author='Codex',
            title='Intact-window qualification · ' + ('24 broad questions' if variant == 'broad' else '29 detailed questions'),
            software_sha256=software_identity(), cohort='all', dictionary=pack['dictionary'],
            dictionary_sha256=fingerprint(pack['dictionary']), topics=[t['id'] for t in pack['dictionary']],
            questions=pack['questions'], items=frozen, design='intact-window-qualification/1',
            method='Technical qualification of fixed question packs with intact target/context; development, not semantic validation.',
            sampling={'seed': SEED, 'method': 'All visible windows above the old 18,000-byte screen, plus the first twelve root controls from the completed 53-question qualification.',
                'eligible_passages': len(inventory['targets']), 'requested': len(frozen), 'excluded': [],
                'split_rule': 'All qualification targets and their lineages are development.',
                'context_policy': 'Identical full target and two actual preceding evidence events in both packs. No text chunking, truncation, summarization or maximum-score recombination.'},
            budget={'max_calls': len(frozen), 'usd_ceiling': .30, 'usd_per_million_input': PRICE,
                'reserved_input_tokens_per_call': MAX_INPUT, 'price_checked': '2026-09-17',
                'policy': 'Stop both packs on any failure or unresolved request. No automatic retry or replacement.'})
        plans.append(plan); allocations.append({'variant': variant, 'batch': identity, 'calls': len(frozen)})
    protocol = {'schema': 'behaviorlab.jev-intact-window-qualification/1', 'created_at': now(),
        'author': 'Codex', 'source_batch': source_batch, 'source_plan_sha256': source['sha256'],
        'inventory_sha256': inventory['sha256'], 'software_sha256': software(),
        'allocations': allocations, 'plan_hashes': {p['id']: fingerprint(p) for p in plans},
        'selected_targets': selected, 'long_targets': long_ids, 'control_targets': controls,
        'max_calls': 2 * len(selected), 'usd_ceiling': .60, 'request_bytes': sizes,
        'acceptance': 'All allocated responses validate, preserve exact target/context and partition questions exactly. Compare available full-pack scores descriptively. No semantic-accuracy or pack-invariance claim.',
        'failure_policy': 'Stop aggregate at first failed or unresolved request; retain evidence and never retry automatically.'}
    write_record(destination / 'qualification.json', protocol)
    for plan in plans: write_record(store.batch_path(plan['id']) / 'plan.json', plan)
    return protocol


def qualification_plans(workspace, destination):
    store = JevAtlas(workspace); protocol = read_record(Path(destination) / 'qualification.json')
    require(protocol['software_sha256'] == software(), 'Qualification software changed after freeze')
    require(protocol['max_calls'] == sum(a['calls'] for a in protocol['allocations']) <= 60 and
            protocol['usd_ceiling'] == .60, 'Aggregate budget differs')
    plans = {}
    for a in protocol['allocations']:
        p = store.plan(a['batch'])
        require(p['sha256'] == protocol['plan_hashes'][p['id']] and len(p['items']) == a['calls'], 'Frozen plan differs')
        plans[a['variant']] = p
    require(sum(p['budget']['usd_ceiling'] for p in plans.values()) <= protocol['usd_ceiling'], 'Pack budget exceeds aggregate')
    return store, protocol, plans


def run_qualification(workspace, destination, max_calls=None):
    from .jev_runner import execute
    with locked(Path(destination) / '.qualification.lock', blocking=False):
        store, protocol, plans = qualification_plans(workspace, destination)
        require(max_calls is None or type(max_calls) is int and max_calls > 0, 'max-calls must be positive')
        for p in plans.values():
            require(not any(r['status'] in ('error', 'unresolved') for r in store.results(p)),
                    'Aggregate stopped on failed/unresolved evidence; no retry')
        remaining = max_calls
        for p in plans.values():
            if remaining is not None and remaining <= 0: break
            before = sum(r['status'] != 'pending' for r in store.results(p))
            result = execute(workspace, p['id'], max_calls=remaining)
            if remaining is not None: remaining -= result['started'] - before
            if result['failed']: return {'status': 'stopped', 'batch': p['id'], 'result': result}
        return summarize_qualification(workspace, destination)


def summarize_qualification(workspace, destination):
    store, protocol, plans = qualification_plans(workspace, destination)
    source = store.plan(protocol['source_batch'])
    require(source['sha256'] == protocol['source_plan_sha256'], 'Source plan differs')
    old = {r['id']: r for r in store.results(source)}; pairs = []; usage = Counter(); ratios = {}; packs = []
    for variant, plan in plans.items():
        rows = store.results(plan); packs.append(store.summary(plan, rows)); ratios[variant] = []
        for r in rows:
            if r['status'] != 'complete': continue
            response = read_record(store.batch_path(plan['id']) / 'responses' / (r['id'] + '.json'))
            raw = json.loads(response['raw_text']); usage.update(raw['usage'])
            size = protocol['request_bytes'][variant + ':' + r['id']]
            ratios[variant].append(raw['usage']['input_tokens'] / size)
            prior = old.get(r['id'])
            if prior and prior['status'] == 'complete':
                for key, value in r['answers'].items():
                    earlier = prior['answers'][key]['noul']; current = value['noul']
                    pairs.append({'item_id': r['id'], 'stratum': r['sampling_stratum'], 'question': key,
                        'full_pack': earlier, 'fixed_pack': current, 'difference': current - earlier})
    complete = all(p['status'] == 'complete' for p in packs)
    return {'schema': 'behaviorlab.jev-intact-window-summary/1', 'created_at': now(), 'author': 'Codex',
        'qualification_sha256': protocol['sha256'], 'status': 'complete' if complete else 'incomplete',
        'batches': packs, 'calls_started': sum(p['started'] for p in packs),
        'cost_usd': sum(p['cost_usd'] for p in packs), 'usage': dict(usage), 'pairs': pairs,
        'comparison': {'pairs': len(pairs), 'targets': len({p['item_id'] for p in pairs}),
            'mean_absolute_difference': statistics.mean(abs(p['difference']) for p in pairs) if pairs else None,
            'maximum_absolute_difference': max((abs(p['difference']) for p in pairs), default=None),
            'crossings_080': sum((p['full_pack'] >= .8) != (p['fixed_pack'] >= .8) for p in pairs)},
        'empirical_tokens_per_request_byte': {k: {'median': statistics.median(v), 'maximum': max(v)}
            for k, v in ratios.items() if v},
        'limitations': ['Technical qualification is not semantic validation or a universal context-length guarantee.',
            'Historical full-pack comparisons cannot isolate pack effects from service/time variation.',
            'Neither candidate counts nor mean scores are measured prevalence.']}


def freeze_corpus(workspace, catalog, coverage, qualification, destination):
    destination = Path(destination)
    require(not destination.exists(), 'Corpus already frozen; do not overwrite')
    store, protocol, qplans = qualification_plans(workspace, qualification)
    summary = read_record(Path(qualification) / 'summary.json')
    require(summary['status'] == 'complete' and summary['qualification_sha256'] == protocol['sha256'],
            'Live qualification must complete before corpus freeze')
    source, inventory, items = checked_sources(workspace, catalog, coverage, protocol['source_batch'])
    require(source['sha256'] == protocol['source_plan_sha256'], 'Qualification source differs')
    packet = read_record(Path(coverage) / 'reading-packet.json'); packs = packs_for(source)
    dev = set(packet['development_lineages']) | {i['lineage'] for p in qplans.values() for i in p['items']}
    # Conservatively exclude every earlier assessment lineage from a newly reserved reference pool.
    exposed = set(dev)
    for pfile in sorted((store.root / 'batches').glob('*/plan.json')):
        previous = read_record(pfile)
        for i in previous['items']:
            if i['id'] in items: exposed.add(items[i['id']]['lineage'])
    pool = sorted({t['lineage'] for t in inventory['targets'] if t['category'] == 'conversation' and t['visible']} - exposed,
                  key=lambda x: fingerprint([SEED, 'reference-root', x]))
    reserved = set(pool[:60]); target_rows = []; calls = 0; reused = 0; max_bytes = 0; forecasts = Counter()
    qrows = {variant: {r['id']: r for r in store.results(p)} for variant, p in qplans.items()}
    for t in inventory['targets']:
        if not t['visible']: continue
        item = items[t['id']]
        split = 'development' if t['lineage'] in dev else 'reference_reserved' if t['lineage'] in reserved else 'analysis'
        target = dict(item, split=split, inventory_category=t['category'], prior_flagged=t['prior_flagged'],
            prior_unavailable=t['prior_unavailable'], window_bytes=t['window_bytes'], requests={})
        for variant, pack in packs.items():
            payload = store.payload({'model': MODEL, 'questions': pack['questions']}, item)
            size = len(canonical(payload).encode()); max_bytes = max(max_bytes, size)
            require(size < 60000, 'Corpus window exceeds qualified fixed-pack byte policy; no silent omission')
            request = {'payload_sha256': fingerprint(payload), 'bytes': size}
            prior = qrows[variant].get(item['id'])
            if prior:
                require(prior['status'] == 'complete', 'Incomplete reuse source')
                qplan = qplans[variant]
                raw_req = read_record(store.batch_path(qplan['id']) / 'requests' / (item['id'] + '.json'))
                require(raw_req['payload'] == payload, 'Reuse requires byte-equivalent canonical request content')
                response = read_record(store.batch_path(qplan['id']) / 'responses' / (item['id'] + '.json'))
                request['reuse'] = {'batch': qplan['id'], 'item': item['id'], 'request_sha256': raw_req['sha256'],
                                    'response_sha256': response['sha256']}; reused += 1
            else:
                calls += 1
                for scenario, ratio in summary['empirical_tokens_per_request_byte'][variant].items():
                    forecasts[scenario] += size * ratio * PRICE / 1_000_000
            target['requests'][variant] = request
        target_rows.append(target)
    reference = []
    for lineage in sorted(reserved):
        options = [t for t in target_rows if t['lineage'] == lineage and t['inventory_category'] == 'conversation']
        target = min(options, key=lambda t: fingerprint([SEED, 'reference-target', t['id']]))
        reference.append({k: target[k] for k in ('id', 'run_id', 'message_id', 'source_sha256', 'text', 'context', 'message_status', 'lineage')})
    # No classifier scores or proposed labels are included in this open-description packet.
    write_record(destination / 'reference-packet.json', {'schema': 'behaviorlab.jev-reference-packet/1',
        'created_at': now(), 'seed': SEED, 'items': reference, 'coding_status': 'pending independent reader',
        'method': 'One hash-ranked target per reserved lineage; no topic enrichment, no model scores. Earlier researcher exposure is unknown. Do not claim blinding without documenting actual reader exposure.'})
    corpus = {'schema': 'behaviorlab.jev-corpus-plan/1', 'created_at': now(), 'author': 'Codex',
        'status': 'prepared_not_dispatched', 'seed': SEED, 'model': MODEL, 'endpoint': ENDPOINT,
        'source_plan_sha256': source['sha256'], 'qualification_sha256': protocol['sha256'],
        'qualification_summary_sha256': summary['sha256'], 'inventory_sha256': inventory['sha256'],
        'software_sha256': software(), 'runner_software_sha256': software_identity(),
        'packs': packs, 'thresholds': source['thresholds'], 'targets': target_rows,
        'inventory_totals': inventory['totals'], 'unavailable_positions': [t for t in inventory['targets'] if not t['visible']],
        'counts': {'visible_targets': len(target_rows), 'by_category': dict(Counter(t['inventory_category'] for t in target_rows)),
            'by_split': dict(Counter(t['split'] for t in target_rows)), 'logical_requests': 2 * len(target_rows),
            'reuse_requests': reused, 'new_calls': calls, 'max_request_bytes': max_bytes,
            'reference_lineages': len(reserved), 'reference_targets': len(reference)},
        'budget': {'max_new_calls': calls, 'usd_ceiling': math.ceil(calls * MAX_INPUT * PRICE / 10000) / 100,
            'usd_per_million_input': PRICE, 'reserved_input_tokens_per_call': MAX_INPUT,
            'usage_based_forecast_usd': dict(forecasts), 'price_checked': '2026-09-17',
            'forecast_method': 'Sum new request bytes times the observed median / maximum token-per-byte ratio for each pack. Descriptive scenarios, not guaranteed upper bounds. Reserve uses 64,000 tokens per call.'},
        'analysis_policy': {'primary': 'Visible participant targets in eligible conversation records; category counts above are authoritative.',
            'technical': 'Technical/short targets assessed but reported separately.',
            'unavailable': 'No inferred negatives. Unavailable positions retain source/status and leave score denominators.',
            'quality': 'Retain cap/after-cap and prior-quality flags; display all-visible and clean-history sensitivity views separately.',
            'lineage': 'Shared branch nodes counted once. Exact transcript-structure groups permit an equal-lineage sensitivity view; independence of historical roots is not established.',
            'message_view': 'One target has one score per question, joined by exact target identity across the two packs.',
            'conversation_view': 'Any-candidate and within-conversation mean are descriptive, length-sensitive summaries; neither establishes preference.',
            'model_view': 'Attribute messages to actual speakers via source records, not every model in the conversation; separate conditions and missing metadata.',
            'evaluation': 'Independent reader and rubric coding remain pending. Reserved lineages were not selected by JEV scores. No calibrated prevalence claim.',
            'thresholds': 'Keep continuous probabilities; report threshold sensitivity at 0.5, 0.8 and 0.9 without choosing after outcome inspection.'},
        'failure_policy': 'One aggregate ledger; stop on any failed or unresolved request. Sequential dispatch, no automatic retries, no replacement targets. Reuse only checksum-matched completed requests. Further orchestration and dispatch authorization required.'}
    write_record(destination / 'plan.json', corpus)
    return {k: corpus[k] for k in ('status', 'counts', 'budget')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'summarize', 'freeze-corpus'])
    parser.add_argument('--workspace', default='workspace'); parser.add_argument('--coverage', default='workspace/jev-atlas/coverage-20260917-v2')
    parser.add_argument('--qualification', required=True); parser.add_argument('--destination'); parser.add_argument('--max-calls', type=int)
    args = parser.parse_args()
    if args.action in ('prepare', 'freeze-corpus'):
        from .explorer import Catalog
        catalog = Catalog(args.workspace)
    if args.action == 'prepare': result = prepare_qualification(args.workspace, catalog, args.coverage, args.qualification)
    elif args.action == 'run': result = run_qualification(args.workspace, args.qualification, args.max_calls)
    elif args.action == 'summarize':
        result = summarize_qualification(args.workspace, args.qualification)
        require(result['status'] == 'complete', 'Qualification is incomplete')
        write_record(Path(args.qualification) / 'summary.json', result)
    else:
        require(args.destination, 'Provide a new corpus destination')
        result = freeze_corpus(args.workspace, catalog, args.coverage, args.qualification, args.destination)
    print(json.dumps({k: v for k, v in result.items() if k not in ('pairs', 'request_bytes', 'plan_hashes', 'software_sha256')}, indent=2))


if __name__ == '__main__': main()
