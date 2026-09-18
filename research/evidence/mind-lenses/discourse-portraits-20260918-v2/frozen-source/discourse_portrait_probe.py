"""Finite, separately frozen conceptual-portrait comparison for the descriptive classifier."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

from .common import canonical, fingerprint, require, sha256
from .jev_atlas import MODEL, ENDPOINT, PRICE, MAX_INPUT, locked, now, read_record, write_record, validate_response
from .jev_runner import credential, transport

ROOT='mind-lenses/discourse-portraits-20260918-v2'
PARENT_ROOT='mind-lenses/discourse-20260918-v1'
SPEC=Path(__file__).resolve().parent.parent/'designs/discourse-portraits-v2.json'
SEED='discourse-portraits-20260918-v2'
VARIANTS=('name_only','definition_only','name_and_definition','name_and_portrait')
BUDGET={'unique_requests':240,'max_attempts':252,'retry_allowance':12,'max_attempts_per_item':3,'usd_ceiling':2.0,
        'usd_per_million_input':PRICE,'reserved_input_tokens_per_attempt':MAX_INPUT}
EXECUTION={'retryable_http':[429,529],'backoff_seconds':[20,40],'minimum_interval_seconds':.25,'timeout_seconds':60}


def software():
    return {**{n:sha256(Path(__file__).with_name(n).read_bytes()) for n in
            ('discourse_portrait_probe.py','common.py','jev_atlas.py','jev_runner.py')},SPEC.name:sha256(SPEC.read_bytes())}


def questions(spec,variant):
    require(variant in VARIANTS,'Unknown wording condition')
    result={}
    for f in spec['features']:
        task='Does the target passage exhibit the pattern described below?'
        if variant=='name_only':
            body=f"Does the target passage exhibit a way of thinking, literary form, or discourse practice associated with this label?\nLabel: {f['name']}"
        else:
            pattern=(f['portrait']+'\nWhat to recognize: '+f['recognition']) if variant=='name_and_portrait' and f.get('portrait') else f['definition']
            body=task+'\nPattern: '+pattern
            if variant in ('name_and_definition','name_and_portrait'):body+='\nLabel: '+f['name']
        result[f['id']]={'type':'noul','instructions':spec['scope']+'\n'+body}
    return result


def payload(plan,item):
    sample=next(s for s in plan['samples'] if s['id']==item['sample_id'])
    return {'model':plan['model'],'state':{'target_passage':sample['text']},'questions':plan['conditions'][item['variant']]}


def prepare(workspace):
    from .explorer import Catalog
    workspace=Path(workspace);root=workspace/ROOT;require(not root.exists(),'Probe already frozen; preserve it')
    spec=json.loads(SPEC.read_text());parent=read_record(workspace/PARENT_ROOT/'plan.json')
    require(not list((workspace/PARENT_ROOT/'attempts').glob('*/*.request.json')),'Prior screen has live attempts; a reuse release is required')
    require(spec['scope']==parent['spec']['scope'] and spec['controls']==parent['spec']['controls'],'Shared inputs changed')
    require(len(spec['features'])==27 and sum('portrait' in f for f in spec['features'])==16,'Expected 16 portraits among 27 features')
    for old,new in zip(parent['spec']['features'],spec['features']):
        require(all(new[k]==v for k,v in old.items()),'Original feature changed')
    samples=parent['samples'];require(len(samples)==60,'Parent sample differs')
    catalog=Catalog(workspace)
    for sample in samples:
        if sample['kind']!='transcript':continue
        run=catalog.runs[sample['run_id']];message=next(m for m in run['messages'] if m['id']==sample['message_id'])
        require(run['source']['sha256']==sample['source_sha256'] and message['text']==sample['text'],'Source changed')
        require(sample['lineage'] not in parent['selection']['reserved_lineages'],'Reserved lineage')
    conditions={v:questions(spec,v) for v in VARIANTS}
    require(all(conditions[v]==q for v,q in parent['conditions'].items()),'Baseline question changed')
    require(all(conditions['name_and_portrait'][f['id']]==conditions['name_and_definition'][f['id']] for f in spec['features'] if f['family']=='discourse'),'Discourse reference questions changed')
    items=[{'id':fingerprint([SEED,s['id'],v])[:24],'sample_id':s['id'],'variant':v} for s in samples for v in VARIANTS]
    items.sort(key=lambda i:fingerprint([SEED,'dispatch',i['id']]))
    # The first four requests cover every wording for one seeded sample.
    first=samples[0]['id'];items=([next(i for i in items if i['sample_id']==first and i['variant']==v) for v in VARIANTS]+[i for i in items if i['sample_id']!=first])
    plan={'schema':'behaviorlab.discourse-probe/2','created_at':now(),'author':'Codex','model':MODEL,'endpoint':ENDPOINT,
          'seed':SEED,'spec':spec,'conditions':{v:questions(spec,v) for v in VARIANTS},'samples':samples,'items':items,
          'parent_plan_sha256':parent['sha256'],'software_sha256':software(),'budget':BUDGET,'execution':EXECUTION,
          'selection':parent['selection'],
          'interpretation':parent['interpretation']+' '+spec['portrait_method']}
    for i in items:
        raw=payload(plan,i);require(len(canonical(raw).encode())<48000,'Input exceeds intact request screen')
        require(len(canonical(raw['state']).encode())+max(len(canonical(q).encode()) for q in raw['questions'].values())<30000,'State plus question exceeds intact window screen')
        i['request_sha256']=fingerprint(raw)
    for name,digest in plan['software_sha256'].items():
        source=SPEC if name==SPEC.name else Path(__file__).with_name(name);raw=source.read_bytes()
        require(sha256(raw)==digest,'Software changed during preparation')
        dest=root/'frozen-source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:f.write(raw)
    write_record(root/'plan.json',plan);plan=read_record(root/'plan.json')
    write_record(root/'dispatch-proposal.json',{'created_at':now(),'plan_sha256':plan['sha256'],'endpoint':ENDPOINT,
        'unique_requests':240,'maximum_attempts':252,'questions_per_request':27,'usd_ceiling':2.0,
        'status':'Prepared; awaiting explicit confirmation of this expanded payload, destination and budget.',
        'payload':'48 frozen nonconfidential model-output passages and 12 Codex synthetic controls; target text only, under four wording conditions. No preceding context, source model metadata, human notes or credentials in assessment state.'})
    return plan


def receipts(root,plan):
    rows={};attempts=[];allowed={i['id']:i for i in plan['items']}
    for path in sorted((root/'attempts').glob('*/*.request.json')):
        req=read_record(path);identity=req['item_id'];number=req['attempt']
        require(identity in allowed and path.parent.name==identity,'Unallocated request')
        require(req['plan_sha256']==plan['sha256'] and req['payload']==payload(plan,allowed[identity]),'Frozen request differs')
        history=rows.setdefault(identity,[])
        require(type(number)is int and 1<=number<=3 and number==len(history)+1 and path.name==f'{number:02d}.request.json','Attempt number differs')
        require(not history or history[-1]['status']=='overload','Duplicate success or unauthorized retry')
        row={'id':identity,'attempt':number,'status':'unresolved','answers':{},'cost_usd':None,'request_sha256':req['sha256']}
        rp=path.with_name(f'{number:02d}.response.json')
        if rp.exists():
            res=read_record(rp);require(res['request_sha256']==req['sha256'],'Response parent differs')
            row['response_sha256']=res['sha256']
            if res.get('http_status') in (429,529) and not res.get('error'):row['status']='overload'
            elif res.get('http_status')==200 and not res.get('error'):
                try:row['answers'],row['cost_usd']=validate_response(json.loads(res['raw_text']),plan['conditions'][allowed[identity]['variant']]);row['status']='complete'
                except (ValueError,TypeError,KeyError):row['status']='invalid'
            else:row['status']='error'
        history.append(row);attempts.append(row)
    require(len(attempts)<=252 and sum(max(0,len(h)-1) for h in rows.values())<=12,'Attempt budget exceeded')
    return rows,attempts


def summary(root,plan):
    rows,attempts=receipts(root,plan);complete=sum(h[-1]['status']=='complete' for h in rows.values())
    return {'plan_sha256':plan['sha256'],'planned':len(plan['items']),'complete':complete,'attempts':len(attempts),
            'known_cost_usd':sum(r['cost_usd'] or 0 for r in attempts),
            'unknown_reserved_usd':sum(MAX_INPUT*PRICE/1e6 for r in attempts if r['cost_usd'] is None),
            'stopped':[h[-1]['status'] for h in rows.values() if h[-1]['status'] in ('invalid','unresolved','error')]}


def execute(workspace,max_calls=None,send=None,key=None,sleep=time.sleep):
    root=Path(workspace)/ROOT
    with locked(root/'.runner.lock',blocking=False):
        plan=read_record(root/'plan.json')
        require((root/'authorization.json').is_file(),'Expanded screen awaits explicit dispatch confirmation')
        auth=read_record(root/'authorization.json')
        require(auth.get('explicit_confirmation') is True and auth.get('endpoint')==ENDPOINT and auth.get('unique_requests')==240 and auth.get('max_attempts')==252,'Explicit scope confirmation differs')
        require(auth['plan_sha256']==plan['sha256'] and auth['usd_ceiling']==2,'Authorization differs')
        require(plan['software_sha256']==software(),'Software changed after freeze')
        require(plan['model']==MODEL and plan['endpoint']==ENDPOINT and plan['budget']==BUDGET and plan['execution']==EXECUTION,'Route/budget/execution differs')
        require(len(plan['items'])==240 and len({i['id'] for i in plan['items']})==240,'Allocation differs')
        require(max_calls is None or type(max_calls)is int and max_calls>0,'Invalid max-calls')
        rows,attempts=receipts(root,plan)
        require(not any(r['status'] in ('invalid','unresolved','error') for r in attempts),'Failed or uncertain call; no redispatch')
        if len(rows)==240 and all(h[-1]['status']=='complete' for h in rows.values()):return summary(root,plan)
        if send is None:key=credential(workspace);send=transport
        calls=0
        for item in plan['items']:
            while not rows.get(item['id']) or rows[item['id']][-1]['status']!='complete':
                if max_calls is not None and calls>=max_calls:return summary(root,plan)
                history=rows.get(item['id'],[]);number=len(history)+1
                require(number<=3 and len(attempts)<252 and (not history or sum(max(0,len(h)-1) for h in rows.values())<12),'Retry allowance exhausted')
                reserve=MAX_INPUT*PRICE/1e6
                require(sum(r['cost_usd'] if r['cost_usd'] is not None else reserve for r in attempts)+reserve<=2,'Cost reservation exhausted')
                raw=payload(plan,item);require(fingerprint(raw)==item['request_sha256'],'Payload fingerprint differs')
                if history:sleep(EXECUTION['backoff_seconds'][len(history)-1])
                elif calls:sleep(EXECUTION['minimum_interval_seconds'])
                prefix=root/'attempts'/item['id'];qp=prefix/f'{number:02d}.request.json'
                write_record(qp,{'at':now(),'plan_sha256':plan['sha256'],'item_id':item['id'],'attempt':number,'payload':raw,'reserved_usd':reserve})
                req=read_record(qp);res={'at':now(),'request_sha256':req['sha256'],'http_status':None,'raw_text':'','error':None};start=time.monotonic()
                try:
                    res['http_status'],res['raw_text']=send(raw,key)
                    if key and key in res['raw_text']:res['raw_text']=res['raw_text'].replace(key,'[credential removed]');res['error']='Credential echoed; response excluded'
                except Exception:res['error']='Transport failed after dispatch; cost unknown'
                res['elapsed_seconds']=round(time.monotonic()-start,4);write_record(prefix/f'{number:02d}.response.json',res)
                calls+=1;rows,attempts=receipts(root,plan)
                if calls%6==0 or rows[item['id']][-1]['status']!='complete':print(json.dumps(summary(root,plan)),flush=True)
                if rows[item['id']][-1]['status'] in ('invalid','unresolved','error'):return summary(root,plan)
        result=summary(root,plan)
        if not (root/'summary.json').exists():write_record(root/'summary.json',dict(result,at=now()))
        return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run','status']);p.add_argument('--workspace',default='workspace');p.add_argument('--max-calls',type=int)
    a=p.parse_args()
    if a.action=='prepare':
        plan=prepare(a.workspace);result={'plan_sha256':plan['sha256'],'selection':{k:v for k,v in plan['selection'].items() if k!='reserved_lineages'},'budget':plan['budget']}
    elif a.action=='run':result=execute(a.workspace,a.max_calls)
    else:
        root=Path(a.workspace)/ROOT;result=summary(root,read_record(root/'plan.json'))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
