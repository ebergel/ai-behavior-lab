"""Three predeclared diagnostics; never replace the original smoke outcomes."""
from pathlib import Path
from behaviorlab.participants import OpenRouter, credential, make_plan, payload, reservation, parse_response
from behaviorlab.journal import Journal
from behaviorlab.common import fingerprint, canonical


def run(base):
    plan=make_plan(); backend=OpenRouter(credential('workspace/private/webui-token'))
    verification=backend.verify(plan)
    cases=[('haiku-system','haiku','system'),('mini-system','mini','system'),('haiku-user','haiku','user')]
    tasks=[]
    for name,label,role in cases:
        job=next(j for j in plan['jobs'] if j['model']==label and j['condition']=='smoke')
        request=payload(plan,job,1,{})
        request.update(temperature=0,max_tokens=128)
        request.pop('seed',None)
        request['messages']=([{'role':'system','content':'Reply with exactly LAB_ROUTING_OK and nothing else.'},
                              {'role':'user','content':'Compute 2+2.'}] if role=='system' else
                             [{'role':'user','content':'Reply with exactly LAB_ROUTING_OK and nothing else.'}])
        tasks.append({'id':name,'job':job,'request':request,'reservation':reservation(plan,job,request)})
    base.mkdir(exist_ok=False)
    with Journal(base,create=True) as journal:
        journal.append('cloud_instruction_diagnostic_created',{'schema':'behaviorlab.cloud-instruction-diagnostic/1',
            'question':'Does the selected OpenRouter route follow a literal instruction in system and user positions?',
            'tasks':tasks,'max_calls':3,'budget_usd':'0.01','verification':verification,
            'prior_smoke':'workspace/participants-20260915-1740','retry_policy':'none','seed_policy':'not_requested',
            'scope':'Technical diagnostic only; not participant self-play or a replacement smoke result.'})
        for task in tasks:
            journal.append('diagnostic_request',{'id':task['id'],'request_sha256':fingerprint(task['request'])})
            try: wire=backend.generate(task['request'])
            except Exception as exc:
                journal.append('diagnostic_transport_error',{'id':task['id'],'error_type':type(exc).__name__,'outcome':'unknown'});break
            journal.append('diagnostic_response',{'id':task['id'],'raw':wire.raw,'transport':wire.evidence})
            r=parse_response(wire.raw,wire.evidence,plan,task['job'],task['request'],task['reservation'])
            journal.append('diagnostic_result',{'id':task['id'],'result':r,'exact_match':r['text']=='LAB_ROUTING_OK'})
            print(canonical({'id':task['id'],'result':r,'exact_match':r['text']=='LAB_ROUTING_OK'}),flush=True)
            if r['halt']:break


if __name__=='__main__':run(Path('workspace/cloud-instruction-check-20260915-1745'))
