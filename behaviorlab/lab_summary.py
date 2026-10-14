"""Read-only lab overview. Inventory membership and assessment coverage are separate."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from .common import fingerprint
from .design_coverage import project
from .jev_atlas import read_record
from . import analysis_corpus, gem_runner, mind_lens_probe, discourse_probe, discourse_portrait_probe
from .topic_atlas import eligible, participant_messages


def percent(numerator, denominator):
    return 100 * numerator / denominator if denominator else None


def source_label(path, workspace=None):
    try:
        return Path(path).relative_to(Path(workspace).resolve()).as_posix() if workspace else Path(path).name
    except ValueError:
        return str(path)


def inventory(catalog):
    """Count unique recorded participant messages, including empty strings and Z speakers."""
    messages = {}; groups = {}; categories = Counter(); empty = Counter(); whitespace = Counter()
    for run in catalog.runs.values():
        kind = 'synthetic' if run['kind'] == 'synthetic' else 'real'
        category = 'unstarted' if run.get('unstarted_assessment') else project(run)['category']; categories[category] += 1
        source = run.get('source', {}); path = str(source.get('path', 'Unknown source'))
        key = (kind, run.get('collection_id', ''), path)
        if key not in groups:
            label = run.get('collection', 'Reference') if run['kind'] == 'reference' else source_label(path, getattr(catalog, 'workspace', None))
            groups[key] = {'id': fingerprint(key)[:24], 'title': label, 'source': path,
                           'kind': kind, 'runs': [], 'models': set(), 'conditions': set(),
                           'categories': Counter(), 'message_keys': set(), 'interventions': 0}
        group = groups[key]; group['categories'][category] += 1
        group['models'].update(run.get('models', [])); group['conditions'].add(run.get('condition', 'Unknown'))
        seen = set(); n = 0
        for message in run.get('messages', []):
            mid = message['id']
            if mid in seen: continue
            seen.add(mid)
            if message.get('kind') != 'message':
                if isinstance(message.get('text'), str): group['interventions'] += 1
                continue
            if run.get('unstarted_assessment') or not isinstance(message.get('text'), str): continue
            identity = (run['id'], mid)
            messages[identity] = {'kind': kind, 'source_sha256': source.get('sha256'), 'text': message['text']}
            group['message_keys'].add(identity); n += 1
            empty[kind] += message['text'] == ''
            whitespace[kind] += bool(message['text']) and not message['text'].strip()
        group['runs'].append({'id': run['id'], 'title': run['title'], 'messages': n,
                              'category': category, 'complete': bool(run.get('complete'))})
    counts = Counter(m['kind'] for m in messages.values()); total = len(messages)
    result = []
    for group in groups.values():
        group['messages'] = len(group.pop('message_keys'))
        group['share_all'] = percent(group['messages'], total)
        group['share_kind'] = percent(group['messages'], counts[group['kind']])
        group['models'] = sorted(group['models']); group['conditions'] = sorted(group['conditions'])
        group['runs'].sort(key=lambda r: (r['title'].casefold(), r['id']))
        group['run_count'] = sum(r['category'] != 'unstarted' for r in group['runs'])
        group['unstarted'] = group['categories']['unstarted']
        result.append(group)
    return {'messages': total, 'real_messages': counts['real'], 'synthetic_messages': counts['synthetic'],
            'real_share': percent(counts['real'], total), 'synthetic_share': percent(counts['synthetic'], total),
            'empty_messages': dict(empty), 'whitespace_messages': dict(whitespace), 'categories': dict(categories),
            'run_count': sum(not r.get('unstarted_assessment') for r in catalog.runs.values()),
            'unstarted': categories['unstarted'], 'experiments': sorted(result, key=lambda g: (-g['messages'], g['title']))}, messages


def assessment(identity, title, samples, message_index, *, questions, wordings=1, packs=1, href=None, source='', requests=None):
    """samples carry completed status for ALL planned question packs/wordings, not merely one score."""
    real = {}; controls = {}; covered = set(); stale = 0
    for sample in samples:
        if sample.get('kind') == 'synthetic':
            key = sample['id']; controls[key] = controls.get(key, True) and bool(sample.get('complete'))
            continue
        key = (sample['run_id'], sample['message_id'])
        previous = real.get(key)
        current = message_index.get(key)
        matches = bool(current and current['kind'] == 'real' and current['source_sha256'] == sample.get('source_sha256')
                       and current['text'] == sample.get('text'))
        real[key] = (bool(sample.get('complete')) and (previous[0] if previous else True),
                     matches and (previous[1] if previous else True))
    for key, (complete, current) in real.items():
        if complete and current: covered.add(key)
        if not current: stale += 1
    completed_real = sum(v[0] for v in real.values()); completed_controls = sum(controls.values())
    denominator = sum(m['kind'] == 'real' for m in message_index.values())
    total = len(real) + len(controls); complete = completed_real + completed_controls
    row = {'id': identity, 'title': title, 'real_sample': len(real), 'controls': len(controls),
           'real_complete': completed_real, 'controls_complete': completed_controls,
           'covered_messages': len(covered), 'coverage': percent(len(covered), denominator),
           'source_runs': len({key[0] for key in real}), 'stale_messages': stale,
           'questions': questions, 'wordings': wordings, 'packs': packs, 'href': href, 'source': source, 'requests': requests,
           'status': 'Source changed' if stale else 'Complete' if total and complete == total else 'Partial / pending' if complete else 'Unassessed'}
    return row, covered


def atlas_inventory(catalog, atlas, studies):
    """Read atlas scope/review counts without treating scans as message assessments."""
    runs = {r['id']: r for r in catalog.runs.values() if eligible(r)}
    dictionary = atlas.dictionary()
    reviews = {r['run_id']: r for r in atlas.reviews(catalog)}
    message_counts = {identity: sum(isinstance(m.get('text'), str) for m in participant_messages(r))
                      for identity, r in runs.items()}
    groups = [('all', 'All atlas-eligible runs', set(runs))]
    groups.extend((s['id'], s['title'], {r['run_id'] for r in s['runs']} & set(runs))
                  for s in studies.all())
    cohorts = []
    from urllib.parse import urlencode
    for identity, title, ids in groups:
        selected = [reviews[i] for i in ids if i in reviews]
        current = [r for r in selected if r['source_current'] and r['dictionary_current']]
        cohorts.append({'id': identity, 'title': title, 'runs': len(ids),
                        'scan_messages': sum(message_counts[i] for i in ids),
                        'opening_reviews_resolved': sum(r['status'] != 'unavailable' for r in current),
                        'opening_reviews_unavailable': sum(r['status'] == 'unavailable' for r in current),
                        'opening_reviews_stale': len(selected) - len(current),
                        'opening_reviews_pending': len(ids) - len(selected),
                        'review_authors': dict(Counter(r['author'] for r in current if r['status'] != 'unavailable')),
                        'href': '#' + urlencode({'view': 'topic-atlas', 'cohort': identity})})
    return {'id': 'topic-atlas', 'title': 'Topic atlas · dictionary matching & opening reviews',
            'status': 'Reading instrument', 'eligible_runs': len(runs),
            'topic_definitions': len(dictionary), 'cohorts': cohorts,
            'included_in_assessment_coverage': False,
            'scope_note': 'All models within the selected cohort. Message counts describe the literal-scan scope; opening outcomes are attributed run-level reviews.'}


def build_summary(workspace, catalog, analysis, gems, jev, topic_atlas=None, studies=None):
    base, message_index = inventory(catalog)
    rows = []; covered = set(); issues = []
    def collect(identity, title, loader):
        try:
            row, keys = loader(); rows.append(row); covered.update(keys)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            issues.append({'id': identity, 'title': title, 'message': str(error)[:240]})
            rows.append({'id': identity, 'title': title, 'status': 'Unavailable', 'error': str(error)[:240]})
    def corpus():
        if not (Path(workspace)/analysis_corpus.EXECUTION/'release.json').exists():
            plan = read_record(Path(workspace)/analysis_corpus.CORPUS/'plan.json')
            return assessment('corpus', 'JEV · Full corpus · prepared',
                              [dict(t, complete=False) for t in plan['targets']], message_index,
                              questions=sum(len(p['questions']) for p in plan['packs'].values()),
                              packs=len(plan['packs']), source=analysis_corpus.CORPUS)
        data = analysis.corpus_dataset(refresh=True)
        samples = [dict(data['passages'][r['__id']], complete=r['Assessment status']=='Complete') for r in data['rows']]
        return assessment('corpus', 'JEV · Full corpus · broad & specific topics', samples, message_index,
                          questions=len(data['topics']), packs=2, href='#view=analysis&analysis=%7B%22dataset%22%3A%22corpus%22%7D', source=analysis_corpus.CORPUS)
    if (Path(workspace)/analysis_corpus.CORPUS/'plan.json').exists():
        collect('corpus', 'JEV · Full corpus', corpus)
    for path in sorted((jev.root/'batches').glob('*/plan.json')):
        def batch(path=path):
            plan = jev.plan(path.parent.name); results = jev.results(plan)
            samples = [dict(r, complete=r['status']=='complete') for r in results]
            return assessment(plan['id'], plan['title'], samples, message_index, questions=len(plan['questions']),
                              href='#view=jev-atlas&batch='+plan['id'], source=str(path.parent.relative_to(workspace)))
        collect(path.parent.name, 'JEV · '+path.parent.name, batch)
    try: batches = gems.batches()
    except (OSError, ValueError, KeyError, TypeError) as error:
        batches=[];issues.append({'id':'gems','title':'Gem Finder','message':str(error)[:240]})
        rows.append({'id':'gems','title':'Gem Finder','status':'Unavailable','error':str(error)[:240]})
    for b in batches:
        def gem(b=b):
            histories, attempts = gem_runner.receipts(b['root'], b['plan'])
            samples = [dict(i, complete=bool(histories.get(i['id'])) and histories[i['id']][-1]['status']=='complete') for i in b['plan']['items']]
            from urllib.parse import urlencode
            import json
            return assessment('gem-'+b['id'], 'Gem Finder · '+b['title'], samples, message_index,
                              questions=len(b['plan']['questions']), requests=len(attempts),
                              href='#'+urlencode({'view':'gems','gem':json.dumps({'batch':b['id']})}), source=str(b['root'].relative_to(workspace)))
        collect('gem-'+b['id'], 'Gem Finder · '+b['title'], gem)
    from . import discourse_corpus
    if (Path(workspace)/discourse_corpus.EXECUTION/'release.json').exists():
        def full_discourse():
            from .discourse_corpus_view import load
            plan,histories,execution,active=load(workspace)
            expected=defaultdict(list)
            for item in plan['items']:expected[item['sample_id']].append(item['id'])
            samples=[dict(t,complete=all(histories.get(i) and histories[i][-1]['status']=='complete' for i in expected[t['id']])) for t in plan['samples']]
            return assessment('mind-discourse-corpus','Mind & discourse · full eligible corpus',samples,message_index,
                              questions=27,wordings=2,requests=execution['attempts'],source=discourse_corpus.ROOT,
                              href='#view=discourse&lens=%7B%22batch%22%3A%22corpus%22%7D')
        collect('mind-discourse-corpus','Mind & discourse · full eligible corpus',full_discourse)
    for module, title in ((mind_lens_probe,'Mind lenses · Borges / Plato'),
                          (discourse_probe,'Mind & discourse · definitions'),
                          (discourse_portrait_probe,'Mind & discourse · conceptual portraits')):
        root=Path(workspace)/module.ROOT
        if not (root/'plan.json').exists(): continue
        def mind(module=module,root=root,title=title):
            plan=read_record(root/'plan.json'); histories,attempts=module.receipts(root,plan)
            expected=defaultdict(list)
            for item in plan['items']: expected[item['sample_id']].append(item['id'])
            samples=[dict(s, complete=bool(expected[s['id']]) and all(histories.get(i) and histories[i][-1]['status']=='complete' for i in expected[s['id']])) for s in plan['samples']]
            return assessment(module.ROOT, title, samples, message_index, questions=len(plan['spec']['features']),
                              wordings=len(module.VARIANTS), requests=len(attempts), source=module.ROOT,
                              href='#view=discourse' if module is discourse_portrait_probe else None)
        collect(module.ROOT,title,mind)
    atlas = None
    if topic_atlas is not None and studies is not None:
        try:
            atlas = atlas_inventory(catalog, topic_atlas, studies)
        except (OSError, ValueError, KeyError, TypeError, AttributeError, sqlite3.Error) as error:
            atlas = {'id': 'topic-atlas', 'title': 'Topic atlas · dictionary matching & opening reviews',
                     'status': 'Unavailable', 'error': str(error)[:240], 'included_in_assessment_coverage': False}
            issues.append({'id': 'topic-atlas', 'title': atlas['title'], 'message': atlas['error']})
    return {'schema':'behaviorlab.lab-summary/1','generated_at':datetime.now(timezone.utc).isoformat(),
            'indexed_at':getattr(catalog,'indexed_at',None), 'inventory':base,'assessments':rows,
            'topic_atlas': atlas,
            'assessment_union':{'covered_messages':len(covered),'denominator':base['real_messages'],
                                'coverage':percent(len(covered),base['real_messages'])},
            'issues':issues,'catalog_notices':getattr(catalog,'issues',[]),
            'probe_batches':[{'title':source_label(p['path'],workspace),'jobs':len(p['report'].get('jobs',[]))} for p in getattr(catalog,'probes',[])],
            'counting_rules':[
                'Real means recorded model output, including imported transcripts and technical checks. It does not mean human-authored text or validated scientific evidence.',
                'A message is one unique (run ID, message ID) participant contribution with recorded text. Empty strings count here; unavailable positions and external interventions do not. Shared branch nodes count once per run. All participant roles are included.',
                'Generation shares divide by all recorded messages (real + synthetic fixtures). Each source experiment appears once. Synthetic classifier controls are separate texts and are not generated-conversation messages.',
                'Assessment coverage divides completed, source-current real messages by the real-message corpus. A message must have every planned question pack or wording completed. Repeated questions, retries, packs and wordings do not add messages.',
                'Assessment batches overlap. Their percentages must not be added. Combined coverage is a union of source-message identities across readable batches; unavailable batches remain unknown.',
                'Topic atlas counts dictionary definitions, messages in its literal-scan scope and attributed opening outcomes per run. These counts never contribute to message-assessment coverage. Its cohort selector does not filter the assessment batches.',
                'This inventory covers indexed experiment sources and registered assessment plans. Diagnostic probe requests are listed separately; they do not add conversations or messages. Counts are descriptive, not independent experimental replicates.'
            ]}
