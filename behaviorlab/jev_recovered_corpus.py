"""Offline corpus freeze including an explicitly recovered qualification.

The unamended preparation is retained under initial-plan/. The final plan adds
checksum-verified reuse of the original successful attempt, not another call.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path

from .common import fingerprint, require, sha256
from .jev_atlas import read_record, write_record, now, MAX_INPUT, PRICE
from .jev_corpus import freeze_corpus
from .jev_recovery import checked


def freeze(workspace, catalog, coverage, recovery, destination):
    destination = Path(destination)
    require(not destination.exists(), 'Recovered corpus already frozen')
    store, protocol, plans, release = checked(workspace, recovery)
    summary = read_record(Path(recovery) / 'summary.json')
    require(summary['status'] == 'complete' and summary['recovery_release_sha256'] == release['sha256'],
            'Recovered qualification must be complete')
    require(summary['effective_complete_assessments'] == protocol['max_calls'] + len(release['reused']),
            'Effective assessment count differs')
    freeze_corpus(workspace, catalog, coverage, recovery, destination / 'initial-plan')
    base = read_record(destination / 'initial-plan/plan.json')
    reference = read_record(destination / 'initial-plan/reference-packet.json')
    plan = {k: v for k, v in base.items() if k != 'sha256'}
    added = []; lineages = set()
    for reused in release['reused']:
        prior = store.plan(reused['batch'])
        row = next(r for r in store.results(prior) if r['id'] == reused['item'])
        require(row['status'] == 'complete', 'Original reuse result is incomplete')
        target = next(t for t in plan['targets'] if t['id'] == reused['item'])
        variant = reused['variant']; request = target['requests'][variant]
        require('reuse' not in request, 'Request already reused')
        payload = store.payload({'model': plan['model'], 'questions': plan['packs'][variant]['questions']}, target)
        path = store.batch_path(prior['id'])
        req = read_record(path / 'requests' / (row['id'] + '.json'))
        response = read_record(path / 'responses' / (row['id'] + '.json'))
        require(req['payload'] == payload and fingerprint(payload) == request['payload_sha256'],
                'Original reuse requires identical full request input')
        receipt = {'batch': prior['id'], 'item': row['id'], 'request_sha256': req['sha256'],
                   'response_sha256': response['sha256']}
        request['reuse'] = receipt; added.append(receipt); lineages.add(target['lineage'])
        for scenario, ratio in summary['empirical_tokens_per_request_byte'][variant].items():
            plan['budget']['usage_based_forecast_usd'][scenario] -= request['bytes'] * ratio * PRICE / 1_000_000
    require(not lineages & {i['lineage'] for i in reference['items']}, 'Reused result overlaps reserved reference lineage')
    for target in plan['targets']:
        if target['lineage'] in lineages: target['split'] = 'development'
    plan['counts']['by_split'] = dict(Counter(t['split'] for t in plan['targets']))
    plan['counts']['reuse_requests'] += len(added); plan['counts']['new_calls'] -= len(added)
    plan['budget']['max_new_calls'] = plan['counts']['new_calls']
    plan['budget']['usd_ceiling'] = math.ceil(plan['counts']['new_calls'] * MAX_INPUT * PRICE / 10000) / 100
    plan.update(created_at=now(), preparation_revision='recovered-original-reuse/1',
                initial_plan_sha256=base['sha256'], recovery_release_sha256=release['sha256'],
                additional_reuse_receipts=added, preparation_software_sha256=sha256(Path(__file__).read_bytes()))
    write_record(destination / 'reference-packet.json', {k: v for k, v in reference.items() if k != 'sha256'})
    write_record(destination / 'plan.json', plan)
    return {k: plan[k] for k in ('status', 'counts', 'budget')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='workspace')
    parser.add_argument('--coverage', default='workspace/jev-atlas/coverage-20260917-v2')
    parser.add_argument('--recovery', required=True); parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    from .explorer import Catalog
    print(json.dumps(freeze(args.workspace, Catalog(args.workspace), args.coverage, args.recovery, args.destination), indent=2))


if __name__ == '__main__': main()
