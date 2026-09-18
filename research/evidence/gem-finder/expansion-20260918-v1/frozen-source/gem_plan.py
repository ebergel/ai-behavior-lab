"""Freeze a small, source-linked Gem Finder development pilot; no network calls."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

from .common import canonical, fingerprint, require, sha256
from .jev_atlas import ENDPOINT, MODEL, PRICE, MAX_INPUT, now, read_record, write_record

PILOT = 'gem-finder/pilot-20260918-v1'
SEED = 'gem-discovery-20260918-v1'


def software():
    return {n:sha256(Path(__file__).with_name(n).read_bytes()) for n in
            ('gem_plan.py','gem_runner.py','gem_rubric.json','common.py','jev_atlas.py','jev_runner.py')}


def questions(rubric):
    return {a['id']:{'type':'score','instructions':rubric['scope']+' '+a['question'],
                     'criteria':a['criteria']} for a in rubric['axes']}


def payload(plan, item):
    # Neither model labels, topic scores, researcher ratings nor later replies enter the request.
    return {'model':plan['model'], 'questions':plan['questions'],
            'state':{'preceding_messages':item['context'],
                     'target':{'speaker':item['speaker'],'text':item['text']}}}


def select_items(catalog, dataset, corpus, count=100):
    """One target per lineage, round-robin over target models, without score selection."""
    require(type(count) is int and 1 <= count <= 100, 'Pilot size must be 1–100')
    reserved = {t['lineage'] for t in corpus['targets'] if t['split']=='reference_reserved'}
    targets = {t['id']:t for t in corpus['targets']}
    groups = defaultdict(list); excluded=Counter(); reference=[]
    broad=[t for t in dataset['topics'] if t['group']=='broad']
    require(bool(broad), 'No broad topic profiles')
    for row in dataset['rows']:
        target=targets.get(row['__id']);p=dataset['passages'].get(row['__id'],{})
        if not target or target['lineage'] in reserved or row['Inventory category']!='conversation':
            excluded['reserved_or_nonconversation']+=1;continue
        run=catalog.runs.get(target['run_id'])
        m=next((m for m in (run or {}).get('messages',[]) if m['id']==target['message_id']),None)
        current=bool(m and p.get('source_current') and m.get('text')==target['text'] and run['source']['sha256']==target['source_sha256'])
        if not current or row['Assessment status']!='Complete':excluded['missing_or_stale']+=1;continue
        if row['Observed history']!='Clean recorded path' or m.get('status') not in ('valid','recorded'):
            excluded['flagged_history_or_target']+=1;continue
        vector=[row[t['field']] for t in broad]
        if not all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=100 for v in vector):
            excluded['missing_profile']+=1;continue
        reference.append({'id':target['id'],'lineage':target['lineage'],'run_id':target['run_id'],
                          'message_id':target['message_id'],'vector':vector})
        if not target.get('context'):excluded['no_preceding_context_for_surprise']+=1;continue
        item={k:target[k] for k in ('id','run_id','message_id','lineage','text','context','speaker','turn','source_sha256','condition')}
        item.update(title=run['title'],model=row['Model ID'],model_label=row['Model'],quality=row['Observed history'],
                    identity=row['Identity'],composition=row['Composition'],topic_scores={t['id']:row[t['field']] for t in broad},
                    broad_topic=max(broad,key=lambda t:row[t['field']])['id'],words=len(target['text'].split()),sample_role='pilot')
        groups[item['model']].append(item)
    for model in groups:groups[model].sort(key=lambda i:fingerprint([SEED,i['id']]))
    models=sorted(groups,key=lambda m:fingerprint([SEED,m]));used=set();selected=[]
    while len(selected)<count:
        progress=False
        for model in models:
            while groups[model] and groups[model][0]['lineage'] in used:groups[model].pop(0)
            if groups[model]:
                item=groups[model].pop(0);used.add(item['lineage']);selected.append(item);progress=True
                if len(selected)==count:break
        if not progress:break
    require(len(selected)==count, 'Not enough eligible distinct lineages for this pilot size')
    # Remove model-based ordering from the reading queue; keep a reproducible random order.
    selected.sort(key=lambda i:fingerprint([SEED,'reading-order',i['id']]))
    return selected,reference,broad,{'excluded_positions':dict(excluded),'reserved_lineages':sorted(reserved),
         'reference_passages':len(reference),'reference_lineages':len({p['lineage'] for p in reference}),
         'selected_models':dict(Counter(i['model'] for i in selected))}


def profile_distance(item, reference, broad, k=5):
    """Average nearest-profile RMS distance, one minimum per other lineage."""
    vector=[item['topic_scores'][t['id']] for t in broad];near={}
    for other in reference:
        if other['lineage']==item['lineage']:continue
        distance=math.sqrt(sum((a-b)**2 for a,b in zip(vector,other['vector']))/len(vector))
        prior=near.get(other['lineage'])
        if prior is None or (distance,other['id'])<(prior[0],prior[1]['id']):near[other['lineage']]=(distance,other)
    chosen=sorted(near.values(),key=lambda v:(v[0],v[1]['id']))[:k]
    return {'value':sum(d for d,_ in chosen)/len(chosen) if len(chosen)==k else None,
            'neighbors':[dict(id=p['id'],run_id=p['run_id'],message_id=p['message_id'],distance=d) for d,p in chosen],
            'k':k,'reference_lineages':len(near)}


def prepare(workspace, count=100):
    from .explorer import Catalog
    from .analysis_workspace import AnalysisWorkspace
    workspace=Path(workspace);root=workspace/PILOT
    require(not root.exists(), 'Pilot already exists; preserve it')
    catalog=Catalog(workspace);analysis=AnalysisWorkspace(workspace,catalog)
    corpus=read_record(workspace/'jev-atlas/corpus-20260917-v1/plan.json')
    dataset=analysis.corpus_dataset()
    rubric=json.loads(Path(__file__).with_name('gem_rubric.json').read_text())
    items,reference,broad,audit=select_items(catalog,dataset,corpus,count)
    for item in items:item['profile_distance']=profile_distance(item,reference,broad)
    plan={'schema':'behaviorlab.gem-pilot/1','created_at':now(),'author':'Codex','seed':SEED,
          'model':MODEL,'endpoint':ENDPOINT,'rubric':rubric,'questions':questions(rubric),'items':items,
          'broad_topics':broad,'reference':reference,'selection':audit,'corpus_plan_sha256':corpus['sha256'],
          'discovery_runs':{rid:catalog.runs[rid]['source']['sha256'] for rid in sorted({r['run_id'] for r in reference})},
          'dataset_fingerprint':dataset['fingerprint'],'software_sha256':software(),
          'budget':{'unique_requests':count,'max_attempts':count+10,'retry_allowance':10,'max_attempts_per_item':3,
                    'usd_ceiling':2.0,'usd_per_million_input':PRICE,'reserved_input_tokens_per_attempt':MAX_INPUT},
          'execution':{'retryable_http':[429,529],'backoff_seconds':[20,40],'minimum_interval_seconds':1,'timeout_seconds':60},
          'policy':'Development sample, not a prevalence estimate. One target per lineage; balanced target-model round robin with finite availability. '
                   'No score or topic used in selection. Reserved validation lineages excluded from target, context and reference. '
                   'Corpus distinctiveness means distance between existing broad-topic score profiles, not linguistic novelty or quality. '
                   'Score outputs are provisional ratings, not gem probabilities. No new dialogue generation. '
                   'Only explicit HTTP 429/529 may retry within both limits; all other failures and uncertain requests stop. '
                   'Every attempt reserves its maximum cost until validated usage; unknown costs retain their reservation.'}
    for item in items:
        raw=payload(plan,item);size=len(canonical(raw).encode())
        require(size<30000,'Intact request exceeds 30,000-byte screen; do not truncate or replace it silently')
        item['request_sha256']=fingerprint(raw);item['request_bytes']=size
    for name,digest in plan['software_sha256'].items():
        raw=Path(__file__).with_name(name).read_bytes();require(sha256(raw)==digest,'Software changed during preparation')
        target=root/'frozen-source'/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(raw)
    write_record(root/'plan.json',plan)
    return read_record(root/'plan.json')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',default='workspace');p.add_argument('--count',type=int,default=100)
    args=p.parse_args();plan=prepare(args.workspace,args.count)
    print(json.dumps({'plan_sha256':plan['sha256'],'items':len(plan['items']),'selection':plan['selection'],
                      'budget':plan['budget'],'request_bytes':sum(i['request_bytes'] for i in plan['items'])},indent=2))


if __name__=='__main__':main()
