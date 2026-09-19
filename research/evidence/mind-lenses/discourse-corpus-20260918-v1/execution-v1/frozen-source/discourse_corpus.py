"""Versioned full-corpus execution, with an aggregate budget and durable attempts.

Original qualification runners and the prepared corpus remain immutable. Only
an execution release created here can authorize this separately bounded run.
"""
import argparse
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import signal
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener

from .common import canonical, fingerprint, require, sha256
from .jev_atlas import (JevAtlas, MODEL, ENDPOINT, MAX_INPUT, PRICE, locked,
                        now, read_record, write_record, validate_response)
from .jev_runner import credential, NoRedirect

ROOT = 'mind-lenses/discourse-corpus-20260918-v1'
EXECUTION = ROOT + '/execution-v1'
VARIANTS = ('name_and_definition', 'name_and_portrait')
PILOT = 'mind-lenses/discourse-portraits-20260918-v2'
NANODOLLARS_PER_TOKEN = 42
RESERVE = MAX_INPUT * NANODOLLARS_PER_TOKEN


def software():
    return {name: sha256(Path(__file__).with_name(name).read_bytes())
            for name in ('discourse_corpus.py', 'jev_atlas.py', 'jev_runner.py', 'common.py')}


def payload(plan, target, variant):
    return {'model': plan['model'], 'state': {'target_passage': target['text']},
            'questions': plan['packs'][variant]['questions']}


def checked_plan(workspace, release):
    workspace=Path(workspace).resolve(); path=workspace/release['plan_path']
    require(path.resolve().is_relative_to(workspace), 'Plan must be inside workspace')
    plan=read_record(path)
    require(plan['sha256']==release['plan_sha256'], 'Prepared corpus changed')
    require(plan['model']==MODEL and plan['endpoint']==ENDPOINT, 'Pinned model or endpoint changed')
    for source in plan.get('source_files', []):
        path=workspace/source['path']
        require(path.resolve().is_relative_to(workspace) and sha256(path.read_bytes())==source['sha256'], 'Source evidence changed')
    if plan.get('source_runs'):
        from .explorer import Catalog
        catalog=Catalog(workspace)
        for source in plan['source_runs']:
            run=catalog.runs.get(source['id'],{})
            require(run.get('source',{}).get('sha256')==source['sha256'], 'Source run changed')
        for t in plan['targets']:
            if t['kind']!='transcript':continue
            run=catalog.runs[t['run_id']];m=next((m for m in run['messages'] if m['id']==t['message_id']),{})
            require(m.get('text')==t['text'], 'Source message changed')
    return plan


def reuse_records(workspace, plan):
    workspace=Path(workspace).resolve();results={}
    for target in plan['targets']:
        for variant, request in target['requests'].items():
            ref=request.get('reuse')
            if not ref:continue
            qp=workspace/ref['request'];rp=workspace/ref['response']
            require(qp.resolve().is_relative_to(workspace) and rp.resolve().is_relative_to(workspace), 'Reuse outside workspace')
            req=read_record(qp);res=read_record(rp)
            require(req['sha256']==ref['request_sha256'] and res['sha256']==ref['response_sha256'] and res['request_sha256']==req['sha256'], 'Reused evidence changed')
            require(req['payload']==payload(plan,target,variant), 'Reused request differs')
            require(res['http_status']==200 and not res.get('error'), 'Reuse requires a successful response')
            answers,cost=validate_response(json.loads(res['raw_text']),plan['packs'][variant]['questions'])
            results[(target['id'],variant)]={'answers':answers,'origin':'reuse','receipt':ref,'cost_usd':cost}
    return results


def freeze_corpus(workspace):
    """Full existing topic-corpus frame; no topic/score selection or new control calls."""
    from .explorer import Catalog
    from .finder import model_info
    workspace=Path(workspace).resolve();root=workspace/ROOT
    require(not root.exists(), 'Corpus already frozen; preserve it')
    parent=read_record(workspace/PILOT/'plan.json')
    frame=read_record(workspace/'jev-atlas/corpus-20260917-v1/plan.json')
    catalog=Catalog(workspace);reserved=set(parent['selection']['reserved_lineages'])
    targets=[];sources={};excluded=Counter();old={(s['run_id'],s['message_id']):s for s in parent['samples'] if s['kind']=='transcript'}
    for t in frame['targets']:
        if t['lineage'] in reserved:excluded['reserved_messages']+=1;continue
        if not t['text'].strip():excluded['blank_messages']+=1;continue
        run=catalog.runs[t['run_id']];m=next(m for m in run['messages'] if m['id']==t['message_id'])
        require(run['source']['sha256']==t['source_sha256'] and m['text']==t['text'], 'Source changed')
        path=Path(run['source']['path']).resolve();require(path.is_relative_to(workspace), 'Source outside workspace')
        sources[t['run_id']]=run['source']['sha256']
        prior=old.get((t['run_id'],t['message_id']));model=m.get('model') or 'Unknown'
        target={k:t[k] for k in ('run_id','message_id','source_sha256','lineage','text','turn','speaker','condition','inventory_category')}
        target.update(id=prior['id'] if prior else t['id'],kind='transcript',title=t['run_title'],
                      model=model,model_label=model_info(model)['label'],words=len(t['text'].split()))
        targets.append(target)
    targets.extend(dict(s) for s in parent['samples'] if s['kind']=='synthetic')
    require(len({t['id'] for t in targets})==len(targets),'Duplicate sample ID')
    plan={'schema':'behaviorlab.discourse-corpus/1','created_at':now(),'author':'Codex','model':MODEL,'endpoint':ENDPOINT,
          'parent_plan_sha256':parent['sha256'],'frame_sha256':frame['sha256'],'spec':parent['spec'],
          'packs':{v:{'questions':parent['conditions'][v]} for v in VARIANTS},'targets':targets,
          'source_runs':[{'id':p,'sha256':h} for p,h in sorted(sources.items())],
          'budget':{'usd_ceiling':10.0,'usd_per_million_input':PRICE},
          'selection':{'method':'Every nonblank message in the frozen JEV topic-corpus frame, excluding reserved validation lineages. All topics; technical runs labeled separately. Existing synthetic controls reused separately.',
                       'reserved_lineages':sorted(reserved),'excluded':dict(excluded),
                       'transcripts':sum(t['kind']=='transcript' for t in targets),'synthetic':sum(t['kind']=='synthetic' for t in targets),
                       'models':dict(Counter(t['model'] for t in targets if t['kind']=='transcript')),
                       'lineages':len({t['lineage'] for t in targets if t['kind']=='transcript'})},
          'interpretation':parent['interpretation']+' This expansion covers the eligible frozen corpus; it remains a descriptive classifier. Paired wording differences change the construct as well as wording. Conversation-balanced summaries complement message-weighted means.'}
    prior_items={(i['sample_id'],i['variant']):i for i in parent['items']};reused=0
    for target in targets:
        target['requests']={}
        for v in VARIANTS:
            raw=payload(plan,target,v);size=len(canonical(raw).encode())
            require(size<48000 and len(canonical(raw['state']).encode())+max(len(canonical(q).encode()) for q in raw['questions'].values())<30000, 'Full message exceeds intact input screen; do not truncate')
            entry={'payload_sha256':fingerprint(raw),'bytes':size}
            item=prior_items.get((target['id'],v))
            if item:
                qr=Path(PILOT)/'attempts'/item['id']/'01.request.json';rr=qr.with_name('01.response.json')
                req=read_record(workspace/qr);res=read_record(workspace/rr)
                require(req['payload']==raw and res['request_sha256']==req['sha256'] and res['http_status']==200 and not res.get('error'),'Pilot reuse differs')
                validate_response(json.loads(res['raw_text']),plan['packs'][v]['questions'])
                entry['reuse']={'request':qr.as_posix(),'response':rr.as_posix(),'request_sha256':req['sha256'],'response_sha256':res['sha256']};reused+=1
            target['requests'][v]=entry
    logical=len(targets)*len(VARIANTS)
    plan['counts']={'logical_requests':logical,'reuse_requests':reused,'new_calls':logical-reused}
    write_record(root/'plan.json',plan)
    return read_record(root/'plan.json')


def prepare(workspace, plan_path, destination, approval, ceiling=10.0, max_workers=16, max_rps=10,
            bytes_per_second=180000, retry_allowance=220, backoff=(20, 60)):
    workspace, plan_path, destination = Path(workspace).resolve(), Path(plan_path).resolve(), Path(destination).resolve()
    require(not destination.exists(), 'Execution release already exists')
    require(plan_path.is_relative_to(workspace) and destination.is_relative_to(workspace), 'Release must stay in workspace')
    require(isinstance(approval, str) and approval.strip(), 'Record researcher authorization')
    require(type(ceiling) in (int, float) and 0 < ceiling <= 10, 'Authorized ceiling is $10')
    require(1 <= max_workers <= 16 and 0 < max_rps <= 10 and 0 < bytes_per_second <= 180000, 'Invalid pacing')
    require(type(retry_allowance) is int and 0 <= retry_allowance <= 220, 'Invalid retry allocation')
    require(len(backoff) == 2 and all(type(x) in (int,float) and math.isfinite(x) and x >= 0 for x in backoff), 'Invalid retry backoff')
    plan = read_record(plan_path)
    require(tuple(plan['packs']) == VARIANTS, 'Only the agreed two wording packs are allowed')
    require(plan['endpoint'] == ENDPOINT and plan['model'] == MODEL and plan['budget']['usd_per_million_input'] == PRICE,
            'Unsupported endpoint/model/price')
    seen = set(); original = []; reused = reuse_records(workspace, plan)
    for target in plan['targets']:
        require(target['id'] not in seen, 'Duplicate target'); seen.add(target['id'])
        for variant, expected in target['requests'].items():
            raw = payload(plan, target, variant); size = len(canonical(raw).encode())
            require(fingerprint(raw) == expected['payload_sha256'] and size == expected['bytes'] < 60000,
                    'Prepared full input differs or exceeds qualified screen')
            if 'reuse' not in expected: original.append([target['id'], variant])
    require(len(original) == plan['counts']['new_calls'] and len(reused) == plan['counts']['reuse_requests'], 'Allocation differs')
    # Hash order spreads partial coverage without using topic scores or reading reserved texts.
    order = sorted(original, key=lambda k: fingerprint(['discourse-corpus-order/1', plan['sha256'], k[0]]))
    release = {'schema': 'behaviorlab.jev-corpus-execution/1', 'created_at': now(), 'author': 'Codex',
        'authorized_by': 'researcher', 'approval': approval, 'plan_path': plan_path.relative_to(workspace).as_posix(),
        'plan_sha256': plan['sha256'], 'model': MODEL, 'endpoint': ENDPOINT, 'software_sha256': software(),
        'new_unique_requests': len(order), 'max_attempts': len(order) + retry_allowance,
        'retry_allowance': retry_allowance, 'retryable_http': [429, 529], 'backoff_seconds': list(backoff),
        'max_attempts_per_request': 1 + len(backoff), 'usd_ceiling': float(ceiling),
        'ceiling_nanodollars': round(ceiling * 1_000_000_000), 'nanodollars_per_input_token': NANODOLLARS_PER_TOKEN,
        'reserved_nanodollars_per_attempt': RESERVE, 'max_workers': max_workers, 'max_requests_per_second': max_rps,
        'max_request_bytes_per_second': bytes_per_second, 'timeout_seconds': 60, 'warmup': [20, 500],
        'order': order, 'pacing_basis': 'Existing qualified local JEV coordinator, 2026-09-17',
        'provider_sources': ['https://docs.typesafe.ai/models', 'https://docs.typesafe.ai/api'],
        'policy': 'One aggregate ledger. Reserve full 64000-token cost before each attempt, release only against validated usage. '
                  'Keep unknown-cost reservations, including overloads. Completed/reused requests never repeat. '
                  'Only explicit HTTP 429/529 gets up to two recorded retries with global exponential backoff and Retry-After. '
                  'Stop on unknown transport outcome, other HTTP errors, invalid schema/model/usage, repeated overload, budget or changed evidence. '
                  'Concurrency warms from 1 through 4 to the frozen maximum at 20/500 validated new requests. '
                  'The pilot is unchanged. This is a separately authorized two-wording corpus allocation with exact reuse.'}
    write_record(destination / 'release.json', release)
    for name in software():
        p = destination / 'frozen-source' / name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(Path(__file__).with_name(name).read_bytes())
    return read_record(destination / 'release.json')


def paths(directory, key, attempt):
    root = Path(directory) / 'attempts' / key[0]
    return root / f'{key[1]}-{attempt:03d}.request.json', root / f'{key[1]}-{attempt:03d}.response.json'


def evaluate(response, questions):
    if response.get('http_status') != 200 or response.get('error'):
        return None, None
    try:
        raw = json.loads(response['raw_text']); answers, _ = validate_response(raw, questions)
        return answers, raw['usage']['input_tokens'] * NANODOLLARS_PER_TOKEN
    except (ValueError, KeyError, TypeError):
        return None, None


def replay(workspace, directory, release=None, plan=None):
    directory = Path(directory); release = release or read_record(directory / 'release.json')
    plan = plan or checked_plan(workspace, release)
    targets = {t['id']: t for t in plan['targets']}; allowed = {tuple(k) for k in release['order']}
    results = reuse_records(workspace, plan); attempts = Counter(); ledger = []; fatal = []
    by_sequence = []; seen_sequences = set()
    for p in (directory / 'attempts').glob('*/*.request.json'):
        req = read_record(p); by_sequence.append((req['sequence'], p, req))
    for rp in (directory / 'attempts').glob('*/*.response.json'):
        require(rp.with_name(rp.name.replace('.response.json', '.request.json')).exists(), 'Orphan response')
    for seq, p, req in sorted(by_sequence):
        key = (req['target_id'], req['variant']); n = req['attempt']
        require(seq not in seen_sequences and seq == len(ledger) + 1, 'Duplicate or invalid sequence'); seen_sequences.add(seq)
        require(key in allowed and key not in results and n == attempts[key] + 1,
                'Duplicate success or invalid attempt allocation')
        require(req['release_sha256'] == release['sha256'] and req['reserved_nanodollars'] == RESERVE,
                'Request does not match release')
        require(req['payload'] == payload(plan, targets[key[0]], key[1]), 'Saved full input changed')
        expected, rp = paths(directory, key, n); require(expected == p, 'Attempt path differs')
        if n > 1:
            previous = next(v for v in reversed(ledger) if v['key'] == key)
            require(previous['http_status'] in release['retryable_http'] and n <= release['max_attempts_per_request'], 'Retry outside allocation')
        attempts[key] += 1
        response = read_record(rp) if rp.exists() else None
        if response: require(response['request_sha256'] == req['sha256'], 'Response refers to different request')
        answers, charge = evaluate(response or {}, plan['packs'][key[1]]['questions'])
        entry = {'key': key, 'attempt': n, 'sequence': seq, 'request_sha256': req['sha256'],
                 'response_sha256': response['sha256'] if response else None,
                 'http_status': response.get('http_status') if response else None,
                 'charge_nanodollars': RESERVE if charge is None else charge,
                 'known_nanodollars': charge, 'at': (response or req)['at'],
                 'retry_after': (response or {}).get('retry_after_seconds', 0)}
        ledger.append(entry)
        if answers is not None:
            results[key] = {'answers': answers, 'origin': 'execution', 'receipt': dict(entry), 'cost_usd': charge / 1e9}
        elif not response or response.get('error') or response.get('http_status') not in release['retryable_http']:
            fatal.append({'sequence':seq,'reason':'Unresolved or non-retryable attempt'})
    require(len(ledger) <= release['max_attempts'] and sum(max(0,n-1) for n in attempts.values()) <= release['retry_allowance'], 'Attempt budget exceeded')
    return plan, results, attempts, ledger, fatal


def atomic_status(directory, body):
    p = Path(directory) / '.status.json'; temp = p.with_suffix('.tmp')
    with temp.open('w') as f: f.write(canonical(body)+'\n'); f.flush(); os.fsync(f.fileno())
    os.replace(temp, p)


def status(plan, release, results, ledger, state='paused', reason=None, active=0):
    complete = Counter(k[1] for k in results)
    pairs = Counter(k[0] for k in results)
    known = sum(e['known_nanodollars'] or 0 for e in ledger)
    reserved = sum(e['charge_nanodollars'] for e in ledger if e['known_nanodollars'] is None)
    return {'schema':'behaviorlab.jev-corpus-progress/1','at':now(),'state':state,'reason':reason,
            'plan_sha256':plan['sha256'],'release_sha256':release['sha256'],
            'visible_targets':len(plan['targets']),'completed_targets':sum(n==len(plan['packs']) for n in pairs.values()),
            'complete_by_pack':dict(complete),'completed_assessments':len(results),
            'logical_requests':plan['counts']['logical_requests'],'reused_assessments':plan['counts']['reuse_requests'],
            'new_attempts':len(ledger),'max_attempts':release['max_attempts'],'active':active,
            'known_cost_usd':known/1e9,'unknown_cost_reserved_usd':reserved/1e9,
            'committed_usd':(known+reserved)/1e9,'usd_ceiling':release['usd_ceiling'],
            'failed_attempts':sum(e['known_nanodollars'] is None and e.get('response_sha256') is not None for e in ledger),
            'max_sequence':max((e['sequence'] for e in ledger),default=0)}


def transport(payload_value, key):
    req = Request(ENDPOINT,data=canonical(payload_value).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    try:
        with build_opener(NoRedirect()).open(req,timeout=60) as res:
            return res.status,res.read(4_000_000).decode('utf-8'),dict(res.headers)
    except HTTPError as error:
        return error.code,error.read(1_000_000).decode('utf-8',errors='replace'),dict(error.headers)


def dispatch(directory, request_record, send, key):
    start=time.monotonic(); result={'at':now(),'request_sha256':request_record['sha256'],'http_status':None,'raw_text':'','error':None,'retry_after_seconds':0}
    try:
        result['http_status'],result['raw_text'],headers=send(request_record['payload'],key)
        if key and key in result['raw_text']:
            result.update(raw_text='[credential echoed by provider; omitted]',http_status=None,error='Credential echo; excluded')
        raw_after=next((v for k,v in headers.items() if k.lower()=='retry-after'),None)
        if raw_after:
            try:
                delay=float(raw_after)
                if math.isfinite(delay): result['retry_after_seconds']=max(0,delay)
            except (ValueError,TypeError):
                from email.utils import parsedate_to_datetime
                try: result['retry_after_seconds']=max(0,parsedate_to_datetime(raw_after).timestamp()-time.time())
                except (ValueError,TypeError): pass
    except Exception:
        result['error']='Transport failed after durable dispatch marker; outcome and cost unknown'
    result['at']=now()
    result['elapsed_seconds']=round(time.monotonic()-start,4)
    _, path=paths(directory,(request_record['target_id'],request_record['variant']),request_record['attempt'])
    write_record(path,result)
    return read_record(path)


def run(workspace, directory, max_calls=None, send=None, key=None, pause=time.sleep):
    directory=Path(directory); stop_requested=[False]
    with locked(directory/'.runner.lock',blocking=False):
        release=read_record(directory/'release.json')
        require(release['software_sha256']==software(),'Execution software changed after freeze')
        plan,results,attempts,ledger,fatal=replay(workspace,directory,release)
        targets={t['id']:t for t in plan['targets']}
        if len(results)==plan['counts']['logical_requests']:
            out=status(plan,release,results,ledger,'complete');atomic_status(directory,out);return out
        if fatal:
            out=status(plan,release,results,ledger,'stopped','Unresolved/non-retryable saved attempt; inspect evidence');atomic_status(directory,out);return out
        require(max_calls is None or type(max_calls) is int and max_calls>0,'Invalid call slice')
        if send is None: key=credential(workspace);send=transport
        queue=deque(tuple(k) for k in release['order'] if tuple(k) not in results)
        active={}; started=0; reason=None; cooldown=0; next_dispatch=0; published=0
        new_complete=sum(v['origin']=='execution' for v in results.values())
        for k,n in attempts.items():
            if k in results: continue
            if n>=release['max_attempts_per_request']:reason='Retry limit reached';break
            last=next(e for e in reversed(ledger) if e['key']==k)
            elapsed=max(0,time.time()-datetime.fromisoformat(last['at']).timestamp())
            delay=max(release['backoff_seconds'][n-1],last['retry_after'])
            cooldown=max(cooldown,time.monotonic()+max(0,delay-elapsed))
        def halt(signum,frame):stop_requested[0]=True
        import threading
        original_signals={}
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGINT,signal.SIGTERM):original_signals[sig]=signal.signal(sig,halt)
        try:
            with ThreadPoolExecutor(max_workers=release['max_workers']) as pool:
                while queue or active:
                    if stop_requested[0] or (directory/'PAUSE').exists(): reason=reason or 'Pause requested; inflight calls drained'
                    workers=min(release['max_workers'],1 if new_complete<release['warmup'][0] else 4 if new_complete<release['warmup'][1] else release['max_workers'])
                    if max_calls is not None and started>=max_calls: reason=reason or 'Requested slice complete'
                    clock=time.monotonic()
                    if not reason and queue and len(active)<workers and clock>=max(cooldown,next_dispatch):
                        k=queue.popleft();n=attempts[k]+1
                        charge=sum(e['charge_nanodollars'] for e in ledger)
                        retries=sum(max(0,v-1) for v in attempts.values())
                        if len(ledger)>=release['max_attempts'] or (n>1 and retries>=release['retry_allowance']):reason='Aggregate attempt allocation exhausted'
                        elif n>release['max_attempts_per_request']:reason='Per-request retry limit reached'
                        elif charge+RESERVE>release['ceiling_nanodollars']:reason='Spending ceiling reached'
                        else:
                            raw=payload(plan,targets[k[0]],k[1]);expected=targets[k[0]]['requests'][k[1]]
                            require(fingerprint(raw)==expected['payload_sha256'],'Frozen request changed')
                            marker={'release_sha256':release['sha256'],'target_id':k[0],'variant':k[1],'attempt':n,'sequence':len(ledger)+1,'at':now(),'payload':raw,'reserved_nanodollars':RESERVE}
                            rp,_=paths(directory,k,n);write_record(rp,marker);req=read_record(rp)
                            entry={'key':k,'attempt':n,'sequence':marker['sequence'],'request_sha256':req['sha256'],'response_sha256':None,'http_status':None,'charge_nanodollars':RESERVE,'known_nanodollars':None,'at':marker['at'],'retry_after':0}
                            ledger.append(entry);attempts[k]=n;started+=1
                            active[pool.submit(dispatch,directory,req,send,key)]=entry
                            next_dispatch=clock+max(1/release['max_requests_per_second'],expected['bytes']/release['max_request_bytes_per_second'])
                    done=wait(active,timeout=.02,return_when=FIRST_COMPLETED).done if active else set()
                    for future in done:
                        entry=active.pop(future);res=future.result();k=entry['key']
                        answers,charge=evaluate(res,plan['packs'][k[1]]['questions'])
                        entry.update(response_sha256=res['sha256'],http_status=res['http_status'],at=res['at'],retry_after=res['retry_after_seconds'])
                        if answers is not None:
                            entry.update(known_nanodollars=charge,charge_nanodollars=charge)
                            new_complete += 1
                            results[k]={'answers':answers,'origin':'execution','receipt':dict(entry),'cost_usd':charge/1e9}
                        elif res['http_status'] in release['retryable_http'] and not res['error'] and entry['attempt']<release['max_attempts_per_request']:
                            delay=max(release['backoff_seconds'][entry['attempt']-1],res['retry_after_seconds'])
                            cooldown=max(cooldown,time.monotonic()+delay);queue.appendleft(k)
                        else:reason=reason or 'Non-retryable/invalid response or exhausted request retries'
                    if time.monotonic()-published>=5 or done and (len(results)%50==0):
                        out=status(plan,release,results,ledger,'draining' if reason and active else 'backoff' if time.monotonic()<cooldown else 'running',reason,len(active));atomic_status(directory,out)
                        print(canonical(out),flush=True);published=time.monotonic()
                    if reason and not active:break
                    if not active and queue:pause(min(.2,max(.001,max(cooldown,next_dispatch)-time.monotonic())))
            state='complete' if len(results)==plan['counts']['logical_requests'] else 'paused' if reason in ('Requested slice complete','Pause requested; inflight calls drained') else 'stopped'
            out=status(plan,release,results,ledger,state,reason);atomic_status(directory,out)
            write_record(directory/'summaries'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),out)
            return out
        finally:
            for sig,handler in original_signals.items():signal.signal(sig,handler)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run','status'])
    p.add_argument('--workspace',default='workspace');p.add_argument('--max-calls',type=int);a=p.parse_args()
    workspace=Path(a.workspace);directory=workspace/EXECUTION
    if a.action=='prepare':
        plan=freeze_corpus(workspace)
        out=prepare(workspace,workspace/ROOT/'plan.json',directory,
                    'Researcher: yes, JEV change the classification cost to vey low. go ahead, run the full JEV job. Agreed names + portraits and names + definitions, existing messages, $10 ceiling.',retry_allowance=190)
    elif a.action=='run':out=run(workspace,directory,a.max_calls)
    else:
        release=read_record(directory/'release.json');plan,results,_,ledger,fatal=replay(workspace,directory,release)
        out=status(plan,release,results,ledger,'complete' if len(results)==plan['counts']['logical_requests'] else 'needs inspection' if fatal else 'incomplete')
    print(canonical({k:v for k,v in out.items() if k!='order'}),flush=True)

if __name__=='__main__':main()
