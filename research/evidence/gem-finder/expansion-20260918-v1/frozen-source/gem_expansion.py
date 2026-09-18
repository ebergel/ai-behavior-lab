"""A separately frozen Gem expansion. Original pilot software remains unchanged."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import json
from pathlib import Path
import time

from .common import canonical, fingerprint, require, sha256
from .gem_plan import PILOT, payload, profile_distance, software as pilot_software
from .gem_runner import receipts, summary, validate
from .jev_atlas import MODEL, ENDPOINT, PRICE, MAX_INPUT, locked, now, read_record, write_record
from .jev_runner import credential, transport

EXPANSION = 'gem-finder/expansion-20260918-v1'
SEED = 'gem-model-length-expansion-20260918-v1'
BANDS = ['1–25', '26–75', '76–150', '151–300', '301+']
EXECUTION = {'retryable_http': [429, 529], 'backoff_seconds': [20, 40],
             'max_workers': 4, 'minimum_interval_seconds': .25, 'timeout_seconds': 60}


def software():
    return {**pilot_software(), 'gem_expansion.py': sha256(Path(__file__).read_bytes())}


def length_band(words):
    return BANDS[0 if words <= 25 else 1 if words <= 75 else 2 if words <= 150 else 3 if words <= 300 else 4]


def select(candidates, original, count=900, cap=3):
    """Model × length round robin, filling least-used lineages first; no score ranking."""
    require(type(count) is int and 0 < count <= 900, 'Expansion size must be 1–900')
    prior_ids = {i['id'] for i in original}
    require(len({i['id'] for i in candidates}) == len(candidates), 'Duplicate candidate IDs')
    groups = defaultdict(list)
    for item in candidates:
        if item['id'] not in prior_ids:
            groups[(item['model'], length_band(item['words']))].append(item)
    for group in groups.values():
        group.sort(key=lambda i: fingerprint([SEED, i['id']]))
    models = sorted({m for m, _ in groups}, key=lambda m: fingerprint([SEED, m]))
    bands = sorted(BANDS, key=lambda b: fingerprint([SEED, b]))
    used = Counter(i['lineage'] for i in original)
    chosen = []; availability = {m: {b: len(groups[(m,b)]) for b in BANDS} for m in models}
    # Reach new lineages before allowing a second or third target from one lineage.
    for level in range(1, cap + 1):
        while len(chosen) < count:
            progress = False
            for band in bands:
                for model in models:
                    group = groups[(model, band)]
                    index = next((j for j, i in enumerate(group) if used[i['lineage']] < level), None)
                    if index is not None:
                        item = group.pop(index); chosen.append(dict(item, length_band=band, sample_role='expansion'))
                        used[item['lineage']] += 1; progress = True
                        if len(chosen) == count: break
                if len(chosen) == count: break
            if not progress: break
    require(len(chosen) == count, 'Not enough eligible passages within lineage cap; do not silently relax it')
    chosen.sort(key=lambda i: fingerprint([SEED, 'reading-order', i['id']]))
    return chosen, {'candidate_count': sum(sum(v.values()) for v in availability.values()),
        'available_model_length': availability,
        'selected_model_length': {m: dict(Counter(i['length_band'] for i in chosen if i['model'] == m)) for m in models},
        'selected_models': dict(Counter(i['model'] for i in chosen)),
        'selected_length_bands': dict(Counter(i['length_band'] for i in chosen)),
        'selected_lineages': len({i['lineage'] for i in chosen}),
        'combined_lineages': len(used), 'combined_max_per_lineage': max(used.values()),
        'lineage_cap_including_original': cap}


def prepare(workspace, count=900):
    from .explorer import Catalog
    from .finder import model_info, experiment
    workspace = Path(workspace); root = workspace / EXPANSION
    require(not root.exists(), 'Expansion already exists; preserve the freeze')
    base = read_record(workspace / PILOT / 'plan.json')
    require(base['software_sha256'] == pilot_software(), 'Original scoring software changed')
    require(summary(workspace/PILOT, base)['complete'] == len(base['items']), 'Finish original pilot first')
    corpus = read_record(workspace/'jev-atlas/corpus-20260917-v1/plan.json')
    require(corpus['sha256'] == base['corpus_plan_sha256'], 'Corpus freeze changed')
    reserved = set(base['selection']['reserved_lineages'])
    ref = {i['id']: i for i in base['reference']}
    require(not reserved & {r['lineage'] for r in ref.values()}, 'Reserved lineage in reference')
    catalog = Catalog(workspace); candidates = []; excluded = Counter()
    old_ids = {i['id'] for i in base['items']}
    for target in corpus['targets']:
        if target['lineage'] in reserved or target['id'] not in ref or target['id'] in old_ids: continue
        if not target.get('context'): excluded['no_preceding_context'] += 1; continue
        run = catalog.runs.get(target['run_id'])
        message = next((m for m in (run or {}).get('messages',[]) if m['id'] == target['message_id']), None)
        if not message or message.get('text') != target['text'] or run['source']['sha256'] != target['source_sha256']:
            excluded['source_changed'] += 1; continue
        require(base['discovery_runs'][run['id']] == target['source_sha256'], 'Source outside original discovery freeze')
        item = {k: target[k] for k in ('id','run_id','message_id','lineage','text','context','speaker','turn','source_sha256','condition')}
        raw = payload(base, item)
        if len(canonical(raw).encode()) >= 30000: excluded['intact_request_too_large'] += 1; continue
        model = message.get('model') or 'Unknown'; exp = experiment(run)
        scores = {t['id']: v for t, v in zip(base['broad_topics'], ref[item['id']]['vector'])}
        item.update(title=run['title'], model=model, model_label=model_info(model)['label'], quality='Clean recorded path',
                    identity=exp.get('identity','Unknown'), composition=exp.get('composition','Unknown'), topic_scores=scores,
                    broad_topic=max(base['broad_topics'],key=lambda t:scores[t['id']])['id'], words=len(item['text'].split()))
        candidates.append(item)
    items, audit = select(candidates, base['items'], count)
    audit.update(excluded_positions=dict(excluded), reserved_lineages=sorted(reserved))
    for item in items:
        item['profile_distance'] = profile_distance(item, base['reference'], base['broad_topics'])
        raw = payload(base, item); item['request_sha256'] = fingerprint(raw); item['request_bytes'] = len(canonical(raw).encode())
    plan = {'schema':'behaviorlab.gem-expansion/1','created_at':now(),'author':'Codex','seed':SEED,
        'parent_plan_sha256':base['sha256'],'model':MODEL,'endpoint':ENDPOINT,'rubric':base['rubric'],
        'questions':base['questions'],'items':items,'broad_topics':base['broad_topics'],
        'reference_plan':PILOT+'/plan.json','reference_sha256':fingerprint(base['reference']),
        'corpus_plan_sha256':corpus['sha256'],'selection':audit,'discovery_runs':base['discovery_runs'],
        'software_sha256':software(),'execution':EXECUTION,
        'budget':{'unique_requests':len(items),'max_attempts':len(items)+27,'retry_allowance':27,'max_attempts_per_item':3,
                  'usd_ceiling':2.0,'usd_per_million_input':PRICE,'reserved_input_tokens_per_attempt':MAX_INPUT},
        'policy':'Separate model × length development expansion. Fresh target IDs only; original 100 retained without rescoring. '
                 'At most three targets per lineage including the original sample. Model/length coverage is availability-limited; '
                 'targets share conversations and are not independent replicates. No topic, gem score or human judgment used in selection. '
                 'All 60 reserved lineages excluded. Original rubric, payload and topic-profile reference are unchanged. '
                 'Only explicit 429/529 overloads may retry within allocation. Other failures stop new dispatch; active requests drain. '
                 'Every request is durable before dispatch, with maximum-cost reservation; unknown costs retain their reserve.'}
    for name, digest in plan['software_sha256'].items():
        raw = Path(__file__).with_name(name).read_bytes(); require(sha256(raw)==digest,'Software changed during freeze')
        path = root/'frozen-source'/name; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f: f.write(raw)
    write_record(root/'plan.json', plan)
    plan = read_record(root/'plan.json')
    write_record(root/'authorization.json', {'at':now(),'plan_sha256':plan['sha256'],'usd_ceiling':2.0,
        'basis':'Researcher requested expansion of the Gem pilot on 18 September 2026. Assistant communicated 900 new assessments, unchanged rubric and a separate $2 ceiling before dispatch. This is a new finite allocation, not reuse of an older ceiling.'})
    return plan


def _perform(root, req, raw, key, send):
    res = {'at':now(),'request_sha256':req['sha256'],'http_status':None,'raw_text':'','error':None}
    start = time.monotonic()
    try:
        res['http_status'], res['raw_text'] = send(raw, key)
        if key and key in res['raw_text']:
            res['raw_text'] = res['raw_text'].replace(key,'[credential removed]'); res['error']='Credential echoed; excluded'
    except Exception: res['error']='Transport failed after dispatch; usage unknown'
    res['elapsed_seconds'] = round(time.monotonic()-start,4)
    write_record(root/'attempts'/req['item_id']/f"{req['attempt']:02d}.response.json",res)
    return res


def execute(workspace, max_calls=None, send=None, key=None):
    root=Path(workspace)/EXPANSION
    with locked(root/'.runner.lock',blocking=False):
        plan=read_record(root/'plan.json'); approval=read_record(root/'authorization.json')
        require(approval['plan_sha256']==plan['sha256'] and approval['usd_ceiling']==plan['budget']['usd_ceiling'],'Authorization differs')
        require(plan['software_sha256']==software(),'Expansion software changed since freeze')
        base=read_record(Path(workspace)/PILOT/'plan.json')
        require(base['sha256']==plan['parent_plan_sha256'] and base['questions']==plan['questions'] and base['rubric']==plan['rubric'],'Original rubric/parent differs')
        require(plan['endpoint']==ENDPOINT and plan['model']==MODEL and plan['execution']==EXECUTION,'Route or execution differs')
        budget=plan['budget']; n=len(plan['items'])
        require(0<n<=900 and budget=={'unique_requests':n,'max_attempts':n+27,'retry_allowance':27,'max_attempts_per_item':3,
                 'usd_ceiling':2.0,'usd_per_million_input':PRICE,'reserved_input_tokens_per_attempt':MAX_INPUT},'Budget differs')
        require(max_calls is None or type(max_calls) is int and max_calls>0,'Invalid max-calls')
        rows, attempts=receipts(root,plan)
        require(not any(r['status'] in ('unresolved','invalid','error') for r in attempts),'Expansion stopped on failed or uncertain request; no redispatch')
        todo=[i for i in plan['items'] if not rows.get(i['id']) or rows[i['id']][-1]['status']!='complete']
        if not todo:return summary(root,plan)
        if send is None:key=credential(workspace);send=transport
        reserve=MAX_INPUT*PRICE/1_000_000; calls=0; active={}; ready={}; stop=None; next_dispatch=0
        for i in todo:
            h=rows.get(i['id'],[])
            if h:require(len(h)<3,'Per-item retries exhausted');ready[i['id']]=time.monotonic()+EXECUTION['backoff_seconds'][len(h)-1]
        with ThreadPoolExecutor(max_workers=EXECUTION['max_workers']) as pool:
            while todo or active:
                while todo and not stop and len(active)<EXECUTION['max_workers'] and (max_calls is None or calls<max_calls):
                    now_mono=time.monotonic()
                    if now_mono<next_dispatch:break
                    index=next((j for j,i in enumerate(todo) if ready.get(i['id'],0)<=now_mono),None)
                    if index is None:break
                    item=todo.pop(index); history=rows.setdefault(item['id'],[])
                    if len(history)>=3 or len(attempts)>=budget['max_attempts'] or (history and sum(max(0,len(h)-1) for h in rows.values())>=27):
                        stop='Retry/attempt allocation exhausted';break
                    committed=sum(r['cost_usd'] if r['cost_usd'] is not None else reserve for r in attempts)
                    if committed+reserve>2:stop='Budget reservation exhausted';break
                    raw=payload(plan,item);require(fingerprint(raw)==item['request_sha256'],'Frozen request differs')
                    attempt=len(history)+1; path=root/'attempts'/item['id']/f'{attempt:02d}.request.json'
                    write_record(path,{'at':now(),'plan_sha256':plan['sha256'],'item_id':item['id'],'attempt':attempt,'payload':raw,'reserved_usd':reserve})
                    req=read_record(path); row={'item_id':item['id'],'attempt':attempt,'status':'unresolved','cost_usd':None,'reserved_usd':reserve,'answers':{}}
                    history.append(row);attempts.append(row);calls+=1
                    active[pool.submit(_perform,root,req,raw,key,send)]=(item,row)
                    next_dispatch=time.monotonic()+EXECUTION['minimum_interval_seconds']
                if active:
                    done,_=wait(active,timeout=.1,return_when=FIRST_COMPLETED)
                    for future in done:
                        item,row=active.pop(future);res=future.result()
                        if res['http_status'] in (429,529) and not res['error']:
                            row['status']='overload';todo.append(item)
                            if row['attempt']<3:ready[item['id']]=time.monotonic()+EXECUTION['backoff_seconds'][row['attempt']-1]
                            else:stop='Per-item retries exhausted'
                        elif res['http_status']==200 and not res['error']:
                            try:row['answers'],row['cost_usd']=validate(json.loads(res['raw_text']),plan['questions']);row['status']='complete'
                            except (ValueError,TypeError,KeyError):row['status']='invalid';stop='Invalid response'
                        else:row['status']='error';stop='Transport/HTTP failure'
                        complete=sum(h[-1]['status']=='complete' for h in rows.values())
                        if complete%25==0 or row['status']!='complete':
                            print(json.dumps({'complete':complete,'planned':n,'attempts':len(attempts),'known_cost_usd':sum(r['cost_usd'] or 0 for r in attempts),'latest':row['status']}),flush=True)
                elif stop or (max_calls is not None and calls>=max_calls):break
                else:time.sleep(.1)
        result=summary(root,plan)
        if stop:result['stop_reason']=stop
        if result['complete']==n and not (root/'summary.json').exists():write_record(root/'summary.json',dict(result,at=now()))
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','run','status'])
    parser.add_argument('--workspace',default='workspace');parser.add_argument('--count',type=int,default=900);parser.add_argument('--max-calls',type=int)
    args=parser.parse_args()
    if args.action=='prepare':
        plan=prepare(args.workspace,args.count);result={k:plan[k] for k in ('sha256','selection','budget')}
    elif args.action=='run':result=execute(args.workspace,args.max_calls)
    else:
        root=Path(args.workspace)/EXPANSION;result=summary(root,read_record(root/'plan.json'))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
