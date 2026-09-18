"""Read-only design inventory. Records, branch paths and message exposure stay distinct."""
from collections import Counter, defaultdict
import json
from pathlib import Path

from .common import fingerprint, require, timestamp
from .finder import experiment, model_info
from .topic_atlas import eligible

SCOPES = {'inventory': 'Conversation runs', 'atlas': 'Atlas-eligible runs with text',
          'technical': 'Technical checks', 'unstarted': 'Unstarted run slots'}
AXES = {
    'identity': ('Partner disclosure', ['Anonymous-Full', 'Anonymous-AI', 'Mirror', 'Named models', 'Unknown']),
    'human': ('Human-presence wording', ['Human presence unspecified', 'No human · explicit', 'Unknown']),
    'composition': ('Actual composition', ['Same model', 'Mixed models', 'Single participant', 'Unknown']),
    'participants': ('Regular participants', ['1', '2', '3', 'Unknown']),
    'task': ('Task', ['Open-ended', 'Assigned task', 'Unknown']),
    'external': ('External intervention', ['None recorded', 'Recorded intervention', 'Scheduled · none recorded']),
    'history': ('History policy', ['Full history', 'Recent history', 'Varied by branch', 'Unknown']),
    'exit': ('Exit instruction', ['No exit instruction', 'Exit token offered', 'Unknown']),
    'temperature': ('Requested temperature', []),
    'weights': ('Weight access', ['Open weights', 'Closed weights', 'Mixed', 'Unknown']),
    'model_kind': ('Recorded model type', []),
    'condition': ('Recorded condition', []),
    'block': ('Recorded protocol / source block', []),
}
TECHNICAL_CLASSES = {'cloud_model_assessment', 'cloud_integration_smoke', 'cloud_integration_diagnostic'}
PLAN_PATH = Path(__file__).resolve().parents[1] / 'designs' / 'balanced-replication-v0.2.json'


def settings_for(run, speaker):
    """Per-speaker metadata overrides shared metadata; never invent effective controls."""
    shared = run.get('settings') or {}
    own = (run.get('settings_by_speaker') or {}).get(speaker) or {}
    result = dict(shared.get('decoding') or {})
    result.update(shared)
    result.update(own.get('decoding') or {})
    result.update(own)
    return result


def requested_value(run, roster, field):
    values = [settings_for(run, p['speaker']).get(field) for p in roster]
    if not values or any(v is None for v in values): return 'Unknown'
    labels = sorted({str(v) for v in values})
    return labels[0] if len(labels) == 1 else 'Mixed: ' + ' / '.join(labels)


def project(run):
    exp = run.get('experiment') or experiment(run)
    # Guest events can have an X/Y label; only regular message events count.
    messages = list({m['id']: m for m in run.get('messages', []) if m.get('kind') == 'message'}.values())
    # Match the frozen corpus's presence rule exactly, including whitespace-only
    # returned strings. Presence is not substantive content or a valid outcome.
    visible = [m for m in messages if isinstance(m.get('text'), str) and m['text']]
    unstarted = bool(run.get('unstarted_assessment'))
    category = ('synthetic' if run['kind'] == 'synthetic' else 'unstarted' if unstarted else
                'technical' if run.get('data_class') in TECHNICAL_CLASSES or len(exp['roster']) < 2 else 'inventory')
    children = Counter(m.get('parent') for m in messages if m.get('parent'))
    leaves = len(run.get('leaves') or [])
    branched = leaves > 1 or any(n > 1 for n in children.values())
    # source.sha256 is often the entire campaign, shared by several fresh roots.
    # It must not be used as a root identifier or deduplication key.
    source = run.get('source') or {}
    protocol = source.get('protocol_sha256')
    block = ('Protocol ' + protocol if protocol else
             'Historical · ' + str(run.get('collection_id', 'unknown')) if run['kind'] == 'reference' else
             'Unrecorded protocol · ' + run['id'])
    by_model = Counter((m.get('model') or 'Unknown') for m in visible)
    unavailable = sum(not isinstance(m.get('text'), str) or not m['text'] for m in messages)
    flags = sorted({m.get('status', 'Unknown') for m in messages if m.get('status') not in ('valid', 'recorded')})
    row = dict(id=run['id'], title=run['title'], category=category, kind=run['kind'],
               data_class=run.get('data_class', 'Unknown'), models=exp['models'],
               families=sorted({model_info(m)['developer'] for m in exp['models']}),
               visible=len(visible), positions=len(messages), unavailable=unavailable,
               by_model=dict(by_model), branched=branched, paths=leaves or None,
               multisegment=len(run.get('segments', [])) > 1,
               flagged=bool(flags), flags=flags, capped=any(m.get('status') == 'cap' for m in messages),
               incomplete=not run.get('complete', False), repeated=bool(run.get('repeat_count')),
               no_visible=not visible, whitespace=sum(not m['text'].strip() for m in visible), atlas=bool(eligible(run) and visible),
               source_sha256=source.get('sha256'), protocol_sha256=protocol,
               protocol_block=block, date=run.get('date'), root_basis='Historical run' if run['kind'] == 'reference' else 'Recorded root / slot',
               # No independence certification is inferred from record IDs or seeds.
               independence='Not established by this inventory',
               seed=run.get('settings', {}).get('seed'),
               prompt_sha256=fingerprint(run['prompt']) if run.get('prompt') else None,
               first_message_id=visible[0]['id'] if visible else None,
               dimensions={key: exp.get(key, 'Unknown') for key in AXES})
    weights = {model_info(m)['weights'] for m in exp['models']}
    row['dimensions'].update(condition=run.get('condition', 'Unknown'), block=block,
                             model_kind=run.get('model_kind') or 'Unknown',
                             weights='Unknown' if not weights or 'Unknown' in weights else next(iter(weights)) if len(weights)==1 else 'Mixed',
                             temperature=requested_value(run, exp['roster'], 'temperature'))
    row['requested_top_p'] = requested_value(run, exp['roster'], 'top_p')
    return row


def metrics(rows):
    return {'records': len(rows), 'visible': sum(r['visible'] for r in rows),
            'positions': sum(r['positions'] for r in rows), 'unavailable': sum(r['unavailable'] for r in rows),
            'no_visible': sum(r['no_visible'] for r in rows), 'flagged': sum(r['flagged'] for r in rows),
            'capped': sum(r['capped'] for r in rows), 'incomplete': sum(r['incomplete'] for r in rows),
            'branched': sum(r['branched'] for r in rows), 'multisegment': sum(r['multisegment'] for r in rows),
            'whitespace': sum(r['whitespace'] for r in rows), 'models': len({m for r in rows for m in r['models']}),
            'families': len({f for r in rows for f in r['families'] if f != 'Unknown'})}


def clean_filters(data):
    require(isinstance(data, dict), 'Expected coverage filters')
    allowed = {'scope', 'axis', 'group', 'task', 'row', 'column', 'sort', 'page'}
    require(not set(data) - allowed, 'Unknown coverage filter')
    result = {}
    for key, default, choices in [('scope', 'inventory', SCOPES), ('axis', 'identity', AXES),
                                  ('group', 'model', ('model', 'family')),
                                  ('task', 'all', ('all', 'Open-ended', 'Assigned task', 'Unknown')),
                                  ('sort', 'records', ('records', 'name', 'visible'))]:
        value = data.get(key, default); require(isinstance(value, str) and value in choices, 'Invalid coverage ' + key)
        result[key] = value
    for key in ('row', 'column'):
        value = data.get(key, ''); require(isinstance(value, str) and len(value) <= 500, 'Invalid coverage ' + key)
        result[key] = value
    page = data.get('page', 0)
    require(isinstance(page, int) and not isinstance(page, bool) and 0 <= page <= 10000, 'Invalid coverage page')
    result['page'] = page
    return result


def build_coverage(catalog, filters=None):
    f = clean_filters(filters or {})
    all_rows = [project(r) for r in sorted(catalog.runs.values(), key=lambda r: r['id'])]
    scope_counts = {s: sum(r['atlas'] if s == 'atlas' else r['category'] == s for r in all_rows) for s in SCOPES}
    rows = [r for r in all_rows if (r['atlas'] if f['scope'] == 'atlas' else r['category'] == f['scope'])
            and (f['task'] == 'all' or r['dimensions']['task'] == f['task'])]
    axis = f['axis']; columns = list(AXES[axis][1])
    columns += sorted({r['dimensions'][axis] for r in rows} - set(columns))
    groups = defaultdict(list)
    for r in rows:
        for key in r['models'] if f['group'] == 'model' else r['families']: groups[key].append(r)
    grid = []
    for key, members in groups.items():
        label = model_info(key)['label'] if f['group'] == 'model' else key
        exposure = sum(sum(n for m, n in r['by_model'].items() if
                          (m == key if f['group'] == 'model' else model_info(m)['developer'] == key)) for r in members)
        cells = []
        for col in columns:
            selected = [r for r in members if r['dimensions'][axis] == col]
            cells.append({'value': col, **metrics(selected)})
        grid.append({'key': key, 'label': label, 'records': len(members), 'visible': exposure, 'cells': cells})
    grid.sort(key=lambda r: (r['label'].casefold(), r['key']) if f['sort'] == 'name' else
              (-r[f['sort']], r['label'].casefold(), r['key']))
    selected = [r for r in rows if (not f['row'] or f['row'] in (r['models'] if f['group'] == 'model' else r['families']))
                and (not f['column'] or r['dimensions'][axis] == f['column'])]
    selected.sort(key=lambda r: (r['title'].casefold(), r['id']))
    page = min(f['page'], max(0, (len(selected) - 1) // 20)); f['page'] = page
    # Frozen-vocabulary identity does not require reading any reserved passage.
    plan = json.loads(PLAN_PATH.read_text())
    return {'schema': 'behaviorlab.design-coverage/1', 'generated_at': timestamp(), 'filters': f,
            'scopes': SCOPES, 'scope_counts': scope_counts,
            'axes': {k: v[0] for k, v in AXES.items()}, 'columns': columns,
            'summary': metrics(rows), 'grid': grid, 'selection': metrics(selected),
            'records': selected[page * 20:(page + 1) * 20], 'selected_ids': [r['id'] for r in selected],
            'evidence': rows, 'inventory_sha256': fingerprint(all_rows),
            'omitted_synthetic': sum(r['category'] == 'synthetic' for r in all_rows),
            'plan': plan, 'plan_sha256': fingerprint(plan),
            'notes': ['Runs and planned run slots are inventory units, not certified independent replicates.',
                      'Shared branch nodes occur once; branch paths never multiply the run count.',
                      'A mixed conversation appears under each participating model/family; row totals are not additive.',
                      'Recorded messages here are nonempty returned strings, including whitespace-only output. Presence does not establish substantive content. Guest interventions are excluded.',
                      'Historical blocks group source collections, not identical protocols. Requested settings are not verified effective settings.',
                      'Zero means no matching run or planned slot in this inventory, not a behavioural absence or a planned allocation.',
                      'Historical planned_count may describe returned positions, not the original allocation. Allocated slots are shown only in the new draft.']}
