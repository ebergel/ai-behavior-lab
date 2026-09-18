"""Separately bounded Score pilot. The Explorer never invokes this runner."""
import argparse
import json
import math
from pathlib import Path
import time

from .common import fingerprint, require
from .gem_plan import PILOT, payload, software
from .jev_atlas import MODEL, PRICE, MAX_INPUT, ENDPOINT, locked, now, read_record, write_record
from .jev_runner import credential, transport


def validate(raw, questions):
    require(isinstance(raw,dict) and raw.get('model')==MODEL,'Response model differs')
    answers=raw.get('answers');require(isinstance(answers,dict) and set(answers)==set(questions),'Answer keys differ')
    checked={}
    def finite(v,lo,hi):return type(v) in (int,float) and math.isfinite(v) and lo<=v<=hi
    for key,q in questions.items():
        a=answers[key];n=len(q['criteria']);require(isinstance(a,dict) and a.get('type')=='score','Expected Score answer')
        probs=a.get('probabilities');keys={str(i) for i in range(n)}
        require(isinstance(probs,dict) and set(probs)==keys and all(finite(v,0,1) for v in probs.values()),'Invalid level distribution')
        rounded=all(abs(v*100-round(v*100))<1e-8 for v in probs.values())
        tolerance=n*.005+1e-9 if rounded else 1e-6
        require(abs(sum(probs.values())-1)<=tolerance,'Level probabilities do not sum to one within rounding bounds')
        require(finite(a.get('score'),0,n-1) and finite(a.get('confidence'),0,1),'Invalid score or confidence')
        require(a.get('legend')=={str(i):c for i,c in enumerate(q['criteria'])},'Returned level definitions differ')
        expected=sum(i*probs[str(i)] for i in range(n))
        bound=.005*(sum(range(n))+1)+1e-9 if rounded else .005+1e-9
        require(abs(a['score']-expected)<=bound,'Score and level distribution disagree')
        checked[key]=dict(a,normalized_score=a['score']/(n-1)*100,
                          rounding_tolerated=abs(sum(probs.values())-1)>1e-6 or abs(a['score']-expected)>.005)
    usage=raw.get('usage',{});tokens=usage.get('input_tokens')
    require(type(tokens) is int and 0<tokens<=MAX_INPUT,'Missing or out-of-range input usage')
    return checked,tokens*PRICE/1_000_000


def receipts(root,plan):
    result={};attempts=[];allowed={i['id']:i for i in plan['items']}
    for path in sorted((root/'attempts').glob('*/*.request.json')):
        req=read_record(path);identity=req['item_id'];number=req['attempt']
        require(identity in allowed and path.parent.name==identity,'Unallocated request')
        require(req['plan_sha256']==plan['sha256'] and req['payload']==payload(plan,allowed[identity]),'Request differs from frozen payload')
        require(type(number) is int and 1<=number<=plan['budget']['max_attempts_per_item'] and path.name==f'{number:02d}.request.json','Invalid attempt number')
        rows=result.setdefault(identity,[])
        require(number==len(rows)+1 and (not rows or rows[-1]['status']=='overload'),'Unallocated retry or duplicate success')
        row={'item_id':identity,'attempt':number,'status':'unresolved','cost_usd':None,
             'reserved_usd':MAX_INPUT*PRICE/1_000_000,'answers':{},'request_sha256':req['sha256']}
        respath=path.with_name(f'{number:02d}.response.json')
        if respath.exists():
            res=read_record(respath);row['response_sha256']=res['sha256']
            require(res['request_sha256']==req['sha256'],'Response parent differs')
            if res.get('http_status') in plan['execution']['retryable_http'] and not res.get('error'):
                row['status']='overload'
            elif res.get('http_status')==200 and not res.get('error'):
                try:row['answers'],row['cost_usd']=validate(json.loads(res['raw_text']),plan['questions']);row['status']='complete'
                except (ValueError,TypeError,KeyError):row['status']='invalid'
            else:row['status']='error'
        rows.append(row);attempts.append(row)
    require(len(attempts)<=plan['budget']['max_attempts'],'Aggregate attempt allocation exceeded')
    require(sum(max(0,len(rows)-1) for rows in result.values())<=plan['budget']['retry_allowance'],'Retry allocation exceeded')
    return result,attempts


def summary(root,plan):
    rows,attempts=receipts(root,plan);complete=sum(r[-1]['status']=='complete' for r in rows.values())
    stopped=[r[-1]['status'] for r in rows.values() if r[-1]['status'] in ('unresolved','invalid','error')]
    return {'planned':len(plan['items']),'complete':complete,'attempts':len(attempts),'stopped':stopped,
            'known_cost_usd':sum(r['cost_usd'] or 0 for r in attempts),
            'unknown_reserved_usd':sum(r['reserved_usd'] for r in attempts if r['cost_usd'] is None),
            'pending':len(plan['items'])-complete,'plan_sha256':plan['sha256']}


def execute(workspace,max_calls=None,send=None,key=None,sleep=time.sleep):
    root=Path(workspace)/PILOT
    with locked(root/'.runner.lock',blocking=False):
        plan=read_record(root/'plan.json');approval=read_record(root/'authorization.json')
        require(approval['plan_sha256']==plan['sha256'] and approval['usd_ceiling']==plan['budget']['usd_ceiling'],'Authorization differs from plan')
        require(plan['software_sha256']==software(),'Scoring software changed after freeze; preserve the release')
        require(plan['endpoint']==ENDPOINT and plan['model']==MODEL and 0<plan['budget']['usd_ceiling']<=2,'Unsupported route or ceiling')
        require(plan['budget']['unique_requests']==len(plan['items'])<=100 and plan['budget']['max_attempts']==len(plan['items'])+10
                and plan['budget']['retry_allowance']==10 and plan['budget']['max_attempts_per_item']==3
                and plan['budget']['usd_per_million_input']==PRICE and plan['budget']['reserved_input_tokens_per_attempt']==MAX_INPUT,'Allocation differs')
        require(plan['execution']=={'retryable_http':[429,529],'backoff_seconds':[20,40],'minimum_interval_seconds':1,'timeout_seconds':60},'Execution policy differs')
        require(max_calls is None or type(max_calls) is int and max_calls>0,'Invalid max-calls')
        rows,attempts=receipts(root,plan)
        require(not any(r['status'] in ('unresolved','invalid','error') for r in attempts),'Pilot stopped on failed or uncertain request; no automatic redispatch')
        if len(rows)==len(plan['items']) and all(r[-1]['status']=='complete' for r in rows.values()):return summary(root,plan)
        if send is None:key=credential(workspace);send=transport
        calls=0
        for item in plan['items']:
            while True:
                history=rows.get(item['id'],[])
                if history and history[-1]['status']=='complete':break
                require(len(history)<3,'Per-item overload attempts exhausted; no replacement')
                require(len(attempts)<plan['budget']['max_attempts'],'Aggregate attempt allowance exhausted')
                if history:require(sum(max(0,len(r)-1) for r in rows.values())<10,'Aggregate retry allowance exhausted')
                if max_calls is not None and calls>=max_calls:return summary(root,plan)
                committed=sum(r['cost_usd'] if r['cost_usd'] is not None else r['reserved_usd'] for r in attempts)
                reserve=MAX_INPUT*PRICE/1_000_000
                require(committed+reserve<=plan['budget']['usd_ceiling'],'Insufficient budget reservation')
                raw=payload(plan,item)
                require(fingerprint(raw)==item['request_sha256'],'Frozen request changed')
                if history:sleep(plan['execution']['backoff_seconds'][len(history)-1])
                elif calls:sleep(1)
                attempt=len(history)+1;prefix=root/'attempts'/item['id'];reqpath=prefix/f'{attempt:02d}.request.json'
                write_record(reqpath,{'at':now(),'plan_sha256':plan['sha256'],'item_id':item['id'],'attempt':attempt,
                                      'payload':raw,'reserved_usd':reserve})
                req=read_record(reqpath);res={'at':now(),'request_sha256':req['sha256'],'http_status':None,'raw_text':'','error':None}
                start=time.monotonic()
                try:
                    res['http_status'],res['raw_text']=send(raw,key)
                    if key and key in res['raw_text']:
                        res['raw_text']=res['raw_text'].replace(key,'[credential removed]');res['error']='Credential echoed; response excluded'
                except Exception:res['error']='Transport failed after dispatch; provider usage unknown'
                res['elapsed_seconds']=round(time.monotonic()-start,4)
                write_record(prefix/f'{attempt:02d}.response.json',res);calls+=1
                rows,attempts=receipts(root,plan);status=rows[item['id']][-1]['status']
                print(json.dumps(dict(summary(root,plan),latest_status=status)),flush=True)
                if status in ('unresolved','invalid','error'):return summary(root,plan)
        result=summary(root,plan)
        if not (root/'summary.json').exists():write_record(root/'summary.json',dict(result,at=now()))
        return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',default='workspace');p.add_argument('--max-calls',type=int)
    args=p.parse_args();print(json.dumps(execute(args.workspace,args.max_calls),indent=2))


if __name__=='__main__':main()
