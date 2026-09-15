"""Read-only projection of participant comparison journals into Explorer rows."""
from decimal import Decimal
import base64
from pathlib import Path

from .common import fingerprint, read_json, require, sha256
from .journal import read_events
from .participants import payload, replay, report
from .trajectory_outcomes import line_features


def load_participants(directory):
    from .explorer import base_summary
    path=Path(directory)/'events.jsonl'; original=path.read_bytes(); events=read_events(path)
    state=replay(events); plan=state['plan']; summary=report(events); found=[]
    for job in plan['jobs']:
        # Frozen but never dispatched roots are not observed conversations.
        if not any(key.startswith(job['id']+':') for key in state['requests']): continue
        model=plan['models'][job['model']]; messages=[]; blocked=None; suffix=0; previous=None
        for turn in range(1,job['turns']+1):
            key=job['id']+':'+str(turn); result=state['results'].get(key)
            req=state['requests'].get(key); resp=state['responses'].get(key); text=None
            status='blocked' if blocked else 'pending'; reason=None
            if key in state['rejected']: status='not_dispatched'; reason=state['rejected'][key]['reason']
            if req: status='unresolved'; reason='Request saved; response unknown'
            if resp:
                status='uncommitted'; reason='Raw response saved; outcome not committed'
                try: text=read_json(resp['raw'])['choices'][0]['message']['content']
                except (ValueError,TypeError,KeyError,IndexError): pass
            if result:
                status=result['status']; reason=result['reason']; text=result['text'] if result['text'] is not None else text
            if status in ('cap','invalid','not_dispatched','unresolved'): blocked=blocked or key
            suffix=suffix+1 if text and text==previous else 1; previous=text
            usage=(result or {}).get('usage') or {}
            messages.append({'id':key,'parent':job['id']+':'+str(turn-1) if turn>1 else None,
                'turn':turn,'speaker':'X' if turn%2 else 'Y','kind':'message','segment':'conversation',
                'model':model['model'],'text':text,'thinking':(result or {}).get('thinking'),
                'thinking_recorded':bool((result or {}).get('thinking')),'status':status,'reason':reason,
                'repeat':bool(status=='valid' and suffix>=6 and text and text.strip()), 'lines':line_features(text),
                'tokens':usage.get('completion_tokens'),'input_tokens':usage.get('prompt_tokens'),
                'cost_usd':(result or {}).get('cost_usd'),'provider':(result or {}).get('provider'),
                'reported_model':(result or {}).get('reported_model'),'system_fingerprint':(result or {}).get('system_fingerprint'),
                'wall_seconds':resp['transport'].get('elapsed_seconds') if resp else None,
                'request':req['request'] if req else None,'raw_response':resp['raw'] if resp else None,
                'blocking_node':blocked, 'seed':req['request'].get('seed') if req else None})
        settings=payload(plan,job,1,{})
        settings={k:v for k,v in settings.items() if k not in ('messages','seed')}
        cost=sum((Decimal(m['cost_usd']) for m in messages if m['cost_usd'] is not None),Decimal(0))
        job_report=next(j for j in summary['jobs'] if j['id']==job['id'])
        smoke=job['condition']=='smoke'; synthetic=events[0]['payload']['synthetic']
        found.append(base_summary({'id':'cloud-'+fingerprint([events[0]['hash'],job['id']])[:24],
            'title':job['id'],'collection':Path(directory).name,'collection_id':'cloud-participants',
            'kind':'synthetic' if synthetic else 'lab','data_class':'synthetic_cloud_fixture' if synthetic else
                'cloud_integration_smoke' if smoke else plan['data_class'],
            'models':[model['model']],'speakers':{'X':model['model'],'Y':model['model']},
            'condition':job['condition']+' · full history','model_kind':'Hosted service configuration',
            'date':events[0]['at'],'complete':not any(job_report['counts'][k] for k in ('pending','unresolved','uncommitted')),
            'prompt':'Reply with the single word Ready.' if smoke else plan['prompts'][job['condition']],
            'opening':plan['opening'],'settings':settings,'settings_by_speaker':{'X':settings,'Y':settings},
            'model_identities':[{'speaker':s,'tag':model['model'],'digest':None,'recorded_runtime_context':None} for s in ('X','Y')],
            'provider':model['provider_name'],'cost_usd':str(cost),'seed_policy':'Requested per message' if model['seed_supported'] else 'Unsupported · not requested',
            'source':{'path':str(Path(directory).resolve()),'sha256':sha256(original),'journal_head':events[-1]['hash'],
                      'protocol_sha256':fingerprint(plan),'parser':plan['parser'],
                      'verification':'Journal, API requests, raw response bytes, reported provider/model and cost replayed. Remote templates, weights and effective sampler internals are not observable.'},
            'messages':messages,'segments':[{'id':'conversation','parent':None,'start':1,'stop':job['turns'],'history':'F'}],
            'leaves':['conversation'],'webui_url':None,'probes':[]}))
    require(path.read_bytes()==original,'Participant campaign changed during indexing; refresh after writer pauses')
    return found


def load_cloud_diagnostics(directory):
    from .explorer import base_summary
    path=Path(directory)/'events.jsonl'; original=path.read_bytes(); events=read_events(path)
    header=events[0]['payload']; tasks={t['id']:t for t in header['tasks']}; responses={}; requested=set()
    require(events[0]['kind'] in ('cloud_instruction_diagnostic_created','cloud_system_formats_created'), 'Unknown diagnostic journal')
    for event in events[1:]:
        p=event['payload']; key=p['id']; require(key in tasks,'Unknown diagnostic task')
        if event['kind']=='diagnostic_request':
            require(key not in requested and p['request_sha256']==fingerprint(tasks[key]['request']), 'Invalid diagnostic request')
            requested.add(key)
        elif event['kind']=='diagnostic_response':
            require(key in requested and key not in responses,'Duplicate/unrequested diagnostic response')
            b=base64.b64decode(p['transport']['response_bytes_base64'],validate=True)
            require(sha256(b)==p['transport']['response_sha256'] and b.decode('utf-8')==p['raw'],'Diagnostic bytes differ')
            responses[key]=p
        elif event['kind'] not in ('diagnostic_result','diagnostic_transport_error'): raise ValueError('Unknown diagnostic event')
    found=[]
    for key,task in tasks.items():
        req=task['request']; resp=responses.get(key); d=read_json(resp['raw']) if resp else {}; usage=d.get('usage') or {}
        native=task.get('path')=='/messages'; msg=d.get('choices',[{}])[0].get('message',{}) if not native else {}
        text=''.join(c['text'] for c in d.get('content',[]) if c.get('type')=='text') if native else msg.get('content')
        finish=d.get('stop_reason') if native else d.get('choices',[{}])[0].get('finish_reason')
        status='valid' if finish in ('stop','end_turn') else 'cap' if finish in ('length','max_tokens') else 'invalid' if resp else 'unresolved' if key in requested else 'pending'
        system=req.get('system') or next((m['content'] for m in req['messages'] if m['role']=='system'),None)
        if isinstance(system,list):system=''.join(c.get('text','') for c in system)
        opening=next((m['content'] for m in req['messages'] if m['role']=='user'),None)
        settings={k:v for k,v in req.items() if k not in ('messages','system')}
        m={'id':key+':1','parent':None,'turn':1,'speaker':'X','kind':'message','segment':'conversation',
           'model':req['model'],'text':text,'thinking':None,'thinking_recorded':False,'status':status,'reason':finish,
           'repeat':False,'lines':line_features(text),'tokens':usage.get('completion_tokens',usage.get('output_tokens')),
           'input_tokens':usage.get('prompt_tokens',usage.get('input_tokens')),'cost_usd':str(usage['cost']) if 'cost' in usage else None,
           'wall_seconds':resp['transport'].get('elapsed_seconds') if resp else None,'request':req,'raw_response':resp['raw'] if resp else None,
           'blocking_node':None,'seed':req.get('seed')}
        found.append(base_summary({'id':'cloud-'+fingerprint([events[0]['hash'],key])[:24], 'title':key,
            'collection':Path(directory).name,'collection_id':'cloud-participants','kind':'lab','data_class':'cloud_integration_diagnostic',
            'models':[req['model']],'condition':'Instruction check · '+('native Messages API' if native else 'Chat Completions API'),
            'model_kind':'Hosted service configuration','date':events[0]['at'],'complete':bool(resp), 'prompt':system,
            'opening':opening,'settings':settings,'settings_by_speaker':{'X':settings,'Y':settings},
            'model_identities':[{'speaker':'X','tag':req['model'],'digest':None,'recorded_runtime_context':None}],
            'cost_usd':str(usage['cost']) if 'cost' in usage else None,'provider':d.get('provider'), 'seed_policy':'Not requested',
            'source':{'path':str(Path(directory).resolve()),'sha256':sha256(original),'journal_head':events[-1]['hash'],
                      'verification':'Technical check, not self-play. Journal, predeclared request and raw response bytes verified. System instruction compliance is a measured outcome; upstream transmission is not captured.'},
            'messages':[m],'segments':[{'id':'conversation','parent':None,'start':1,'stop':1,'history':'F'}],
            'leaves':['conversation'],'webui_url':None,'probes':[]}))
    require(path.read_bytes()==original,'Diagnostic journal changed during indexing')
    return found
