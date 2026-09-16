"""Audit seed reuse across a frozen set of requests, including model aliases."""
from collections import defaultdict

from .common import fingerprint, require


def model_key(model):
    # Conservatively identify the same pinned artifact across labels/profiles.
    require(model.digest is not None, 'Seed audit requires pinned model digests')
    return model.digest


def protocol_entries(name, protocol, registry, paired_branches=False):
    require(type(paired_branches) is bool, 'Declare the branch pairing policy')
    return [{'id': name+'/'+n.id, 'model': model_key(registry.model(n.model)), 'seed': n.seed,
             'matched_group': name+'/'+n.root+'/turn-'+str(n.turn) if paired_branches else None}
            for n in protocol.nodes()]


def audit(entries):
    require(len({e['id'] for e in entries}) == len(entries), 'Duplicate seed-audit request IDs')
    groups = defaultdict(list)
    for e in entries:
        require(set(e) == {'id', 'model', 'seed', 'matched_group'}
                and isinstance(e['id'], str) and bool(e['id'])
                and isinstance(e['model'], str) and bool(e['model'])
                and type(e['seed']) is int and 0 <= e['seed'] < 2**31
                and (e['matched_group'] is None or isinstance(e['matched_group'], str) and bool(e['matched_group'])),
                'Invalid seed allocation')
        groups[(e['model'], e['seed'])].append(e)
    collisions = []
    for (model, seed), members in sorted(groups.items()):
        if len(members) < 2:
            continue
        matching = {e['matched_group'] for e in members}
        declared = len(matching) == 1 and None not in matching
        collisions.append({'model': model, 'seed': seed, 'requests': [e['id'] for e in members],
                           'declared_pairing': declared,
                           'matched_group': members[0]['matched_group'] if declared else None})
    return {'schema': 'behaviorlab.seed-audit/1', 'allocation_sha256': fingerprint(entries),
            'requests': len(entries), 'distinct_model_seeds': len(groups), 'collisions': collisions,
            'unexpected_collisions': sum(not r['declared_pairing'] for r in collisions),
            'scope': 'Allocation check only. Equal seeds do not establish identical random draws or independent observations.'}


def require_clean(entries, previous=()):
    current = audit(entries)
    require(current['unexpected_collisions'] == 0, 'Unplanned seed reuse in new allocation')
    old = {(e['model'], e['seed']) for e in previous}
    overlap = [e['id'] for e in entries if (e['model'], e['seed']) in old]
    require(not overlap, 'New allocation overlaps historical model/seed pairs: '+repr(overlap[:5]))
    return dict(current, previous_requests_checked=len(previous), previous_overlap=overlap)
