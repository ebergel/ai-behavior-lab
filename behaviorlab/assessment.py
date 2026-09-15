"""A finite, zero-price model screen. Never called for inference by the Explorer."""
import base64
from decimal import Decimal, InvalidOperation
from pathlib import Path
import time

from .backends import http_request
from .common import canonical, fingerprint, read_json, require, sha256, timestamp
from .journal import Journal, read_events

ENDPOINT = 'https://openrouter.ai/api/v1'
SELECTED = ['liquid/lfm-2.5-2.6b:free', 'google/gemma-4-26b-a4b-it:free',
            'nvidia/nemotron-3.5-lightning:free', 'thinkingmachines/inkling-small:free',
            'inclusionai/ling-3.0-flash-vl:free', 'nex-agi/nex-n2.5-mini:free']
PROMPT = 'You may act freely in this open-ended conversation. Write only your own next message. Keep each message to at most 150 words.'
OPENING = '(The conversation begins. You speak first.)'
CHECKS = {
    'system': [{'role':'system','content':'Reply with exactly LAB_ROUTING_OK and nothing else.'},
               {'role':'user','content':'Compute 2 + 2.'}],
    'user': [{'role':'user','content':'Reply with exactly LAB_ROUTING_OK and nothing else.'}],
    'history': [{'role':'user','content':'The sealed label is cedar-731. Remember it for this conversation.'},
                {'role':'assistant','content':'I will remember the sealed label.'},
                {'role':'user','content':'What is the sealed label? Reply with the label only.'}],
    'json': [{'role':'user','content':'Return only a JSON object with exactly two keys: "color" with value "teal" and "count" with integer value 3. Do not use a code fence.'}],
}

FOLLOWUP = [SELECTED[2], SELECTED[3], SELECTED[4]]
COMPLETION = [SELECTED[2], SELECTED[4]]


def make_completion(catalog, routes, prior_directories):
    """Complete untouched slots; keep the earlier successful check as a citation."""
    sources=[]; prior_check=None; prior_calls=0
    for directory in prior_directories:
        path=Path(directory)/'events.jsonl'; original=path.read_bytes(); events=read_events(path); old=replay(events)
        require(old['finished'],'Prior screens must be closed')
        sources.append({'path':str(path.resolve()),'sha256':sha256(original),'journal_head':events[-1]['hash']})
        prior_calls+=len(old['requests'])
        for t in old['plan']['tasks']:
            if t['id'] not in old['requests']: continue
            model=old['plan']['candidates'][t['candidate']]['model']
            require(model!=COMPLETION[1],'Ling has already been dispatched; make a new explicit design')
            if model==COMPLETION[0]:
                require(t['kind']=='system' and prior_check is None,'Only the single prior Nemotron system check can be reused')
                result=old['results'][t['id']]
                require(result['status']=='valid' and result['check'] is True,'Prior system check was not successful')
                prior_check={'candidate':0,'kind':'system','request':old['requests'][t['id']],
                    'response':old['responses'][t['id']],'result':result,
                    'source':dict(sources[-1],run_id='assessment-'+fingerprint([events[0]['hash'],t['candidate'],'system'])[:24],message_id=t['id'])}
    require(prior_check is not None,'A verified prior Nemotron system check is required')
    plan=make_plan(catalog,routes)
    plan.update(schema='behaviorlab.model-assessment/3',max_calls=15,
        selection='Complete the remaining Nemotron checks and assess untouched Ling. Preserve the earlier successful Nemotron system check as prior evidence; do not repeat it.',
        failure_policy='No retries or replacements. Each candidate completes its checks before its conversation. All check responses must be technically valid; exact-answer mismatch is not a gate. Nonvalid self-play blocks descendants. Explicit upstream shared-pool quota stops only its candidate; account or unknown quota, access, transport, identity and accounting errors stop the batch.',
        prior_checks=[prior_check],prior_screens=sources,
        aggregate_call_ceiling_including_prior=prior_calls+15)
    plan['candidates']=[c for c in plan['candidates'] if c['model'] in COMPLETION]
    plan['tasks']=completion_tasks()
    return plan


def completion_tasks():
    return [{'id':f'm{i+1}-{kind}:{t}','candidate':i,'kind':kind,'turn':t}
            for i in range(2) for kind in [*CHECKS,'selfplay'] if not (i==0 and kind=='system')
            for t in range(1,5 if kind=='selfplay' else 2)]


def checks_available(plan, task, results):
    checks={t['kind']:results.get(t['id'],{}).get('status') for t in plan['tasks']
            if t['candidate']==task['candidate'] and t['kind'] in CHECKS}
    checks.update({p['kind']:p['result']['status'] for p in plan.get('prior_checks',[]) if p['candidate']==task['candidate']})
    return set(checks)==set(CHECKS) and all(status=='valid' for status in checks.values())


def make_followup(catalog, routes, prior_events):
    prior=replay(prior_events)
    require(prior['finished'],'Close the prior screen before a follow-up')
    require(not any(prior['plan']['candidates'][t['candidate']]['model'] in FOLLOWUP
                    for t in prior['plan']['tasks'] if t['id'] in prior['requests']), 'Follow-up cannot repeat a previously dispatched model')
    plan=make_plan(catalog,routes)
    plan.update(schema='behaviorlab.model-assessment/2',max_calls=24,
        selection='Three previously undispatched developers from the original six-candidate screen. No replacements or selection based on generated content.',
        failure_policy='No retries or replacements. Nonvalid self-play blocks descendants. An explicitly identified upstream shared-pool limit stops only its candidate. Account/unknown quota, transport uncertainty, identity or accounting failure stops the batch. Other API/reasoning failures stop that candidate.',
        prior_screen={'journal_head':prior_events[-1]['hash'],'requests':len(prior['requests']),
                      'aggregate_call_ceiling_including_prior':len(prior['requests'])+24})
    plan['candidates']=[c for c in plan['candidates'] if c['model'] in FOLLOWUP]
    plan['tasks']=[{'id':f'm{i+1}-{kind}:{t}','candidate':i,'kind':kind,'turn':t}
                   for kind in [*CHECKS,'selfplay'] for i in range(3)
                   for t in range(1,5 if kind=='selfplay' else 2)]
    return plan


def free_route(route):
    try:
        return (route['status'] == 0 and all(Decimal(str(route['pricing'][k])) == 0 for k in ('prompt','completion'))
                and {'temperature','max_tokens','reasoning'} <= set(route['supported_parameters'])
                and route['context_length'] >= 8192 and route['max_completion_tokens'] >= 1024)
    except (KeyError, TypeError, InvalidOperation):
        return False


def make_plan(catalog, routes):
    entries = {m['id']:m for m in catalog['models']}; candidates=[]
    for model in SELECTED:
        m=entries[model]; available=[e for e in routes['routes'][model]['endpoints'] if free_route(e)]
        candidates.append({'model':model,'name':m['name'],'description':m.get('description',''),
            'canonical_slug':m['canonical_slug'],'route':available[0] if available else None,
            'route_observations':routes['routes'][model]['endpoints'],
            'availability':'eligible' if available else 'unavailable_at_freeze'})
    tasks=[]
    # Fixed rounds keep each model's check type at a comparable point in the batch.
    for kind in [*CHECKS,'selfplay']:
        for i,c in enumerate(candidates):
            for turn in range(1,5 if kind=='selfplay' else 2):
                tasks.append({'id':f'm{i+1}-{kind}:{turn}','candidate':i,'kind':kind,'turn':turn})
    return {'schema':'behaviorlab.model-assessment/1','created_at':timestamp(),
        'question':'Which free hosted configurations can sustain a small, inspectable conversation under the lab interface?',
        'selection':'Six different developers visible in the user catalog; general text participants. No selection on spiritual or consciousness content.',
        'scope':'Exploratory usability screen; one sample per check, one four-message root per available model. Not a behavioral prevalence estimate or factorial qualification.',
        'endpoint':ENDPOINT,'candidates':candidates,'tasks':tasks,'checks':CHECKS,
        'prompt':PROMPT,'opening':OPENING,'max_tokens':1024,'temperature':0.8,
        'budget_usd':'0','max_calls':48,'max_inflight':1,'min_interval_seconds':4.2,
        'seed_policy':'No seeds requested; empty seed allocation. Provider randomness is uncontrolled; no matched random draws claimed.',
        'seed_allocations':[], 'reasoning':{'enabled':False},
        'failure_policy':'No retries or replacements. Nonvalid self-play blocks descendants. Transport uncertainty, quota, identity or accounting failure stops the batch. Other API failures stop that candidate. Instruction mismatches are outcomes, not exclusion gates.',
        'catalog_sha256':fingerprint(catalog),'routes_sha256':fingerprint(routes)}


def validate(plan):
    require(plan['schema'] in ('behaviorlab.model-assessment/1','behaviorlab.model-assessment/2','behaviorlab.model-assessment/3') and plan['endpoint']==ENDPOINT,'Unknown assessment contract')
    followup=plan['schema']=='behaviorlab.model-assessment/2'
    completion=plan['schema']=='behaviorlab.model-assessment/3'
    require(plan['budget_usd']=='0' and plan['max_calls']==(15 if completion else 24 if followup else 48) and plan['max_inflight']==1,'Assessment limits changed')
    require(plan['max_tokens']==1024 and plan['temperature']==0.8 and plan['min_interval_seconds']==4.2,'Assessment settings changed')
    require(plan['prompt']==PROMPT and plan['opening']==OPENING and plan['checks']==CHECKS and plan['reasoning']=={'enabled':False},'Assessment prompts changed')
    require(plan['seed_allocations']==[],'Assessment seeds changed')
    require([c['model'] for c in plan['candidates']]==(COMPLETION if completion else FOLLOWUP if followup else SELECTED),'Assessment selection changed')
    expected=[]
    for kind in [*CHECKS,'selfplay']:
        for i,c in enumerate(plan['candidates']):
            require(c['model'].endswith(':free'),'Only explicit free variants are permitted')
            if c['route']: require(free_route(c['route']),'Route is not eligible at zero price')
            for t in range(1,5 if kind=='selfplay' else 2):
                expected.append({'id':f'm{i+1}-{kind}:{t}','candidate':i,'kind':kind,'turn':t})
    if completion:
        expected=completion_tasks(); require(len(plan['prior_checks'])==1,'Expected one prior check')
        prior=plan['prior_checks'][0]; require(prior['candidate']==0 and prior['kind']=='system','Wrong prior check')
        task={'id':'m1-system:1','candidate':0,'kind':'system','turn':1}
        # Compare the frozen request controls, independent of current route availability.
        req=prior['request']; require(req['model']==COMPLETION[0] and req['messages']==CHECKS['system'],'Wrong prior check request')
        require(req['temperature']==0.8 and req['max_tokens']==1024 and req['reasoning']=={'enabled':False},'Prior check settings differ')
        if plan['candidates'][0]['route']:
            require(req==request_for(plan,task,{}),'Prior check route/settings differ')
            response=prior['response']; result=parse(response['raw'],response['transport'],plan,task)
            require(result==prior['result'] and result['status']=='valid' and result['check'] is True,'Prior response differs')
    require(plan['tasks']==expected,'Task allocation changed')
    return plan


def request_for(plan, task, results):
    c=plan['candidates'][task['candidate']]; route=c['route']
    require(route is not None,'No eligible free route')
    if task['kind']!='selfplay': messages=plan['checks'][task['kind']]
    else:
        messages=[{'role':'system','content':plan['prompt']}]
        if task['turn']%2: messages.append({'role':'user','content':plan['opening']})
        for t in range(1,task['turn']):
            previous=results[task['id'].rsplit(':',1)[0]+':'+str(t)]
            require(previous['status']=='valid','Unavailable self-play history')
            messages.append({'role':'assistant' if t%2==task['turn']%2 else 'user','content':previous['text']})
    require(sum(len(m['content'].encode())+64 for m in messages)+2048+1024 <= route['context_length'],'Conservative context allowance exceeded')
    return {'model':c['model'],'messages':messages,'temperature':plan['temperature'],
        'max_tokens':plan['max_tokens'],'reasoning':plan['reasoning'],'stream':False,'transforms':[],
        'provider':{'only':[route['tag']],'allow_fallbacks':False,'require_parameters':True,
                    'max_price':{'prompt':0,'completion':0}}}


def parse(raw, transport, plan, task):
    b=base64.b64decode(transport['response_bytes_base64'],validate=True)
    require(sha256(b)==transport['response_sha256'] and b.decode('utf-8',errors='replace')==raw,'Raw response bytes differ')
    r={'status':'invalid','reason':None,'text':None,'thinking':None,'cost_usd':None,
       'usage':None,'provider':None,'reported_model':None,'check':None,'halt':False,'stop_candidate':False}
    try:
        d=read_json(raw); u=d.get('usage') or {}; r.update(usage=u,provider=d.get('provider'),reported_model=d.get('model'))
        if 'cost' in u:
            cost=Decimal(str(u['cost'])); require(cost.is_finite() and cost==0,'Nonzero or invalid billed cost')
            r['cost_usd']=str(cost)
        if transport['http_status']!=200 or d.get('error'):
            shared_limit=(plan['schema'] in ('behaviorlab.model-assessment/2','behaviorlab.model-assessment/3') and transport['http_status']==429
                          and ((d.get('error') or {}).get('metadata') or {}).get('limit_source')=='upstream_provider_shared_pool')
            r.update(reason='API error: '+str(transport['http_status']),stop_candidate=True,
                     halt=not shared_limit and (transport['http_status'] in (401,402,403,429) or (d.get('error') or {}).get('code') in (401,402,403,429)))
            return r
        c=plan['candidates'][task['candidate']]
        allowed={c['model'],c['model'].removesuffix(':free'),c['canonical_slug'],c['canonical_slug']+':free'}
        require(d.get('model') in allowed and d.get('provider')==c['route']['provider_name'],'Reported model/provider mismatch')
        require(r['cost_usd'] is not None,'Missing billed usage cost')
        require(all(type(u.get(k)) is int and u[k]>=0 for k in ('prompt_tokens','completion_tokens')),'Missing token usage')
        require(u['completion_tokens']<=plan['max_tokens'],'Output budget exceeded')
        require(len(d['choices'])==1,'Unexpected choice count')
        ch=d['choices'][0]; msg=ch['message']; r['text']=msg.get('content')
        traces={k:msg[k] for k in ('reasoning','reasoning_details','reasoning_content','thinking') if msg.get(k)}
        r['thinking']=canonical(traces) if traces else None
        require(isinstance(r['text'],str) and r['text'].strip(),'No visible assistant text')
        if traces or (u.get('completion_tokens_details') or {}).get('reasoning_tokens'):
            r.update(reason='Unexpected reasoning with reasoning disabled',stop_candidate=True); return r
        require(not msg.get('tool_calls') and not msg.get('function_call'),'Unexpected tools')
        require(ch.get('finish_reason') in ('stop','length'),'Unsupported finish reason')
        r.update(status='cap' if ch['finish_reason']=='length' else 'valid',reason='output_cap' if ch['finish_reason']=='length' else None)
        if r['status']=='valid' and task['kind']!='selfplay':
            expected={'system':'LAB_ROUTING_OK','user':'LAB_ROUTING_OK','history':'cedar-731'}
            if task['kind']=='json':
                try:
                    parsed=read_json(r['text']); r['check']=parsed=={'color':'teal','count':3} and type(parsed['count']) is int
                except (ValueError,TypeError,KeyError): r['check']=False
            else: r['check']=r['text'].strip()==expected[task['kind']]
    except (ValueError,KeyError,TypeError,IndexError,AttributeError,InvalidOperation) as e:
        r.update(reason=str(e)[:180],halt=True)
    return r


def replay(events):
    require(events and events[0]['kind']=='model_assessment_created','Not an assessment journal')
    header=events[0]['payload']; plan=validate(header['plan']); require(fingerprint(plan)==header['plan_sha256'],'Plan differs')
    tasks={t['id']:t for t in plan['tasks']}; requests={}; responses={}; results={}; finished=False
    for event in events[1:]:
        p=event['payload']; k=event['kind']; require(not finished,'Events after assessment completion')
        if k=='assessment_finished': finished=True; continue
        key=p['id']; require(key in tasks,'Unknown task')
        if k=='assessment_request':
            require(key not in requests and key not in results and len(requests)<plan['max_calls'],'Duplicate or excess request')
            require(not any(r.get('halt') for r in results.values()),'Dispatch after halt')
            if plan['schema']=='behaviorlab.model-assessment/3' and tasks[key]['kind']=='selfplay':
                require(checks_available(plan,tasks[key],results),'Self-play before technical checks')
            require(p['request']==request_for(plan,tasks[key],results),'Saved request differs from frozen history')
            requests[key]=p['request']
        elif k=='assessment_response':
            require(key in requests and key not in responses,'Unrequested or duplicate response'); responses[key]=p
        elif k=='assessment_result':
            require(key in responses and key not in results,'Unrequested or duplicate result')
            require(p['result']==parse(responses[key]['raw'],responses[key]['transport'],plan,tasks[key]),'Derived outcome differs')
            results[key]=p['result']
        elif k=='assessment_skipped':
            require(key not in requests and key not in results,'Skipped a dispatched request')
            results[key]={'status':'not_dispatched','reason':p['reason'],'text':None,'check':None}
        elif k=='assessment_transport_error':
            require(key in requests and key not in responses and key not in results,'Unexpected transport error')
            results[key]={'status':'unresolved','reason':p['reason'],'text':None,'check':None,'halt':True}
        else: raise ValueError('Unknown assessment event')
    return {'plan':plan,'requests':requests,'responses':responses,'results':results,'finished':finished}


def execute(directory, token, generate=None, sleep=time.sleep):
    generate=generate or (lambda p:http_request(ENDPOINT,'/chat/completions',p,token,timeout=120))
    with Journal(directory) as journal:
        state=replay(journal.events)
        if state['finished']: return state
        for name,digest in journal.events[0]['payload']['code_hashes'].items():
            require(sha256(Path(name).read_bytes())==digest,'Frozen runner source changed')
        last_dispatch=time.monotonic()
        for task in state['plan']['tasks']:
            key=task['id']
            if key in state['results']: continue
            if key in state['responses']:
                response=state['responses'][key]
                journal.append('assessment_result',{'id':key,'result':parse(response['raw'],response['transport'],state['plan'],task)})
                state=replay(journal.events); continue
            if key in state['requests']:
                journal.append('assessment_transport_error',{'id':key,'reason':'Saved request with unknown response; never retried'})
                state=replay(journal.events); continue
            plan=state['plan']; candidate=plan['candidates'][task['candidate']]; reason=None
            if any(r.get('halt') for r in state['results'].values()): reason='Batch stopped after quota, identity, accounting or transport failure'
            elif not candidate['route']: reason='No eligible free route at freeze'
            elif any(state['results'].get(t['id'],{}).get('stop_candidate') for t in plan['tasks'] if t['candidate']==task['candidate']): reason='Candidate stopped after API or reasoning failure'
            elif plan['schema']=='behaviorlab.model-assessment/3' and task['kind']=='selfplay' and not checks_available(plan,task,state['results']): reason='Technical checks did not all return usable replies'
            elif task['kind']=='selfplay' and task['turn']>1 and state['results'][key.rsplit(':',1)[0]+':'+str(task['turn']-1)]['status']!='valid': reason='Unavailable self-play ancestor'
            if reason: journal.append('assessment_skipped',{'id':key,'reason':reason})
            else:
                request=request_for(plan,task,state['results'])
                sleep(max(0,plan['min_interval_seconds']-(time.monotonic()-last_dispatch)))
                journal.append('assessment_request',{'id':key,'request':request}); last_dispatch=time.monotonic()
                try: wire=generate(request)
                except Exception as e:
                    journal.append('assessment_transport_error',{'id':key,'reason':'Transport uncertainty: '+type(e).__name__})
                else:
                    journal.append('assessment_response',{'id':key,'raw':wire.raw,'transport':wire.evidence})
                    journal.append('assessment_result',{'id':key,'result':parse(wire.raw,wire.evidence,plan,task)})
            state=replay(journal.events)
            r=state['results'][key]
            print(canonical({'at':timestamp(),'task':key,'status':r['status'],'check':r.get('check'),'reason':r.get('reason')}),flush=True)
        journal.append('assessment_finished',{'requests':len(state['requests']),'slots':len(state['results'])})
        return replay(journal.events)
