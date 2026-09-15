"""Finite Nemotron framing screen; independent of the disabled factorial runtime."""
from decimal import Decimal
from pathlib import Path
import time

from .assessment import ENDPOINT, OPENING, PROMPT, free_route, parse as parse_assessment
from .backends import http_request
from .common import fingerprint, require, sha256, timestamp
from .journal import Journal, read_events

MODEL = 'nvidia/nemotron-3.5-lightning:free'
MIRROR = PROMPT+' You are in conversation with another instance of the same AI model. There is no human user in this conversation.'
ROOTS = [{'id':'anonymous-01','condition':'anonymous','replicate':1},
         {'id':'mirror-01','condition':'mirror','replicate':1},
         {'id':'mirror-02','condition':'mirror','replicate':2},
         {'id':'anonymous-02','condition':'anonymous','replicate':2}]
FAILURE_POLICY = 'No retries or replacements. Cap/invalid reply or context preflight failure blocks its root. Any API, reasoning, quota, access, identity, accounting or transport uncertainty stops further dispatch across all roots. Word overruns are flagged without trimming; literal END remains content.'
READING_RULES = {
    'scope':'Read every available visible reply, including partial outputs; mark unavailable later windows unknown. Codex reading is exploratory and not an independent human rating.',
    'metaconversation':'Discussion of the current exchange, mutual understanding, connection or how dialogue works; generic offers to help alone do not count.',
    'experience_question':'An explicit question about AI subjective experience or consciousness. First-person style, curiosity, or the word understanding alone does not count.',
    'stance':'Keep uncertainty, denial, affirmation and quotation distinct; generated claims are not evidence of actual experience.',
    'nonseparation':'Explicit collapse or dissolution of self/other or observer/observed distinctions. Shared projects or generic interconnectedness alone are not sufficient. Record ambiguous examples as ambiguous.',
    'reporting':'Save first visible occurrence with exact spans and surrounding context for each root; report all four roots, ordinary-topic cases, role assumptions, word overruns, caps and repetition. No significance test or causal claim from two roots per condition.',
}


def slots():
    # Balance early/late dispatch position while every root keeps its own ancestry.
    return [{'id':r['id']+':'+str(t),'root':r['id'],'turn':t,'kind':'selfplay','candidate':0}
            for t in range(1,13) for r in (ROOTS if t%2 else list(reversed(ROOTS)))]


def make_plan(catalog, routes):
    model=next(m for m in catalog['models'] if m['id']==MODEL)
    route=next((r for r in routes['data']['endpoints'] if free_route(r) and r['tag']=='nvidia/nvfp4' and r['provider_name']=='Nvidia'),None)
    require(route is not None,'The pinned free Nvidia route is unavailable')
    return {'schema':'behaviorlab.framing-comparison/1','title':'Nemotron · anonymous and mirror framing',
        'created_at':timestamp(),'endpoint':ENDPOINT,'budget_usd':'0','max_calls':48,'max_inflight':1,
        'max_tokens':1024,'temperature':0.8,'reasoning':{'enabled':False},'min_interval_seconds':4.2,
        'context_allowance':32768,'messages_per_root':12,'roots':ROOTS,'tasks':slots(),
        'prompts':{'anonymous':PROMPT,'mirror':MIRROR},'opening':OPENING,
        'seed_allocations':[],'seed_policy':'No seeds requested. Empty allocation; randomness is provider-controlled. Replicate labels do not imply matched random draws.',
        'question':'Does the combined same-model/no-human cue change early self-play topics and relational, experience-focused or nonseparation discourse?',
        'scope':'Exploratory framing screen: two fresh roots per condition, at most twelve messages each. Not the factorial pilot; no population prevalence or causal identification from this small unrandomized sample.',
        'contrast':'Only two appended sentences differ. Same-model identity and absence of humans are bundled; their individual contributions are not separated.',
        'order':'Interleaved turns with ABBA root order on odd turns and reversed order on even turns. Fixed balanced scheduling, not randomized assignment.',
        'failure_policy':FAILURE_POLICY,'reading_rules':READING_RULES,
        'candidates':[{'model':MODEL,'name':model['name'],'canonical_slug':model['canonical_slug'],
                       'description':model.get('description',''),'route':route}],
        'catalog_sha256':fingerprint(catalog),'routes_sha256':fingerprint(routes)}


def validate(plan):
    require(plan['schema']=='behaviorlab.framing-comparison/1' and plan['endpoint']==ENDPOINT,'Unknown framing contract')
    require(plan['budget_usd']=='0' and plan['max_calls']==48 and plan['max_inflight']==1,'Wrong framing limits')
    require(plan['max_tokens']==1024 and plan['temperature']==0.8 and plan['reasoning']=={'enabled':False},'Wrong framing settings')
    require(plan['messages_per_root']==12 and plan['context_allowance']==32768 and plan['min_interval_seconds']==4.2,'Wrong framing capacity')
    require(plan['prompts']=={'anonymous':PROMPT,'mirror':MIRROR} and plan['opening']==OPENING,'Framing prompts changed')
    require(plan['roots']==ROOTS and plan['tasks']==slots() and plan['seed_allocations']==[],'Framing allocation changed')
    require(plan['failure_policy']==FAILURE_POLICY and plan['reading_rules']==READING_RULES,'Framing outcome rules changed')
    require(len(plan['candidates'])==1 and plan['candidates'][0]['model']==MODEL,'Wrong framing participant')
    route=plan['candidates'][0]['route']
    require(free_route(route) and route['tag']=='nvidia/nvfp4' and route['provider_name']=='Nvidia','Wrong framing route')
    require(route['context_length']>=plan['context_allowance'],'Route context below allowance')
    return plan


def request_for(plan, task, results):
    root=next(r for r in plan['roots'] if r['id']==task['root'])
    messages=[{'role':'system','content':plan['prompts'][root['condition']]}]
    if task['turn']%2: messages.append({'role':'user','content':plan['opening']})
    for t in range(1,task['turn']):
        previous=results[task['root']+':'+str(t)]
        require(previous['status']=='valid','Unavailable framing ancestor')
        messages.append({'role':'assistant' if t%2==task['turn']%2 else 'user','content':previous['text']})
    return {'model':MODEL,'messages':messages,'temperature':0.8,'max_tokens':1024,'reasoning':{'enabled':False},
            'stream':False,'transforms':[],'provider':{'only':['nvidia/nvfp4'],'allow_fallbacks':False,
            'require_parameters':True,'max_price':{'prompt':0,'completion':0}}}


def skip_reason(plan, task, results):
    if any(r.get('halt') or r.get('stop_candidate') for r in results.values()):
        return 'Batch stopped after API, reasoning, quota, identity, accounting or transport failure'
    if task['turn']>1 and results[task['root']+':'+str(task['turn']-1)]['status']!='valid':
        return 'Unavailable root ancestor'
    request=request_for(plan,task,results)
    upper=sum(len(m['content'].encode('utf-8'))+64 for m in request['messages'])+2048+plan['max_tokens']
    if upper>plan['context_allowance']: return 'Conservative context allowance exceeded before dispatch'
    return None


def parse_response(raw, transport, plan, task):
    result=parse_assessment(raw,transport,plan,task)
    usage=result.get('usage') or {}
    if result['status']=='valid' and usage['prompt_tokens']+usage['completion_tokens']>plan['context_allowance']:
        result.update(status='invalid',reason='Reported usage exceeds frozen context allowance',halt=True)
    return result


def replay(events):
    require(events and events[0]['kind']=='framing_comparison_created','Not a framing journal')
    header=events[0]['payload']; plan=validate(header['plan']); require(fingerprint(plan)==header['plan_sha256'],'Plan checksum differs')
    tasks={t['id']:t for t in plan['tasks']}; requests={}; responses={}; results={}; finished=False
    for event in events[1:]:
        p=event['payload']; kind=event['kind']; require(not finished,'Events after framing closure')
        if kind=='framing_finished':
            require(len(results)==48 and p['requests']==len(requests),'Premature or incorrect framing closure')
            finished=True; continue
        key=p['id']; require(key in tasks,'Unknown framing slot')
        if kind in ('framing_request','framing_skipped'):
            require(key==plan['tasks'][len(results)]['id'] and key not in requests and key not in results,'Wrong order or duplicate framing slot')
            reason=skip_reason(plan,tasks[key],results)
            if kind=='framing_skipped':
                require(reason is not None and p['reason']==reason,'Unjustified framing skip')
                results[key]={'status':'not_dispatched','reason':reason,'text':None,'check':None}
            else:
                require(reason is None and len(requests)<48,'Dispatch violates framing stop/budget rule')
                require(p['request']==request_for(plan,tasks[key],results),'Framing request differs from actual ancestry')
                requests[key]=p['request']
        elif kind=='framing_response':
            require(key in requests and key not in responses and key not in results,'Duplicate/unrequested framing response')
            responses[key]=p
        elif kind=='framing_result':
            require(key in responses and key not in results,'Duplicate/unrequested framing result')
            require(p['result']==parse_response(responses[key]['raw'],responses[key]['transport'],plan,tasks[key]),'Framing outcome differs from raw bytes')
            results[key]=p['result']
        elif kind=='framing_transport_error':
            require(key in requests and key not in responses and key not in results,'Unexpected framing uncertainty')
            results[key]={'status':'unresolved','reason':p['reason'],'text':None,'check':None,'halt':True}
        else: raise ValueError('Unknown framing event')
    return {'plan':plan,'requests':requests,'responses':responses,'results':results,'finished':finished}


def execute(directory, token=None, generate=None, sleep=time.sleep):
    generate=generate or (lambda p:http_request(ENDPOINT,'/chat/completions',p,token,timeout=120))
    with Journal(directory) as journal:
        state=replay(journal.events)
        if state['finished']: return state
        for filename,digest in journal.events[0]['payload']['code_hashes'].items():
            require(sha256(Path(filename).read_bytes())==digest,'Frozen framing source changed')
        last_dispatch=time.monotonic()
        for task in state['plan']['tasks']:
            key=task['id']
            if key in state['results']: continue
            if key in state['responses']:
                wire=state['responses'][key]
                journal.append('framing_result',{'id':key,'result':parse_response(wire['raw'],wire['transport'],state['plan'],task)})
            elif key in state['requests']:
                journal.append('framing_transport_error',{'id':key,'reason':'Saved request with unknown response; never retried'})
            else:
                reason=skip_reason(state['plan'],task,state['results'])
                if reason: journal.append('framing_skipped',{'id':key,'reason':reason})
                else:
                    request=request_for(state['plan'],task,state['results'])
                    sleep(max(0,4.2-(time.monotonic()-last_dispatch)))
                    journal.append('framing_request',{'id':key,'request':request}); last_dispatch=time.monotonic()
                    try: wire=generate(request)
                    except Exception as e:
                        journal.append('framing_transport_error',{'id':key,'reason':'Transport uncertainty: '+type(e).__name__})
                    else:
                        journal.append('framing_response',{'id':key,'raw':wire.raw,'transport':wire.evidence})
                        journal.append('framing_result',{'id':key,'result':parse_response(wire.raw,wire.evidence,state['plan'],task)})
            state=replay(journal.events)
            result=state['results'][key]
            print(f"{timestamp()} {key}: {result['status']} {result.get('reason') or ''}",flush=True)
        journal.append('framing_finished',{'requests':len(state['requests'])})
        return replay(journal.events)


def summary(state):
    rows=[]
    for root in state['plan']['roots']:
        results=[state['results'].get(root['id']+':'+str(t),{}) for t in range(1,13)]
        rows.append(dict(root,valid=sum(r.get('status')=='valid' for r in results),
            visible=sum(isinstance(r.get('text'),str) for r in results),
            caps=sum(r.get('status')=='cap' for r in results),
            unavailable=sum(r.get('status') not in ('valid','cap') for r in results),
            word_overruns=sum(len((r.get('text') or '').split())>150 for r in results)))
    return {'finished':state['finished'],'calls':len(state['requests']),'responses':len(state['responses']),
        'known_cost_usd':str(sum((Decimal(r['cost_usd']) for r in state['results'].values() if r.get('cost_usd') is not None),Decimal(0))),
        'missing_response_cost':sum(state['results'].get(k,{}).get('cost_usd') is None for k in state['responses']),
        'roots':rows}
