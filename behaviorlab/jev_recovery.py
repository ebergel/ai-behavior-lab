"""Explicitly released recovery of a stopped intact-window qualification.

Original attempts remain immutable. Each recovery item gets one new attempt;
completed original items are referenced, never copied as new dispatch records.
"""
import argparse
import json
from pathlib import Path
import time

from .common import fingerprint, require, sha256
from .jev_atlas import read_record, write_record, now, locked, MAX_INPUT, PRICE
from .jev_corpus import qualification_plans, run_qualification, summarize_qualification


def software():
    return sha256(Path(__file__).read_bytes())


def prepare(workspace, original, destination, approval):
    original, destination = Path(original), Path(destination)
    require(not destination.exists(), 'Recovery already frozen')
    store, prior, plans = qualification_plans(workspace, original)
    reserve = MAX_INPUT * PRICE / 1_000_000
    evidence = []; reused = []; unknown = 0; spent = 0; started = 0
    newplans = []; allocations = []; sizes = {}
    for variant, plan in plans.items():
        rows = store.results(plan); pending = []
        for row in rows:
            if row['status'] != 'pending':
                started += 1
                for kind in ('requests', 'responses'):
                    path = store.batch_path(plan['id']) / kind / (row['id'] + '.json')
                    record = read_record(path)
                    evidence.append({'path': path.relative_to(Path(workspace)).as_posix(), 'sha256': record['sha256']})
            if row['status'] == 'complete':
                spent += row['cost_usd']
                reused.append({'variant': variant, 'batch': plan['id'], 'item': row['id']})
            else:
                if row['status'] != 'pending':
                    response = read_record(store.batch_path(plan['id']) / 'responses' / (row['id'] + '.json'))
                    require(row['status'] == 'error' and response['http_status'] == 529,
                            'Only the explicitly reviewed HTTP 529 failure is eligible')
                    unknown += 1
                pending.append(row['id'])
        require(pending, 'Each recovery pack must contain pending work')
        new = {k: v for k, v in plan.items() if k != 'sha256'}
        new['id'] = fingerprint(['intact-window-recovery/1', prior['sha256'], variant, pending])[:24]
        new['title'] = 'Intact-window recovery · ' + ('24 broad questions' if variant == 'broad' else '29 detailed questions')
        new['created_at'] = now()
        new['items'] = [i for i in plan['items'] if i['id'] in pending]
        new['budget'] = dict(plan['budget'], max_calls=len(pending))
        new['recovery_origin'] = {'batch': plan['id'], 'plan_sha256': plan['sha256'],
                                  'policy': 'Explicit recovery; original failed evidence is retained. One new attempt per item.'}
        for item in new['items']:
            require(store.payload(new, item) == store.payload(plan, item), 'Recovery changed input')
            sizes[variant + ':' + item['id']] = prior['request_bytes'][variant + ':' + item['id']]
        newplans.append(new); allocations.append({'variant': variant, 'batch': new['id'], 'calls': len(pending)})
    require(unknown == 1 and len(reused) == 1 and started == 2, 'This release requires one success and one reviewed overload')
    total = sum(a['calls'] for a in allocations)
    require(spent + (unknown + total) * reserve <= 2, 'Recovery exceeds authorized aggregate ceiling')
    protocol = {k: v for k, v in prior.items() if k != 'sha256'}
    protocol.update(created_at=now(), allocations=allocations, max_calls=total,
                    plan_hashes={p['id']: fingerprint(p) for p in newplans}, request_bytes=sizes,
                    recovery_of=prior['sha256'])
    release = {'schema': 'behaviorlab.jev-recovery-release/1', 'created_at': now(), 'author': 'Codex',
               'authorized_by': 'researcher', 'approval': approval, 'software_sha256': software(),
               'original_directory': original.relative_to(Path(workspace)).as_posix(),
               'original_qualification_sha256': prior['sha256'], 'qualification_sha256': fingerprint(protocol),
               'prior_evidence': evidence, 'reused': reused, 'prior_calls': started,
               'prior_known_cost_usd': spent, 'prior_unknown_cost_calls': unknown,
               'prior_unknown_reserved_usd': unknown * reserve, 'max_new_calls': total,
               'max_cumulative_calls': total + started, 'authorized_usd_ceiling': 2.0,
               'spacing_seconds': 2, 'policy': 'One new attempt per listed recovery item. Stop on any error or unresolved request. No automatic retries. Original success is reused; original overload retains unknown usage.'}
    write_record(destination / 'qualification.json', protocol)
    write_record(destination / 'release.json', release)
    for plan in newplans: write_record(store.batch_path(plan['id']) / 'plan.json', plan)
    return release


def checked(workspace, destination):
    store, protocol, plans = qualification_plans(workspace, destination)
    release = read_record(Path(destination) / 'release.json')
    require(release['software_sha256'] == software() and release['qualification_sha256'] == protocol['sha256'],
            'Recovery release or software changed')
    _, original, _ = qualification_plans(workspace, Path(workspace) / release['original_directory'])
    require(original['sha256'] == release['original_qualification_sha256'], 'Original qualification changed')
    for receipt in release['prior_evidence']:
        require(read_record(Path(workspace) / receipt['path'])['sha256'] == receipt['sha256'], 'Original attempt changed')
    require(release['max_new_calls'] == protocol['max_calls'] and release['authorized_usd_ceiling'] == 2,
            'Recovery budget changed')
    return store, protocol, plans, release


def summary(workspace, destination):
    store, protocol, plans, release = checked(workspace, destination)
    result = summarize_qualification(workspace, destination)
    result.update(recovery_release_sha256=release['sha256'], original_reused_assessments=len(release['reused']),
                  recovery_calls_started=result['calls_started'], cumulative_calls_started=result['calls_started'] + release['prior_calls'],
                  cumulative_known_cost_usd=result['cost_usd'] + release['prior_known_cost_usd'],
                  prior_unknown_cost_calls=release['prior_unknown_cost_calls'],
                  prior_unknown_reserved_usd=release['prior_unknown_reserved_usd'],
                  effective_complete_assessments=sum(b['complete'] for b in result['batches']) + len(release['reused']),
                  authorized_usd_ceiling=release['authorized_usd_ceiling'])
    result['limitations'].append('Original overloaded attempt retains unknown usage. Recovery comparisons include a later service time; no causal pack-effect claim.')
    return result


def run(workspace, destination, max_calls=None, pause=time.sleep):
    require(max_calls is None or type(max_calls) is int and max_calls > 0, 'Invalid max-calls')
    with locked(Path(destination) / '.recovery.lock', blocking=False):
        sent = 0
        while max_calls is None or sent < max_calls:
            store, protocol, plans, release = checked(workspace, destination)
            rows = [r for p in plans.values() for r in store.results(p)]
            require(not any(r['status'] in ('error', 'unresolved') for r in rows), 'Recovery stopped; no automatic retry')
            if not any(r['status'] == 'pending' for r in rows): break
            charge = release['prior_known_cost_usd'] + release['prior_unknown_reserved_usd'] + sum(r['cost_usd'] or 0 for r in rows)
            require(charge + MAX_INPUT * PRICE / 1_000_000 <= release['authorized_usd_ceiling'], 'Aggregate budget exhausted')
            pause(release['spacing_seconds'])
            result = run_qualification(workspace, destination, max_calls=1)
            sent += 1
            if result['status'] == 'stopped': break
        return summary(workspace, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'summarize'])
    parser.add_argument('--workspace', default='workspace'); parser.add_argument('--original')
    parser.add_argument('--destination', required=True); parser.add_argument('--approval'); parser.add_argument('--max-calls', type=int)
    args = parser.parse_args()
    if args.action == 'prepare':
        require(args.original and args.approval, 'Provide original qualification and explicit approval')
        result = prepare(args.workspace, args.original, args.destination, args.approval)
    elif args.action == 'run': result = run(args.workspace, args.destination, args.max_calls)
    else:
        result = summary(args.workspace, args.destination)
        filename = 'summary.json' if result['status'] == 'complete' else 'stopped-summary.json'
        write_record(Path(args.destination) / filename, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('pairs', 'prior_evidence')}, indent=2))


if __name__ == '__main__': main()
