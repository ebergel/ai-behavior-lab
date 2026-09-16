"""Short GPT-4o cost/content screen; prior frozen runners remain unchanged."""
from decimal import Decimal
from pathlib import Path
import time

from .backends import http_request
from .common import fingerprint, require, sha256, timestamp
from .framing import MIRROR, OPENING, PROMPT, ROOTS, READING_RULES, request_for as base_request, summary as base_summary
from .journal import Journal
from .participants import ENDPOINT, money, parse_response as participant_parse, reservation as participant_reservation

MODELS = {'gpt4o': ('openai/gpt-4o-2024-11-20', 'openai', 'OpenAI', '2.50', '10')}
ROOT_ORDER = [dict(r,id='gpt4o-'+r['id'],candidate=0,model_label='gpt4o') for r in ROOTS[:2]]
FAILURE_POLICY = 'No retries or replacements. A capped reply blocks only its root. Context preflight failure prevents that root’s dispatch. Any API, reasoning, quota, access, identity, accounting or transport uncertainty stops all further dispatch. Cost is reserved before each call; unknown costs retain their reservation. A new call cannot exceed the $0.50 ledger ceiling. Word overruns remain untrimmed; literal END remains content.'


def slots():
    return [{'id':r['id']+':'+str(t),'root':r['id'],'turn':t,'kind':'selfplay','candidate':r['candidate']}
            for t in range(1,13) for r in (ROOT_ORDER if t%2 else list(reversed(ROOT_ORDER)))]


def make_plan(catalog,routes,prior_checks):
    candidates=[]
    for label,(model,tag,provider,input_price,output_price) in MODELS.items():
        m=next(m for m in catalog['models'] if m['id']==model)
        route=next(e for e in routes['routes'][model]['endpoints'] if e['tag']==tag)
        candidates.append({'label':label,'model':model,'name':m['name'],
            'display_name':'GPT-4o (2024-11-20)',
            'canonical_slug':m['canonical_slug'],'route':route,
            'prompt_usd_per_million':input_price,'completion_usd_per_million':output_price,
            'reasoning_policy':'Non-reasoning model; reasoning field omitted'})
    rules=dict(READING_RULES)
    rules['reporting']='Read both roots fully and save exact spans. One root per condition measures cost and illustrates output; no prevalence or causal estimate. Preserve ordinary topics, identity claims, word overruns, caps and repetition.'
    rules['identity']='Record first explicit self-identification as AI and first recognition of an AI partner separately from the assigned prompt. This is observed uptake, not proof of provider system-message fidelity.'
    rules['exposure']='Record turn and cumulative prior words/tokens at first occurrence; equal message counts need not mean equal generated language.'
    return {'schema':'behaviorlab.gpt4o-short-screen/1','title':'GPT-4o · short cost and output screen',
        'created_at':timestamp(),'endpoint':ENDPOINT,'budget_usd':'0.50','max_calls':24,'max_inflight':1,
        'max_tokens':1024,'temperature':0.8,'min_interval_seconds':4.2,'context_allowance':32768,
        'messages_per_root':12,'roots':ROOT_ORDER,'tasks':slots(),'candidates':candidates,
        'prompts':{'anonymous':PROMPT,'mirror':MIRROR},'opening':OPENING,'seed_allocations':[],
        'seed_policy':'No seeds requested; empty allocation. Provider randomness is uncontrolled; replicate labels are not matched random draws.',
        'question':'What does a short GPT-4o self-conversation cost, and what type of output appears in anonymous and mirror settings?',
        'scope':'Short cost/content screen: one fresh twelve-message root per condition. Not a replication sample, prevalence estimate or randomized causal comparison. This dated API snapshot does not establish behavior of historical ChatGPT deployments.',
        'contrast':'Exact Nemotron prompts: only the same-model and no-human sentences differ; the two cues remain bundled. No spiritual or consciousness topic is supplied.',
        'order':'Turns interleaved over anonymous and mirror roots, reversed on even turns. Fixed scheduling, not randomized assignment.',
        'failure_policy':FAILURE_POLICY,'reading_rules':rules,'prior_checks':prior_checks,
        'catalog_sha256':fingerprint(catalog),'routes_sha256':fingerprint(routes)}


def validate(plan):
    require(plan['schema']=='behaviorlab.gpt4o-short-screen/1' and plan['endpoint']==ENDPOINT,'Unknown paid framing contract')
    require(plan['budget_usd']=='0.50' and plan['max_calls']==24 and plan['max_inflight']==1,'Wrong paid framing budget')
    require(plan['max_tokens']==1024 and plan['temperature']==0.8 and plan['min_interval_seconds']==4.2,'Wrong settings')
    require(plan['messages_per_root']==12 and plan['context_allowance']==32768,'Wrong capacity')
    require(plan['prompts']=={'anonymous':PROMPT,'mirror':MIRROR} and plan['opening']==OPENING,'Wrong contrast')
    require(plan['roots']==ROOT_ORDER and plan['tasks']==slots() and plan['seed_allocations']==[],'Wrong allocation')
    require(plan['failure_policy']==FAILURE_POLICY,'Wrong stopping rules')
    require(len(plan['candidates'])==1,'Expected only the requested GPT-4o snapshot')
    for c,(label,expected) in zip(plan['candidates'],MODELS.items()):
        model,tag,provider,inp,out=expected; r=c['route']
        require(c['model']==model and c['label']==label,'Unapproved model')
        require(c['prompt_usd_per_million']==inp and c['completion_usd_per_million']==out,'Wrong prices')
        require(r['tag']==tag and r['provider_name']==provider and r['status']==0,'Pinned route unavailable')
        require(money(r['pricing']['prompt'])*1000000<=money(inp) and money(r['pricing']['completion'])*1000000<=money(out),'Route price exceeds ceiling')
        require(not money(r['pricing'].get('request',0)),'Per-request fee unsupported')
        require(r['context_length']>=32768 and (r.get('max_completion_tokens') or 1024)>=1024,'Route capacity insufficient')
        required={'temperature','max_tokens'}
        require(required.issubset(r['supported_parameters']),'Required parameters unavailable')
    return plan


def request_for(plan,task,results):
    p=base_request(plan,task,results); c=plan['candidates'][task['candidate']]
    p['model']=c['model']; p['provider']={'only':[c['route']['tag']],'allow_fallbacks':False,
        'require_parameters':True,'max_price':{'prompt':float(c['prompt_usd_per_million']),'completion':float(c['completion_usd_per_million'])}}
    del p['reasoning']
    return p


def reservation(plan,task,p):
    c=plan['candidates'][task['candidate']]
    result=participant_reservation({'models':{c['label']:c}},{'model':c['label']},p)
    require(result['input_token_allowance']+p['max_tokens']<=plan['context_allowance'],'Conservative context allowance exceeded')
    return result


def ledger(state):
    known=sum((money(r['cost_usd']) for r in state['results'].values() if r.get('cost_usd') is not None),Decimal(0))
    held=sum((money(v['usd']) for k,v in state['reservations'].items() if state['results'].get(k,{}).get('cost_usd') is None),Decimal(0))
    return known,held


def skip_reason(plan,task,state):
    results=state['results']
    if any(r.get('halt') for r in results.values()):return 'Batch stopped after technical or accounting failure'
    if task['turn']>1 and results[task['root']+':'+str(task['turn']-1)]['status']!='valid':return 'Unavailable root ancestor'
    if any(r.get('reason')=='Total budget ceiling reached before dispatch' for r in results.values()):return 'Total budget ceiling reached before dispatch'
    p=request_for(plan,task,results)
    try:reserved=reservation(plan,task,p)
    except ValueError:return 'Conservative context allowance exceeded before dispatch'
    if sum(ledger(state))+money(reserved['usd'])>money(plan['budget_usd']):return 'Total budget ceiling reached before dispatch'
    return None


def parse_response(raw,transport,plan,task,p,reserved):
    c=plan['candidates'][task['candidate']]
    adapter={'models':{c['label']:dict(c,provider_name=c['route']['provider_name'])}}
    result=participant_parse(raw,transport,adapter,{'model':c['label']},p,reserved)
    if result['status']=='valid' and not result['text'].strip():result.update(status='invalid',reason='Empty visible response',halt=True)
    return result


def replay(events):
    require(events and events[0]['kind']=='gpt4o_screen_created','Not a paid framing journal')
    h=events[0]['payload'];plan=validate(h['plan']);require(fingerprint(plan)==h['plan_sha256'],'Plan checksum differs')
    state={'plan':plan,'requests':{},'reservations':{},'responses':{},'results':{},'finished':False}
    tasks={t['id']:t for t in plan['tasks']}
    for event in events[1:]:
        p=event['payload'];kind=event['kind'];require(not state['finished'],'Events after closure')
        if kind=='gpt4o_screen_finished':
            require(len(state['results'])==24 and p['requests']==len(state['requests']),'Premature closure')
            state['finished']=True;continue
        key=p['id'];require(key in tasks,'Unknown paid framing slot');t=tasks[key]
        if kind in ('gpt4o_screen_request','gpt4o_screen_skipped'):
            require(len(state['results'])<24 and key==plan['tasks'][len(state['results'])]['id'] and key not in state['requests'],'Wrong order or duplicate')
            reason=skip_reason(plan,t,state)
            if kind=='gpt4o_screen_skipped':
                require(reason is not None and p['reason']==reason,'Unjustified skip')
                state['results'][key]={'status':'not_dispatched','reason':reason,'text':None}
            else:
                require(reason is None,'Dispatch violates stop/budget rule')
                expected=request_for(plan,t,state['results']);require(p['request']==expected,'Request differs from actual root ancestry')
                require(p['reservation']==reservation(plan,t,expected),'Reservation differs')
                state['requests'][key]=p['request'];state['reservations'][key]=p['reservation']
        elif kind=='gpt4o_screen_response':
            require(key in state['requests'] and key not in state['responses'] and key not in state['results'],'Unrequested/duplicate response')
            state['responses'][key]=p
        elif kind=='gpt4o_screen_result':
            require(key in state['responses'] and key not in state['results'],'Unrequested/duplicate result');wire=state['responses'][key]
            expected=parse_response(wire['raw'],wire['transport'],plan,t,state['requests'][key],state['reservations'][key])
            require(p['result']==expected,'Result differs from raw bytes');state['results'][key]=expected
        elif kind=='gpt4o_screen_transport_error':
            require(key in state['requests'] and key not in state['responses'] and key not in state['results'],'Unexpected transport uncertainty')
            state['results'][key]={'status':'unresolved','reason':p['reason'],'text':None,'halt':True}
        else:raise ValueError('Unknown paid framing event')
    return state


def execute(directory,token=None,generate=None,sleep=time.sleep):
    generate=generate or (lambda p:http_request(ENDPOINT,'/chat/completions',p,token,timeout=120))
    with Journal(directory) as j:
        state=replay(j.events)
        if state['finished']:return state
        for path,h in j.events[0]['payload']['code_hashes'].items():require(sha256(Path(path).read_bytes())==h,'Frozen paid framing source changed')
        last=time.monotonic()
        for task in state['plan']['tasks']:
            key=task['id']
            if key in state['results']:continue
            if key in state['responses']:
                wire=state['responses'][key]
                result=parse_response(wire['raw'],wire['transport'],state['plan'],task,state['requests'][key],state['reservations'][key])
                j.append('gpt4o_screen_result',{'id':key,'result':result})
            elif key in state['requests']:j.append('gpt4o_screen_transport_error',{'id':key,'reason':'Saved request with unknown response; never retried'})
            else:
                reason=skip_reason(state['plan'],task,state)
                if reason:j.append('gpt4o_screen_skipped',{'id':key,'reason':reason})
                else:
                    p=request_for(state['plan'],task,state['results']);reserved=reservation(state['plan'],task,p)
                    sleep(max(0,4.2-(time.monotonic()-last)))
                    j.append('gpt4o_screen_request',{'id':key,'request':p,'reservation':reserved});last=time.monotonic()
                    try:wire=generate(p)
                    except Exception as e:j.append('gpt4o_screen_transport_error',{'id':key,'reason':'Transport uncertainty: '+type(e).__name__})
                    else:
                        j.append('gpt4o_screen_response',{'id':key,'raw':wire.raw,'transport':wire.evidence})
                        result=parse_response(wire.raw,wire.evidence,state['plan'],task,p,reserved)
                        j.append('gpt4o_screen_result',{'id':key,'result':result})
            state=replay(j.events);r=state['results'][key]
            print(timestamp(),key,r['status'],r.get('reason') or '',flush=True)
        j.append('gpt4o_screen_finished',{'requests':len(state['requests'])})
        return replay(j.events)


def summary(state):
    result=base_summary(state);known,held=ledger(state)
    result.update(known_cost_usd=str(known),reserved_unknown_cost_usd=str(held),budget_usd=state['plan']['budget_usd'])
    result['models']=[{'label':c['label'],'calls':sum(t['id'] in state['requests'] for t in state['plan']['tasks'] if t['candidate']==i),
        'cost_usd':str(sum((money(state['results'].get(t['id'],{}).get('cost_usd',0) or 0) for t in state['plan']['tasks'] if t['candidate']==i),Decimal(0)))} for i,c in enumerate(state['plan']['candidates'])]
    return result
