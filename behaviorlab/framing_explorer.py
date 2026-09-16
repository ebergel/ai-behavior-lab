"""Read-only projection of the separately frozen framing comparison."""
from decimal import Decimal
from pathlib import Path
from statistics import median

from .common import fingerprint, read_json, require, sha256
from .journal import read_events
from .trajectory_outcomes import line_features


def load_framing(directory):
    from .explorer import base_summary
    path=Path(directory)/'events.jsonl'; original=path.read_bytes(); events=read_events(path)
    if events[0]['kind']=='paid_framing_created':
        from .paid_framing import replay, request_for, summary
    elif events[0]['kind']=='gpt4o_screen_created':
        from .gpt4o_screen import replay, request_for, summary
    else:
        from .framing import replay, request_for, summary
    state=replay(events); plan=state['plan']; runs=[]; roots=[]; stats=summary(state)
    source={'path':str(Path(directory).resolve()),'sha256':sha256(original),'journal_head':events[-1]['hash'],
        'protocol_sha256':fingerprint(plan),'parser':plan['schema'].replace('behaviorlab.',''),
        'verification':'Hash-chained journal, exact per-root ancestry, requests, raw bytes and technical outcomes replayed. Remote weights, templates and effective samplers are not captured.'}
    for root in plan['roots']:
        candidate=plan['candidates'][root.get('candidate',0)]
        display_name=candidate.get('display_name','Nemotron')
        tasks=[t for t in plan['tasks'] if t['root']==root['id']]; messages=[]; costs=[]; times=[]
        run_id='framing-'+fingerprint([events[0]['hash'],root['id']])[:24]
        for task in tasks:
            key=task['id']; result=state['results'].get(key,{}); response=state['responses'].get(key); request=state['requests'].get(key)
            usage=result.get('usage') or {}; text=result.get('text')
            if result.get('cost_usd') is not None:costs.append(Decimal(result['cost_usd']))
            if response:times.append(response['transport']['elapsed_seconds'])
            messages.append({'id':key,'parent':root['id']+':'+str(task['turn']-1) if task['turn']>1 else None,
                'turn':task['turn'],'speaker':'X' if task['turn']%2 else 'Y','kind':'message','segment':'conversation',
                'model':candidate['model'],'text':text,'thinking':result.get('thinking'),
                'thinking_recorded':bool(result.get('thinking')),'status':result.get('status','unresolved' if request else 'pending'),
                'reason':result.get('reason'),'repeat':bool(text and messages and text==messages[-1]['text']),
                'lines':line_features(text),'tokens':usage.get('completion_tokens'),
                'input_tokens':usage.get('prompt_tokens'),'cost_usd':result.get('cost_usd'),
                'wall_seconds':response['transport']['elapsed_seconds'] if response else None,
                'request':request,'raw_response':response['raw'] if response else None,'blocking_node':None,'seed':None})
        settings={k:v for k,v in request_for(plan,tasks[0],{}).items() if k!='messages'}
        run=base_summary({'id':run_id,'title':display_name+' · '+root['condition'].capitalize()+' '+str(root['replicate']),
            'collection':Path(directory).name,'collection_id':'model-assessment',
            'kind':'synthetic' if events[0]['payload']['synthetic'] else 'lab','data_class':'cloud_framing_screen',
            'models':[candidate['model']],'condition':'Framing · '+root['condition']+' · full history',
            'model_kind':'Hosted configuration · exploratory framing screen','date':events[0]['at'],
            'complete':all(m['status'] in ('valid','cap','invalid') for m in messages),
            'unstarted_assessment':not any(m['request'] for m in messages),
            'prompt':plan['prompts'][root['condition']],'opening':plan['opening'],
            'settings':settings,'settings_by_speaker':{'X':settings,'Y':settings},
            'model_identities':[{'speaker':s,'tag':candidate['model'],'digest':None,'recorded_runtime_context':None} for s in ('X','Y')],
            'provider':candidate['route']['provider_name'],'seed_policy':plan['seed_policy'],
            'cost_usd':None if any(m['request'] and m['cost_usd'] is None for m in messages) else str(sum(costs,Decimal(0))),
            'source':source,'messages':messages,'segments':[{'id':'conversation','parent':None,'start':1,'stop':12,'history':'F'}],
            'leaves':['conversation'],'webui_url':None,'probes':[]})
        runs.append(run)
        row=next(r for r in stats['roots'] if r['id']==root['id'])
        roots.append(dict(row,run_id=run_id,title=run['title'],model=candidate['model'],display_name=display_name,preview=run['preview'],cost_usd=run['cost_usd'],
                          median_seconds=median(times) if times else None,
                          messages=[{'id':m['id'],'turn':m['turn'],'status':m['status'],
                                     'words':len(m['text'].split()) if m['text'] else None} for m in messages]))
    reading=None; sidecar=Path(directory)/'reading.json'
    if sidecar.exists():
        reading=read_json(sidecar.read_text()); require(reading['journal_head']==source['journal_head'],'Framing reading source changed')
        require(bool(reading['author']) and bool(reading['method']),'Unattributed framing reading')
        by_id={r['id']:r for r in runs}
        evidence_groups=[f.get('evidence',[]) for f in reading['findings']]
        evidence_groups += [[e['evidence'] for e in r.get('onsets',[])] for r in reading.get('root_reviews',{}).values()]
        for group in evidence_groups:
            for quote in group:
                run=by_id[quote['run_id']]; message=next(m for m in run['messages'] if m['id']==quote['message_id'])
                start,end=quote['start'],quote['end']; text=message['text']
                require(isinstance(text,str) and 0<=start<end<=len(text) and text[start:end]==quote['quote'],'Framing evidence span differs')
        if 'root_reviews' in reading:
            require(set(reading['root_reviews'])=={r['id'] for r in plan['roots']},'Framing reading omits a root')
    require(path.read_bytes()==original,'Framing journal changed during indexing; refresh after completion')
    return runs,{'id':'framing-'+events[0]['hash'][:24],'screen_type':'framing','date':events[0]['at'],
        'finished':state['finished'],'synthetic':events[0]['payload']['synthetic'],'plan':plan,'source':source,
        'reading':reading,'profiles':[],'roots':roots,'calls':stats['calls'],'responses':stats['responses'],
        'cost_usd':stats['known_cost_usd'],'missing_cost':stats['missing_response_cost'],
        'reserved_unknown_cost_usd':stats.get('reserved_unknown_cost_usd','0'),
        'unresolved':sum(r['status']=='unresolved' for r in state['results'].values())}
