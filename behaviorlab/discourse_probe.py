"""Finite, separately frozen descriptive thought/discourse classifier screen."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

from .common import canonical, fingerprint, require, sha256
from .jev_atlas import MODEL, ENDPOINT, PRICE, MAX_INPUT, locked, now, read_record, write_record, validate_response
from .jev_runner import credential, transport

ROOT='mind-lenses/discourse-20260918-v1'
SPEC=Path(__file__).resolve().parent.parent/'designs/discourse-lenses-v1.json'
SEED='discourse-name-definition-20260918-v1'
VARIANTS=('name_only','definition_only','name_and_definition')
BUDGET={'unique_requests':180,'max_attempts':192,'retry_allowance':12,'max_attempts_per_item':3,'usd_ceiling':2.0,
        'usd_per_million_input':PRICE,'reserved_input_tokens_per_attempt':MAX_INPUT}
EXECUTION={'retryable_http':[429,529],'backoff_seconds':[20,40],'minimum_interval_seconds':.25,'timeout_seconds':60}


def software():
    return {**{n:sha256(Path(__file__).with_name(n).read_bytes()) for n in
            ('discourse_probe.py','common.py','jev_atlas.py','jev_runner.py')},SPEC.name:sha256(SPEC.read_bytes())}


def questions(spec,variant):
    require(variant in VARIANTS,'Unknown wording condition')
    result={}
    for f in spec['features']:
        task='Does the target passage exhibit the pattern described below?'
        if variant=='name_only':
            body=f"Does the target passage exhibit a way of thinking, literary form, or discourse practice associated with this label?\nLabel: {f['name']}"
        else:
            body=task+'\nPattern: '+f['definition']
            if variant=='name_and_definition':body+='\nLabel: '+f['name']
        result[f['id']]={'type':'noul','instructions':spec['scope']+'\n'+body}
    return result


def select(items,reserved,count=48):
    require(len({i['id'] for i in items})==len(items),'Duplicate source target')
    groups=defaultdict(list)
    for i in items:
        if i['lineage'] not in reserved and i['text'].strip():groups[i['model']].append(i)
    def order(i):return fingerprint([SEED,i['id']])
    # Rotate length bands within each model without consulting any score.
    bands=((1,50),(51,100),(101,150),(151,None))
    def band(i):return next(n for n,(lo,hi) in enumerate(bands) if lo<=len(i['text'].split()) and (hi is None or len(i['text'].split())<=hi))
    for g in groups.values():g.sort(key=order)
    counts=defaultdict(Counter)
    models=sorted(groups,key=lambda m:(len({i['lineage'] for i in groups[m]}),fingerprint([SEED,m])))
    chosen=[];used=set()
    while len(chosen)<count:
        progress=False
        for m in models:
            available=[i for i in groups[m] if i['lineage'] not in used]
            i=min(available,key=lambda i:(counts[m][band(i)],order(i)),default=None)
            if i:
                chosen.append(dict(i));used.add(i['lineage']);counts[m][band(i)]+=1;progress=True
                if len(chosen)==count:break
        if not progress:break
    require(len(chosen)==count,'Not enough distinct eligible lineages')
    return sorted(chosen,key=lambda i:fingerprint([SEED,'reading',i['id']]))


def payload(plan,item):
    sample=next(s for s in plan['samples'] if s['id']==item['sample_id'])
    return {'model':plan['model'],'state':{'target_passage':sample['text']},'questions':plan['conditions'][item['variant']]}


def prepare(workspace):
    from .explorer import Catalog
    workspace=Path(workspace);root=workspace/ROOT;require(not root.exists(),'Probe already frozen; preserve it')
    spec=json.loads(SPEC.read_text());plans=[read_record(workspace/p/'plan.json') for p in
          ('gem-finder/pilot-20260918-v1','gem-finder/expansion-20260918-v1')]
    reserved=set(plans[0]['selection']['reserved_lineages']);catalog=Catalog(workspace)
    selected=select([i for p in plans for i in p['items']],reserved)
    samples=[]
    for i in selected:
        run=catalog.runs[i['run_id']];m=next(m for m in run['messages'] if m['id']==i['message_id'])
        require(run['source']['sha256']==i['source_sha256'] and m['text']==i['text'],'Source changed')
        samples.append({k:i[k] for k in ('id','run_id','message_id','source_sha256','lineage','model','model_label','title','text','words')})
        samples[-1]['kind']='transcript'
    samples.extend(dict(c,kind='synthetic',author='Codex',words=len(c['text'].split())) for c in spec['controls'])
    require(len(samples)==60 and len(spec['features'])==27,'Screen requires 48 transcripts, 12 controls, and 27 features')
    items=[{'id':fingerprint([SEED,s['id'],v])[:24],'sample_id':s['id'],'variant':v} for s in samples for v in VARIANTS]
    items.sort(key=lambda i:fingerprint([SEED,'dispatch',i['id']]))
    plan={'schema':'behaviorlab.discourse-probe/1','created_at':now(),'author':'Codex','model':MODEL,'endpoint':ENDPOINT,
          'seed':SEED,'spec':spec,'conditions':{v:questions(spec,v) for v in VARIANTS},'samples':samples,'items':items,
          'parent_plan_sha256':[p['sha256'] for p in plans],'software_sha256':software(),'budget':BUDGET,'execution':EXECUTION,
          'selection':{'transcripts':48,'synthetic':12,'models':dict(Counter(i['model'] for i in selected)),
                       'lineages':len({i['lineage'] for i in selected}),'reserved_lineages':sorted(reserved),
                       'method':'Seeded model round robin, sparse models first, rotating least-used available word bands within each model (1–50, 51–100, 101–150, 151+), one target per lineage, nonempty targets, no score or topic-based selection.'},
          'interpretation':'Paired exploratory prompt comparison, not author identification, depth, accuracy, calibrated degree of likeness, or population prevalence. Definition-only vs named-definition appends only a label line to identical question wording; name-only vs defined also changes the construct. One assessment per condition cannot separate stochastic variation from wording sensitivity. Selection is from the 1,000 Gem development targets, not a representative corpus sample. Synthetic expectations are Codex design intentions, not human validation. No reference-author quotations are used. Only the target text is supplied; no preceding context, participant model, source or condition metadata.'}
    for i in items:
        raw=payload(plan,i);require(len(canonical(raw).encode())<32000,'Input exceeds intact request screen')
        i['request_sha256']=fingerprint(raw)
    for name,digest in plan['software_sha256'].items():
        source=SPEC if name==SPEC.name else Path(__file__).with_name(name);raw=source.read_bytes()
        require(sha256(raw)==digest,'Software changed during preparation')
        dest=root/'frozen-source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:f.write(raw)
    write_record(root/'plan.json',plan);plan=read_record(root/'plan.json')
    write_record(root/'dispatch-proposal.json',{'created_at':now(),'plan_sha256':plan['sha256'],'endpoint':ENDPOINT,
        'unique_requests':180,'maximum_attempts':192,'questions_per_request':27,'usd_ceiling':2.0,
        'status':'Prepared; awaiting explicit confirmation of this expanded payload, destination and budget.',
        'payload':'48 frozen nonconfidential model-output passages and 12 Codex synthetic controls; target text only, under three wording conditions. No preceding context, source model metadata, human notes or credentials in assessment state.'})
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
    require(len(attempts)<=192 and sum(max(0,len(h)-1) for h in rows.values())<=12,'Attempt budget exceeded')
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
        require(auth.get('explicit_confirmation') is True and auth.get('endpoint')==ENDPOINT and auth.get('unique_requests')==180 and auth.get('max_attempts')==192,'Explicit scope confirmation differs')
        require(auth['plan_sha256']==plan['sha256'] and auth['usd_ceiling']==2,'Authorization differs')
        require(plan['software_sha256']==software(),'Software changed after freeze')
        require(plan['model']==MODEL and plan['endpoint']==ENDPOINT and plan['budget']==BUDGET and plan['execution']==EXECUTION,'Route/budget/execution differs')
        require(len(plan['items'])==180 and len({i['id'] for i in plan['items']})==180,'Allocation differs')
        require(max_calls is None or type(max_calls)is int and max_calls>0,'Invalid max-calls')
        rows,attempts=receipts(root,plan)
        require(not any(r['status'] in ('invalid','unresolved','error') for r in attempts),'Failed or uncertain call; no redispatch')
        if len(rows)==180 and all(h[-1]['status']=='complete' for h in rows.values()):return summary(root,plan)
        if send is None:key=credential(workspace);send=transport
        calls=0
        for item in plan['items']:
            while not rows.get(item['id']) or rows[item['id']][-1]['status']!='complete':
                if max_calls is not None and calls>=max_calls:return summary(root,plan)
                history=rows.get(item['id'],[]);number=len(history)+1
                require(number<=3 and len(attempts)<192 and (not history or sum(max(0,len(h)-1) for h in rows.values())<12),'Retry allowance exhausted')
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
