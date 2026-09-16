"""Opening comparisons over existing collections; never dispatches inference."""
from collections import Counter
from .common import canonical, require, timestamp
from .finder import experiment
from .topic_atlas import participant_messages, VALID, WINDOW


def dimensions(run):
    e=experiment(run)
    return {
        'Participant models':{p['speaker']:p['models'] for p in e['roster']} or None,
        'Prompt':run.get('prompt') or None,
        'Opening cue':run.get('opening') or None,
        'Identity disclosure':e['identity'],
        'Human presence instruction':e['human'],
        'History policy':e['history'],
        'Task instruction':e['task'],
        'Exit instruction':e['exit'],
        'External intervention':e['external'],
        'Planned participant positions':run.get('planned_count'),
        'Recorded/requested settings':run.get('settings_by_speaker') or run.get('settings') or None,
        'Seed policy':run.get('seed_policy') or None,
        'Protocol fingerprint':run.get('source',{}).get('protocol_sha256'),
    }


def comparison(rows):
    result=[]
    for name in dimensions(rows[0]) if rows else []:
        values=[dimensions(r)[name] for r in rows]
        # Matching missing values cannot establish a shared experimental condition.
        missing=any(v is None or v=='Unknown' for v in values)
        state='unknown' if missing else 'same' if len({canonical(v) for v in values})==1 else 'different'
        result.append({'name':name,'state':state,'values':values})
    return result


def build_workbench(catalog,studies,atlas,study_id,selected=None):
    study=studies.get(study_id)
    ids=[m['run_id'] for m in study['runs']]
    if selected is None:selected=ids[:min(4,len(ids))]
    require(isinstance(selected,list) and len(selected)<=4 and all(isinstance(s,str) for s in selected),'Choose up to four conversations')
    require(len(set(selected))==len(selected) and all(s in ids for s in selected),'Comparison must use distinct members of this collection')
    dictionary={t['id']:t for t in atlas.dictionary()}
    reviews={r['run_id']:r for r in atlas.reviews(catalog)}
    rows=[];groups={}
    for identity in ids:
        run=catalog.runs.get(identity)
        if run is None:
            rows.append({'id':identity,'title':'Source unavailable','available':False,'review_state':'unavailable'})
            continue
        source=run['source'];block_key=source.get('protocol_sha256') or 'unrecorded:'+identity
        if block_key not in groups:
            groups[block_key]={'id':'block-'+str(len(groups)+1),'source_label':run.get('collection','Source'),
                               'label':{'mixed_dialogue_exploration':'Mixed-pair pilot','cloud_framing_screen':'Framing comparison'}.get(run.get('data_class'),'Recorded experiment'),
                               'protocol_sha256':source.get('protocol_sha256'),'rows':[]}
        block=groups[block_key]
        ms=participant_messages(run);window=[m for m in ms if m['turn']<=WINDOW]
        complete=(len(window)==WINDOW and {m['turn'] for m in window}==set(range(1,WINDOW+1))
                  and all(m['status'] in VALID and isinstance(m.get('text'),str) for m in window))
        review=reviews.get(identity);current=bool(review and review['source_current'] and review['dictionary_current'])
        choice=review['choice'] if current and review['status']=='selected' else None
        row={'id':identity,'title':run['title'],'models':run['models'],'condition':run['condition'],
             'available':True,'block':block['id'],'experiment':experiment(run),'source':source,
             'review_state':review['status'] if current else 'stale' if review else 'unreviewed',
             'review':review,'choice':choice,'topic':dictionary.get(choice['topic_id']) if choice else None,
             'opener':{k:ms[0].get(k) for k in ('model','speaker','id')} if ms else None,
             'window_complete':complete,'window_visible_words':sum(len((m.get('text') or '').split()) for m in window),
             'messages':[{k:m.get(k) for k in ('id','turn','speaker','model','text','status')} for m in window] if identity in selected else [],
             'prompt':run.get('prompt'),'opening':run.get('opening')}
        rows.append(row);block['rows'].append(row)
    blocks=[]
    for block in groups.values():
        rs=block.pop('rows');resolved=[r for r in rs if r['review_state'] in ('selected','no_selection')]
        counts=Counter(r['topic']['title'] for r in resolved if r['choice'])
        blocks.append(dict(block,run_ids=[r['id'] for r in rs],total=len(rs),reviewed=len(resolved),
                           no_selection=sum(r['review_state']=='no_selection' for r in rs),topics=dict(counts)))
    by_id={r['id']:r for r in rows}
    selected_rows=[by_id[i] for i in selected]
    settings=comparison([catalog.runs[i] for i in selected if i in catalog.runs]) if all(i in catalog.runs for i in selected) else []
    return {'schema':'behaviorlab.study-workbench/1','generated_at':timestamp(),'collection':study,'rows':rows,'blocks':blocks,
            'selected':selected,'comparison':settings,'selected_rows':selected_rows,
            'scope':'Attributed opening reviews within six participant positions. Protocol blocks are not pooled causal contrasts. Matching requested settings do not establish identical effective sampling.'}
