"""Read-only topic paths from existing corpus scores and actual source ancestry.

No inference, notebook writes, or validation-packet text is exposed here.
"""
import math
from collections import defaultdict

from .common import require

GROUPS = {'broad': 'Broad domains', 'focused': 'Experiential topics', 'form': 'Conversation forms',
          'stance': 'Stances', 'coverage': 'Coverage checks', 'all': 'All questions'}


def clean_filters(value=None):
    require(value is None or isinstance(value, dict), 'Expected trajectory filters')
    f = dict(model='', identity='', task='', q='', run='', branch='', group='broad',
             topic='broad_cognition', threshold=80, message='', sort='mean', page=0)
    require(not set(value or {}) - set(f), 'Unknown trajectory filter')
    f.update(value or {})
    for k in set(f) - {'threshold', 'page'}:
        require(isinstance(f[k], str) and len(f[k]) <= 500, 'Invalid trajectory filter: ' + k)
    require(f['group'] in GROUPS and f['sort'] in ('mean', 'name', 'onset'), 'Invalid topic display')
    require(type(f['threshold']) is int and f['threshold'] in (50, 80, 90), 'Choose threshold 50, 80 or 90')
    require(type(f['page']) is int and f['page'] >= 0, 'Invalid trajectory page')
    return f


def path_messages(run, leaf):
    """Use the same segment ancestry as the source reader, never concatenate forks."""
    segments = {s['id']: s for s in run['segments']}
    require(leaf in run['leaves'] and leaf in segments, 'Unknown conversation path')
    wanted = set()
    while leaf is not None:
        require(leaf in segments and leaf not in wanted, 'Broken or cyclic segment ancestry')
        wanted.add(leaf); leaf = segments[leaf].get('parent')
    seen = set(); result = []
    for m in run['messages']:
        if m.get('segment') in wanted and m['id'] not in seen:
            seen.add(m['id']); result.append(m)
    return result


def score_summary(values, threshold):
    """Missing/event cells break streaks and cannot establish a below-score interval."""
    observed = [(i, v) for i, v in enumerate(values) if v is not None]
    first = None; streak = longest = returns = above = 0
    prior_high = False; below_after_high = False
    for i, v in enumerate(values):
        if v is None:
            streak = 0; prior_high = False; below_after_high = False
        elif v >= threshold:
            if first is None: first = i + 1
            if prior_high and below_after_high: returns += 1
            prior_high = True; below_after_high = False
            streak += 1; longest = max(longest, streak); above += 1
        else:
            streak = 0
            if prior_high: below_after_high = True
    return {'observed': len(observed), 'above': above, 'mean': sum(v for _, v in observed)/len(observed) if observed else None,
            'first_crossing': first, 'longest_streak': longest, 'reentries': returns}


def build_trajectories(catalog, dataset, filters=None):
    f = clean_filters(filters); by_run = defaultdict(list)
    for row in dataset['rows']:
        if row.get('Inventory category') == 'conversation': by_run[row['Conversation ID']].append(row)
    # Keep whole reserved lineages out, including neighbouring context. This view is
    # for discovery; the independent reading packet has a different workflow.
    reserved = {rid for rid, rows in by_run.items() if any(r.get('Reading split') == 'reference_reserved' for r in rows)}
    candidates = []
    for rid, rows in by_run.items():
        run = catalog.runs.get(rid)
        if run is None or rid in reserved: continue
        exp = run.get('experiment', {})
        candidates.append({'id': rid, 'title': run['title'], 'models': exp.get('models', run['models']),
                           'identity': exp.get('identity', 'Unknown'), 'task': exp.get('task', 'Unknown'),
                           'condition': run.get('condition', 'Unknown'), 'paths': len(run['leaves']),
                           'passages': len(rows)})
    facets = {'models': sorted({m for c in candidates for m in c['models']}),
              'identities': sorted({c['identity'] for c in candidates}), 'tasks': sorted({c['task'] for c in candidates})}
    records = [c for c in candidates if (not f['model'] or f['model'] in c['models'])
               and (not f['identity'] or c['identity'] == f['identity'])
               and (not f['task'] or c['task'] == f['task'])
               and (not f['q'] or f['q'].casefold() in (' '.join([c['title'], c['condition'], *c['models']])).casefold())]
    records.sort(key=lambda c: (c['title'].casefold(), c['id']))
    f['page'] = min(f['page'], max(0, (len(records)-1)//20))
    available = {c['id'] for c in records}
    if f['run'] and f['run'] not in available:
        # Explicit stale/filtered/reserved selection is not silently substituted.
        selected = None
    else:
        selected = f['run'] or (records[f['page']*20]['id'] if records else None)
        f['run'] = selected or ''
    result = {'schema': 'behaviorlab.topic-trajectories/1', 'filters': f, 'groups': GROUPS, 'facets': facets,
              'records': records[f['page']*20:(f['page']+1)*20], 'matching_records': len(records),
              'discovery_records': len(candidates), 'reserved_records': len(reserved),
              'dataset_fingerprint': dataset['fingerprint'], 'detail': None,
              'method': 'Existing JEV model scores along one actual conversation path. Threshold crossings describe scores, '
                        'not confirmed topic adoption or subjective experience. Missing scores and external events break streaks '
                        'and re-entry comparisons. Independent semantic validation is pending. Reserved validation lineages '
                        'are withheld from this discovery view; their text and scores are not returned.'}
    if not selected: return result
    run = catalog.runs[selected]; leaves = run['leaves']
    if f['branch']: require(f['branch'] in leaves, 'Unknown conversation path')
    else: f['branch'] = leaves[0]
    rows = {dataset['passages'][r['__id']]['message_id']: r for r in by_run[selected]}
    topics = [t for t in dataset['topics'] if f['group'] == 'all' or t['group'] == f['group']]
    if f['topic'] not in {t['id'] for t in topics}: f['topic'] = topics[0]['id'] if topics else ''
    positions = []; scores = {t['id']: [] for t in topics}
    for m in path_messages(run, f['branch']):
        row = rows.get(m['id']); p = dataset['passages'].get((row or {}).get('__id'), {})
        regular = m.get('kind') == 'message'
        current = bool(row and p.get('source_sha256') == run['source']['sha256'] and p.get('text') == m.get('text'))
        status = 'External event' if not regular else 'Source changed' if row and not current else 'Scored' if current else 'No score'
        item = {'id': m['id'], 'turn': m.get('turn'), 'speaker': m.get('speaker', ''), 'model': m.get('model', ''),
                'segment': m.get('segment'), 'kind': m.get('kind'), 'quality': m.get('status', 'Unknown'),
                'assessment': status, 'text': m.get('text') if (current or not regular) else None}
        positions.append(item)
        for t in topics:
            v = row.get(t['field']) if current and regular else None
            valid = type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 100
            scores[t['id']].append(v if valid else None)
    summaries = [dict(t, values=scores[t['id']], **score_summary(scores[t['id']], f['threshold'])) for t in topics]
    if f['sort'] == 'mean': summaries.sort(key=lambda t: (-(t['mean'] if t['mean'] is not None else -1), t['title']))
    elif f['sort'] == 'onset': summaries.sort(key=lambda t: (t['first_crossing'] or math.inf, t['title']))
    else: summaries.sort(key=lambda t: t['title'])
    if f['message'] not in {m['id'] for m in positions}: f['message'] = positions[0]['id'] if positions else ''
    result['detail'] = {'id': run['id'], 'title': run['title'], 'models': run['models'], 'experiment': run.get('experiment', {}),
                        'prompt': run.get('prompt'), 'opening': run.get('opening'), 'settings': run.get('settings', {}),
                        'settings_by_speaker': run.get('settings_by_speaker', {}), 'leaves': leaves,
                        'positions': positions, 'topics': summaries, 'source_sha256': run['source']['sha256']}
    return result
