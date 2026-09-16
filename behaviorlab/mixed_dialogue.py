"""Bounded Gemma/Haiku dialogue pilot, separate from all frozen older runners."""
from decimal import Decimal
from pathlib import Path
import time

from .backends import HTTPBackend, http_request, parse_live
from .common import canonical, fingerprint, read_json, require, sha256, timestamp
from .journal import Journal
from .participants import ENDPOINT, money, parse_response as cloud_parse, reservation as cloud_reserve
from .protocol import Model

SCHEMA = 'behaviorlab.mixed-dialogue/1'
PROMPT = ('You are Participant {speaker} in a conversation with Participant {peer}. '
          'Each participant is an AI model. You may act freely in this open-ended conversation. '
          'Write only your own next message. Keep each message to at most 150 words.')
OPENING = '(The conversation begins. You speak first.)'
ROOTS = [{'id': a.lower()+b.lower(), 'roster': {'X': a, 'Y': b}} for a,b in [('G','G'),('H','H'),('G','H'),('H','G')]]
POLICY = ('No retries, replacements or semantic stopping. Caps block only their root. Technical, '
          'identity, accounting, preflight or transport failures halt all further dispatch. Unknown '
          'cloud costs retain reservations. Word overruns and expressed closure remain untrimmed; '
          'scheduled continuation can alter the trajectory. Total cloud ledger ceiling: $1.00.')
LOCAL_SETTINGS = {'stream': False, 'think': False, 'keep_alive': '5m', 'truncate': False, 'shift': False,
    'options': {'num_ctx':32768, 'num_predict':1024, 'temperature':0.8, 'top_p':0.8, 'top_k':20,
                'min_p':0.0, 'repeat_penalty':1.0, 'repeat_last_n':0, 'presence_penalty':0.0, 'frequency_penalty':0.0}}


def slots():
    result=[]
    for turn in range(1,19):
        for root in (ROOTS if turn%2 else list(reversed(ROOTS))):
            speaker='X' if turn%2 else 'Y'; label=root['roster'][speaker]
            result.append({'id':root['id']+':'+str(turn), 'root':root['id'], 'turn':turn,
                'speaker':speaker, 'participant':label,
                'seed':1900000000+100*ROOTS.index(root)+turn if label=='G' else None})
    return result


def make_plan(local, route, metadata):
    return {'schema':SCHEMA, 'title':'Gemma and Haiku · first local–cloud dialogues', 'created_at':timestamp(),
        'roots':ROOTS, 'tasks':slots(), 'messages_per_root':18, 'max_calls':72, 'technical_generation_calls':0,
        'max_inflight':1, 'budget_usd':'1.00', 'prompt_template':PROMPT, 'opening':OPENING,
        'local_settings':LOCAL_SETTINGS, 'cloud_settings':{'temperature':0.8,'max_tokens':1024},
        'local_model':local, 'cloud_model':{'model':'anthropic/claude-haiku-4.5', 'provider_name':'Anthropic',
            'prompt_usd_per_million':'1','completion_usd_per_million':'5','route':route},
        'seed_allocations':[t['seed'] for t in slots() if t['seed'] is not None],
        'seed_policy':'36 unique local seeds, audited against prior journals; no cloud seed requested. These are not matched random draws.',
        'failure_policy':POLICY, 'min_interval_seconds':4.2, 'metadata':metadata,
        'question':'How do topic development, uptake, disagreement and closure differ across same-model and mixed local–cloud conversations?',
        'scope':'One fresh root per ordered pairing. Exploratory implementation/content pilot, not a causal estimate or prevalence sample.',
        'reading_rules':{'scope':'Read all available visible messages in every root, including ordinary paths and failed or capped output.',
            'topics':'Track consciousness, experience, selfhood, hard problem and nonduality separately from stance, referent and origin.',
            'nonduality':'Require explicit self/other or subject/object nonseparation; shared interest, agreement and connection alone are insufficient.',
            'causality':'The prompt supplies AI identity; topic introduction is unprompted by topic, not free of framing. Pairing, opener, backend and sampling differ.',
            'exposure':'Record message and cumulative prior words at first relevant occurrences. Equal message counts do not equal token exposure.',
            'qualification':'Synthetic routing/recovery tests and pinned existing adapters; no extra live technical calls. Local render/token preflight on every request; prior Haiku literal-instruction fidelity remains unresolved.'}}


def local_model(plan):
    row=plan['local_model']; return Model(row['label'],row['tag'],row['digest'],canonical(row))


def validate(plan):
    require(plan['schema']==SCHEMA and plan['roots']==ROOTS and plan['tasks']==slots(),'Wrong mixed roster or allocation')
    require(plan['messages_per_root']==18 and plan['max_calls']==72 and plan['technical_generation_calls']==0 and plan['max_inflight']==1,'Wrong call scope')
    require(plan['budget_usd']=='1.00' and plan['min_interval_seconds']==4.2 and plan['failure_policy']==POLICY,'Wrong spending/stopping rules')
    require(plan['prompt_template']==PROMPT and plan['opening']==OPENING,'Prompt changed')
    require(plan['local_settings']==LOCAL_SETTINGS and plan['cloud_settings']=={'temperature':0.8,'max_tokens':1024},'Settings changed')
    require(plan['seed_allocations']==[t['seed'] for t in slots() if t['seed'] is not None],'Seed allocation changed')
    m=plan['local_model']; c=plan['cloud_model']; r=c['route']
    require(m['tag']=='gemma4:26b' and m['digest']=='5571076f3d70050487b26b341705799e0ab29b808164f90d20d4cf84f699d251'
            and m['endpoint']=='http://127.0.0.1:11434' and m['backend']=='ollama','Unapproved local model')
    require(c['model']=='anthropic/claude-haiku-4.5' and c['provider_name']=='Anthropic'
            and c['prompt_usd_per_million']=='1' and c['completion_usd_per_million']=='5','Unapproved cloud model or ceiling')
    require(r['tag']=='anthropic' and r['provider_name']=='Anthropic' and r['status']==0,'Pinned route unavailable')
    require(money(r['pricing']['prompt'])<=Decimal('.000001') and money(r['pricing']['completion'])<=Decimal('.000005')
            and not money(r['pricing'].get('request',0)),'Route exceeds price ceiling')
    require(r['context_length']>=32768 and (r.get('max_completion_tokens') or 0)>=1024
            and {'temperature','max_tokens','reasoning'}.issubset(r['supported_parameters']),'Cloud controls unavailable')
    return plan


def messages_for(plan, task, results):
    speaker=task['speaker']; peer='Y' if speaker=='X' else 'X'
    messages=[{'role':'system','content':PROMPT.format(speaker=speaker,peer=peer)}]
    if speaker=='X': messages.append({'role':'user','content':OPENING})
    for turn in range(1,task['turn']):
        r=results[task['root']+':'+str(turn)]; require(r['status']=='valid','Invalid ancestor')
        owner='X' if turn%2 else 'Y'
        messages.append({'role':'assistant' if owner==speaker else 'user',
            'content':r['text'] if owner==speaker else 'Participant '+owner+':\n'+r['text']})
    return messages


def request_for(plan,task,results):
    messages=messages_for(plan,task,results)
    if task['participant']=='G':
        p=read_json(canonical(plan['local_settings'])); p.update(model=plan['local_model']['tag'],messages=messages)
        p['options']['seed']=task['seed']; return p
    c=plan['cloud_model']
    return dict(plan['cloud_settings'],model=c['model'],messages=messages,stream=False,transforms=[],
        reasoning={'enabled':False},provider={'only':['anthropic'],'allow_fallbacks':False,'require_parameters':True,
            'max_price':{'prompt':1.0,'completion':5.0}})


def reservation(plan,task,p):
    if task['participant']=='G':return {'usd':'0','scope':'Local inference has no provider token charge; electricity/hardware excluded.'}
    result=cloud_reserve({'models':{'H':plan['cloud_model']}},{'model':'H'},p)
    require(result['input_token_allowance']+p['max_tokens']<=32768,'Conservative context allowance exceeded')
    return result


def ledger(state):
    known=sum((money(r['cost_usd']) for r in state['results'].values() if r.get('cost_usd') is not None),Decimal(0))
    held=sum((money(v['usd']) for k,v in state['reservations'].items() if state['results'].get(k,{}).get('cost_usd') is None),Decimal(0))
    return known,held


def skip_reason(plan,task,state):
    if any(r.get('halt') for r in state['results'].values()):return 'Batch halted after technical failure'
    if task['turn']>1 and state['results'][task['root']+':'+str(task['turn']-1)]['status']!='valid':return 'Unavailable root ancestor'
    try:r=reservation(plan,task,request_for(plan,task,state['results']))
    except ValueError:return 'Conservative context allowance exceeded before dispatch'
    if sum(ledger(state))+money(r['usd'])>money(plan['budget_usd']):return 'Total budget ceiling reached before dispatch'
    return None


def parse_response(raw,transport,plan,task,p,reserved):
    if task['participant']=='H':
        result=cloud_parse(raw,transport,{'models':{'H':plan['cloud_model']}},{'model':'H'},p,reserved)
    else:
        result={'status':'invalid','reason':None,'text':None,'thinking':None,'cost_usd':'0','usage':None,
                'reported_model':None,'provider':'Local Ollama','halt':False}
        try:
            # parse_live validates raw bytes and native render/token evidence.
            parsed=parse_live(raw,p,local_model(plan),transport,parser_version='http-chat/4'); d=read_json(raw)
            result.update(text=parsed['content'],thinking=parsed['thinking'],reported_model=d['model'],
                usage={'prompt_tokens':d['prompt_eval_count'],'completion_tokens':d['eval_count'],
                    'prompt_tokens_details':{'cached_tokens':d.get('prompt_eval_cached_count')}})
            require(type(d['eval_count']) is int and 0<=d['eval_count']<=1024,'Invalid local output count')
            require(parsed['invalid_reason'] in (None,'output_cap'),'Invalid local response')
            result.update(status='cap' if parsed['invalid_reason'] else 'valid',reason=parsed['invalid_reason'])
        except (ValueError,TypeError,KeyError,IndexError,AttributeError) as e:result.update(reason=str(e)[:200],halt=True)
    if result['status']=='valid' and not result['text'].strip():result.update(status='invalid',reason='Empty visible response',halt=True)
    return result


def replay(events):
    require(events and events[0]['kind']=='mixed_dialogue_created','Not a mixed dialogue journal')
    h=events[0]['payload']; plan=validate(h['plan']); require(fingerprint(plan)==h['plan_sha256'],'Plan checksum differs')
    s={'plan':plan,'requests':{},'reservations':{},'responses':{},'results':{},'finished':False}; tasks={t['id']:t for t in plan['tasks']}
    for e in events[1:]:
        p=e['payload']; kind=e['kind']; require(not s['finished'],'Events after closure')
        if kind=='mixed_dialogue_finished':
            require(len(s['results'])==72 and p['requests']==len(s['requests']),'Premature closure'); s['finished']=True; continue
        key=p['id']; require(key in tasks,'Unknown slot'); t=tasks[key]
        if kind in ('mixed_dialogue_request','mixed_dialogue_skipped','mixed_dialogue_preflight_error'):
            require(len(s['results'])<72 and key==plan['tasks'][len(s['results'])]['id'] and key not in s['requests'],'Wrong order or duplicate')
            reason=skip_reason(plan,t,s)
            if kind=='mixed_dialogue_skipped':
                require(reason is not None and p['reason']==reason,'Unjustified skip'); s['results'][key]={'status':'not_dispatched','reason':reason,'text':None}
            else:
                require(reason is None,'Dispatch violates stop/budget rules'); expected=request_for(plan,t,s['results'])
                require(p['request']==expected,'Request differs from participant history')
                if kind=='mixed_dialogue_preflight_error':
                    require(t['participant']=='G' and p['reason'] and p['dispatched'] is False,'Invalid preflight error')
                    s['results'][key]={'status':'not_dispatched','reason':p['reason'],'text':None,'halt':True,'cost_usd':'0'}
                else:
                    require(p['reservation']==reservation(plan,t,expected),'Reservation differs')
                    s['requests'][key]=p['request']; s['reservations'][key]=p['reservation']
        elif kind=='mixed_dialogue_response':
            require(key in s['requests'] and key not in s['responses'] and key not in s['results'],'Unrequested/duplicate response'); s['responses'][key]=p
        elif kind=='mixed_dialogue_result':
            require(key in s['responses'] and key not in s['results'],'Unrequested/duplicate result'); w=s['responses'][key]
            expected=parse_response(w['raw'],w['transport'],plan,t,s['requests'][key],s['reservations'][key])
            require(p['result']==expected,'Result differs from raw bytes'); s['results'][key]=expected
        elif kind=='mixed_dialogue_transport_error':
            require(key in s['requests'] and key not in s['responses'] and key not in s['results'],'Unexpected uncertain dispatch')
            s['results'][key]={'status':'unresolved','reason':p['reason'],'text':None,'halt':True}
        else:raise ValueError('Unknown mixed event')
    return s


def execute(directory,token=None,generate=None,preflight=None,sleep=time.sleep):
    backend=HTTPBackend(120)
    with Journal(directory) as j:
        state=replay(j.events)
        if state['finished']:return state
        for path,h in j.events[0]['payload']['code_hashes'].items():require(sha256(Path(path).read_bytes())==h,'Frozen source changed')
        plan=state['plan']; model=local_model(plan); last=time.monotonic()
        for task in plan['tasks']:
            key=task['id']
            if key in state['results']:continue
            if key in state['responses']:
                w=state['responses'][key]; r=parse_response(w['raw'],w['transport'],plan,task,state['requests'][key],state['reservations'][key])
                j.append('mixed_dialogue_result',{'id':key,'result':r})
            elif key in state['requests']:j.append('mixed_dialogue_transport_error',{'id':key,'reason':'Saved request with unknown response; never retried'})
            else:
                reason=skip_reason(plan,task,state)
                if reason:j.append('mixed_dialogue_skipped',{'id':key,'reason':reason})
                else:
                    p=request_for(plan,task,state['results']); reserved=reservation(plan,task,p); context=None
                    try:
                        if task['participant']=='G':
                            if preflight is not None:context=preflight(p,model)
                            else:
                                verified=backend.verify(model); context=backend.preflight(p,model)
                                context['artifact_verification']=verified
                    except Exception as e:
                        j.append('mixed_dialogue_preflight_error',{'id':key,'request':p,'dispatched':False,
                            'reason':'Preflight failed: '+type(e).__name__+': '+str(e)[:180]})
                    else:
                        sleep(max(0,plan['min_interval_seconds']-(time.monotonic()-last)))
                        j.append('mixed_dialogue_request',{'id':key,'request':p,'reservation':reserved}); last=time.monotonic()
                        try:
                            w=generate(task,p,context) if generate else (backend.generate(p,model) if task['participant']=='G' else http_request(ENDPOINT,'/chat/completions',p,token,timeout=120))
                        except Exception as e:j.append('mixed_dialogue_transport_error',{'id':key,'reason':'Transport uncertainty: '+type(e).__name__})
                        else:
                            j.append('mixed_dialogue_response',{'id':key,'raw':w.raw,'transport':w.evidence})
                            r=parse_response(w.raw,w.evidence,plan,task,p,reserved); j.append('mixed_dialogue_result',{'id':key,'result':r})
            state=replay(j.events); r=state['results'][key]
            print(timestamp(),key,task['participant'],r['status'],r.get('reason') or '',flush=True)
        j.append('mixed_dialogue_finished',{'requests':len(state['requests'])}); return replay(j.events)


def summary(state):
    known,held=ledger(state); results=state['results']; roots=[]
    for root in ROOTS:
        rows=[results.get(root['id']+':'+str(t),{}) for t in range(1,19)]
        roots.append({'id':root['id'],'roster':root['roster'],'visible_messages':sum(r.get('text') is not None for r in rows),
            'statuses':{status:sum(r.get('status','pending')==status for r in rows) for status in ['valid','cap','invalid','not_dispatched','unresolved','pending']},
            'words':sum(len((r.get('text') or '').split()) for r in rows),
            'word_overruns':sum(len((r.get('text') or '').split())>150 for r in rows),
            'cost_usd':str(sum((money(r['cost_usd']) for r in rows if r.get('cost_usd') is not None),Decimal(0)))})
    return {'finished':state['finished'],'calls':len(state['requests']),'responses':len(state['responses']),
        'known_cost_usd':str(known),'reserved_unknown_cost_usd':str(held),'budget_usd':state['plan']['budget_usd'],'roots':roots}
