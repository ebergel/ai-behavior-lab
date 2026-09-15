"""Read-only assessment projection; observations remain attributed sidecars."""
from decimal import Decimal
from pathlib import Path
from statistics import median

from .assessment import replay, request_for
from .common import fingerprint, read_json, require, sha256
from .journal import read_events
from .trajectory_outcomes import line_features


def load_assessment(directory):
    from .explorer import base_summary
    path=Path(directory)/'events.jsonl'; original=path.read_bytes(); events=read_events(path)
    state=replay(events); plan=state['plan']; runs=[]; profiles=[]
    batch_id='assessment-'+events[0]['hash'][:24]
    source={'path':str(Path(directory).resolve()),'sha256':sha256(original),'journal_head':events[-1]['hash'],
            'protocol_sha256':fingerprint(plan),'parser':plan['schema'].replace('behaviorlab.',''),
            'verification':'Hash-chained journal, frozen requests, raw bytes and derived technical outcomes replayed. Remote weights, templates and effective samplers are not captured.'}
    for i,candidate in enumerate(plan['candidates']):
        profile=dict(candidate,runs=[],checks={},responses=0,valid_messages=0,cost_usd='0',median_seconds=None,missing_cost=0,errors=[])
        times=[]; costs=[]
        for kind in [*plan['checks'],'selfplay']:
            tasks=[t for t in plan['tasks'] if t['candidate']==i and t['kind']==kind]; messages=[]
            run_id='assessment-'+fingerprint([events[0]['hash'],i,kind])[:24]
            for task in tasks:
                key=task['id']; r=state['results'].get(key,{}); response=state['responses'].get(key); request=state['requests'].get(key)
                status=r.get('status','unresolved' if request else 'pending'); text=r.get('text'); usage=r.get('usage') or {}
                if response:
                    profile['responses']+=1; times.append(response['transport']['elapsed_seconds'])
                    if r.get('cost_usd') is not None: costs.append(Decimal(r['cost_usd']))
                    else: profile['missing_cost']+=1
                    data=read_json(response['raw'])
                    if data.get('error'):
                        error=data['error']; metadata=error.get('metadata') or {}
                        profile['errors'].append({'code':error.get('code'),'message':error.get('message'),
                            'detail':metadata.get('raw'),'run_id':run_id,'limit_source':metadata.get('limit_source')})
                profile['valid_messages']+=status=='valid'
                messages.append({'id':key,'parent':tasks[task['turn']-2]['id'] if task['turn']>1 else None,
                    'turn':task['turn'],'speaker':'X' if task['turn']%2 else 'Y','kind':'message','segment':'conversation',
                    'model':candidate['model'],'text':text,'thinking':r.get('thinking'),'thinking_recorded':bool(r.get('thinking')),
                    'status':status,'reason':r.get('reason'),'repeat':False,'lines':line_features(text),
                    'tokens':usage.get('completion_tokens'),'input_tokens':usage.get('prompt_tokens'),'cost_usd':r.get('cost_usd'),
                    'wall_seconds':response['transport']['elapsed_seconds'] if response else None,
                    'request':request,'raw_response':response['raw'] if response else None,'blocking_node':None,'seed':None})
            first_request=next((m['request'] for m in messages if m['request']),None)
            planned=request_for(plan,tasks[0],{}) if candidate['route'] else {'model':candidate['model'],'temperature':plan['temperature'],'max_tokens':plan['max_tokens'],'reasoning':plan['reasoning']}
            settings={k:v for k,v in (first_request or planned).items() if k!='messages'}
            prompt=plan['prompt'] if kind=='selfplay' else next((m['content'] for m in plan['checks'][kind] if m['role']=='system'),None)
            opening=plan['opening'] if kind=='selfplay' else plan['checks'][kind][-1]['content']
            run=base_summary({'id':run_id,'title':candidate['name'].replace(' (free)','')+' · '+kind,
                'collection':Path(directory).name,'collection_id':'model-assessment','kind':'synthetic' if events[0]['payload']['synthetic'] else 'lab',
                'data_class':'cloud_model_assessment','models':[candidate['model']],
                'condition':'Assessment · '+('anonymous self-play · full history' if kind=='selfplay' else kind+' check'),
                'model_kind':'Hosted configuration · exploratory screen','date':events[0]['at'],
                'complete':all(m['status'] in ('valid','cap','invalid') for m in messages),
                'unstarted_assessment':not any(m['request'] for m in messages),
                'prompt':prompt,'opening':opening,'settings':settings,'settings_by_speaker':{'X':settings,'Y':settings},
                'model_identities':[{'speaker':s,'tag':candidate['model'],'digest':None,'recorded_runtime_context':None} for s in ('X','Y')],
                'provider':(candidate['route'] or {}).get('provider_name'),'seed_policy':plan['seed_policy'],
                'cost_usd':None if any(m['request'] and m['cost_usd'] is None for m in messages) else str(sum((Decimal(m['cost_usd']) for m in messages if m['cost_usd'] is not None),Decimal(0))),
                'source':source,'messages':messages,'segments':[{'id':'conversation','parent':None,'start':1,'stop':len(tasks),'history':'F'}],
                'leaves':['conversation'],'webui_url':None,'probes':[]})
            runs.append(run)
            profile['runs'].append({'id':run_id,'kind':kind,'title':run['title'],'messages':run['message_count'],
                                    'preview':run['preview'],'statuses':[m['status'] for m in messages]})
            if kind!='selfplay':
                r=state['results'].get(tasks[0]['id'],{})
                profile['checks'][kind]={'match':r.get('check'),'status':messages[0]['status'],'reason':r.get('reason'),'run_id':run_id}
        profile['cost_usd']=str(sum(costs,Decimal(0))); profile['median_seconds']=median(times) if times else None
        profiles.append(profile)
    reading=None; sidecar=Path(directory)/'reading.json'
    if sidecar.exists():
        reading=read_json(sidecar.read_text()); require(reading['journal_head']==events[-1]['hash'],'Assessment reading source changed')
        require(bool(reading['author']) and bool(reading['method']),'Unattributed assessment reading')
        by_id={r['id']:r for r in runs}
        for finding in reading['findings']:
            for quote in finding.get('evidence',[]):
                run=by_id[quote['run_id']]; message=next(m for m in run['messages'] if m['id']==quote['message_id'])
                require(message['text'][quote['start']:quote['end']]==quote['quote'],'Assessment evidence span differs')
    require(path.read_bytes()==original,'Assessment journal changed during indexing; refresh after completion')
    return runs, {'id':batch_id,'date':events[0]['at'],'finished':state['finished'],'synthetic':events[0]['payload']['synthetic'],
        'profiles':profiles,'plan':plan,'source':source,'reading':reading,'calls':len(state['requests']),
        'responses':len(state['responses']),'cost_usd':str(sum((Decimal(p['cost_usd']) for p in profiles),Decimal(0))),
        'missing_cost':sum(p['missing_cost'] for p in profiles),
        'unresolved':sum(r['status']=='unresolved' for r in state['results'].values())}
