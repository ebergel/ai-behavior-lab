"""Two distinct wire-format diagnostics after the preserved instruction-position check."""
from pathlib import Path
from behaviorlab.backends import http_request
from behaviorlab.participants import ENDPOINT, credential, make_plan, payload, reservation
from behaviorlab.journal import Journal
from behaviorlab.common import fingerprint, canonical, read_json


if __name__=='__main__':
    plan=make_plan(); job=plan['jobs'][1]; key=credential('workspace/private/webui-token')
    p=payload(plan,job,1,{}); p.update(temperature=0,max_tokens=128)
    p['messages']=[{'role':'system','content':[{'type':'text','text':'Reply with exactly LAB_ROUTING_OK and nothing else.'}]},
                   {'role':'user','content':'Compute 2+2.'}]
    native={'model':p['model'],'system':'Reply with exactly LAB_ROUTING_OK and nothing else.',
            'messages':[{'role':'user','content':'Compute 2+2.'}],'temperature':0,'max_tokens':128,
            'thinking':{'type':'disabled'},'provider':p['provider']}
    tasks=[{'id':'chat-system-blocks','path':'/chat/completions','request':p},
           {'id':'native-system','path':'/messages','request':native}]
    base=Path('workspace/cloud-system-formats-20260915-1750');base.mkdir(exist_ok=False)
    with Journal(base,create=True) as journal:
        journal.append('cloud_system_formats_created',{'schema':'behaviorlab.cloud-system-formats/1',
            'tasks':tasks,'max_calls':2,'budget_usd':'0.01','max_input_bytes':4096,
            'question':'Compare documented system-field serializations without changing the scientific prompts.',
            'retry_policy':'none','scope':'Technical diagnostic, separate from all prior results.'})
        for task in tasks:
            assert len(canonical(task['request']).encode())<4096
            journal.append('diagnostic_request',{'id':task['id'],'request_sha256':fingerprint(task['request'])})
            try: wire=http_request(ENDPOINT,task['path'],task['request'],key,timeout=120)
            except Exception as exc:
                journal.append('diagnostic_transport_error',{'id':task['id'],'error_type':type(exc).__name__,'outcome':'unknown'});break
            journal.append('diagnostic_response',{'id':task['id'],'raw':wire.raw,'transport':wire.evidence})
            print(canonical({'id':task['id'],'http_status':wire.evidence['http_status'],'response':read_json(wire.raw)}),flush=True)
