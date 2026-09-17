"""Reproducible corpus inventory and open-reading packets; no inference dispatch."""
from collections import Counter, defaultdict
from pathlib import Path

from .common import canonical, fingerprint, require
from .jev_atlas import now, write_record
from .topic_atlas import eligible, participant_messages

SEED = 'jev-two-tier-coverage-20260917-v1'


def context_for(run, message):
    """Two preceding evidence events on the actual path, including interventions."""
    messages = run['messages']; by_id = {m['id']: m for m in messages}
    if any(m.get('parent') for m in messages):
        previous = []; parent = message.get('parent'); visited = {message['id']}
        while parent:
            require(parent in by_id and parent not in visited, 'Missing or cyclic message ancestry')
            visited.add(parent); previous.append(by_id[parent]); parent = by_id[parent].get('parent')
        previous.reverse()
    else:
        require(len(run.get('leaves', [])) <= 1, 'Branched evidence requires explicit ancestry')
        previous = messages[:next(i for i, m in enumerate(messages) if m['id'] == message['id'])]
    return [{k: m.get(k) for k in ('id', 'speaker', 'text', 'status')} for m in previous[-2:]]


def build_inventory(catalog, seed=SEED):
    records = []; targets = []; source_items = {}; seen = set(); duplicate_nodes = []
    for run in sorted(catalog.runs.values(), key=lambda r: r['id']):
        # Some historical external interventions carry the recipient's X/Y
        # speaker label. Their event kind, not that label, defines their role.
        ms = [m for m in participant_messages(run) if m.get('kind') == 'message']
        # Same words in separate generations are retained. Full identical records
        # are grouped for sampling, without assuming they are independent roots.
        lineage = fingerprint([run.get('models'), run.get('prompt'),
            [{k:m.get(k) for k in ('id','parent','speaker','text','status')} for m in run['messages']]])
        if not any(m.get('text') for m in ms): lineage = fingerprint(['unavailable', run['id']])
        category = ('synthetic' if run['kind'] == 'synthetic' else
                    'unstarted' if run.get('unstarted_assessment') else
                    'conversation' if eligible(run) else 'technical_or_short')
        records.append({'id':run['id'],'title':run['title'],'lineage':lineage,'category':category,
            'data_class':run['data_class'],'models':run['models'],'condition':run['condition'],
            'source_sha256':run['source']['sha256'],'participant_positions':len(ms),
            'visible_targets':sum(bool(m.get('text')) for m in ms),
            'branched':len(run.get('leaves',[]))>1})
        if category == 'synthetic': continue
        for m in ms:
            identity = fingerprint([run['id'], m['id']])[:24]
            if identity in seen:
                duplicate_nodes.append(identity); continue
            seen.add(identity)
            context = context_for(run, m)
            item = {'id':identity,'run_id':run['id'],'run_title':run['title'],'models':run['models'],
                'condition':run['condition'],'message_id':m['id'],'speaker':m['speaker'],'turn':m['turn'],
                'source_sha256':run['source']['sha256'],'text':m.get('text'),'context':context,
                'message_status':m['status'],'split':'development','literal':{},'lineage':lineage}
            window_bytes = len(canonical({'text':item['text'],'context':context}).encode())
            meta = {k:v for k,v in item.items() if k not in ('text','context','literal','split')}
            meta.update(category=category,branched=len(run.get('leaves',[]))>1,
                visible=bool(m.get('text')),words=len((m.get('text') or '').split()),
                text_sha256=fingerprint(m.get('text')),context_sha256=fingerprint(context),
                window_bytes=window_bytes,window_sha256=fingerprint({'text':item['text'],'context':context}),
                prior_unavailable=any(not c['text'] for c in context),
                prior_flagged=any(c['status'] not in ('valid','recorded','intervention') for c in context))
            targets.append(meta); source_items[identity] = item
    by_window = defaultdict(list)
    for t in targets:
        if t['visible']: by_window[t['window_sha256']].append(t['id'])
    totals = {'records':len(records),'categories':dict(Counter(r['category'] for r in records)),
        'data_classes':dict(Counter(r['data_class'] for r in records)),
        'nonsynthetic_participant_positions':len(targets),
        'visible_nonsynthetic_targets':sum(t['visible'] for t in targets),
        'message_statuses':dict(Counter(t['message_status'] for t in targets)),
        'visible_flagged_targets':sum(t['visible'] and t['message_status'] not in ('valid','recorded') for t in targets),
        'oversized_18000_byte_windows':sum(t['visible'] and t['window_bytes']>18000 for t in targets),
        'branched_records':sum(r['branched'] and r['category']!='synthetic' for r in records),
        'identical_window_groups':sum(len(v)>1 for v in by_window.values())}
    return {'schema':'behaviorlab.jev-coverage-inventory/1','seed':seed,'records':records,'targets':targets,
        'totals':totals,'duplicate_nodes_removed':duplicate_nodes,
        'identical_windows':[v for v in by_window.values() if len(v)>1],
        'catalog_issues':catalog.issues,
        'policy':'Inventory includes partial and unavailable positions; synthetic records are counted separately. '
                 'Shared branch nodes occur once. Identical visible windows are flagged, not merged across distinct generations. '
                 'Two preceding evidence events follow actual ancestry and include external interventions.'}, source_items


def development_sample(inventory, items, count=48, seed=SEED):
    eligible_targets = [t for t in inventory['targets'] if t['category']=='conversation' and t['visible']
                        and t['message_status'] in ('valid','recorded') and t['window_bytes']<=18000]
    groups = defaultdict(list)
    for t in eligible_targets: groups[t['lineage']].append(t)
    selected = []; selected_ids = set()
    for lineage in sorted(groups, key=lambda x:fingerprint([seed,'root',x]))[:count]:
        target = min(groups[lineage], key=lambda t:fingerprint([seed,'target',t['id']]))
        selected.append(dict(items[target['id']], sampling_stratum='root_sample')); selected_ids.add(target['id'])
    # Separate coverage challenges, selected without looking at topic content.
    challenges = {
        'capped':lambda t:t['message_status']=='cap',
        'after_cap':lambda t:t['message_status']=='after_cap',
        'large_window':lambda t:t['window_bytes']>18000,
        'branched':lambda t:t['branched'] and t['message_status'] in ('valid','recorded'),
    }
    for name, predicate in challenges.items():
        pool = [t for t in inventory['targets'] if t['category']=='conversation' and t['visible'] and
                t['id'] not in selected_ids and predicate(t)]
        for target in sorted(pool,key=lambda t:fingerprint([seed,name,t['id']]))[:2]:
            selected.append(dict(items[target['id']],sampling_stratum=name)); selected_ids.add(target['id'])
    dev_lineages = {i['lineage'] for i in selected}
    return {'schema':'behaviorlab.jev-coverage-reading/1','seed':seed,'created_at':now(),
        'inventory_sha256':fingerprint(inventory),'items':selected,
        'development_lineages':sorted(dev_lineages),
        'future_evaluation_lineages':[x for x in sorted(groups) if x not in dev_lineages],
        'sampling':'Hash-ranked roots, one hash-ranked valid/recorded message per root; separate quality/size/branch challenges. '
                   'No topic scores, phrase matches or semantic enrichment. Challenges are not a prevalence sample.',
        'reader_exposure':'Codex knows the proposed taxonomy and earlier study. New reading packet omits labels and JEV scores; '
                          'this is open-description development, not blinded or independent human coding.'}


def freeze_coverage(catalog, destination, seed=SEED, count=48):
    destination = Path(destination)
    require(not destination.exists(), 'Coverage destination already exists; do not overwrite a freeze')
    inventory, items = build_inventory(catalog,seed)
    packet = development_sample(inventory,items,count,seed)
    write_record(destination/'inventory.json',inventory)
    write_record(destination/'reading-packet.json',packet)
    return inventory,packet
