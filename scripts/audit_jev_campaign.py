"""Audit a completed corpus campaign offline; never dispatch an assessment."""
import argparse
from collections import Counter
from pathlib import Path
from statistics import median

from behaviorlab.common import require, fingerprint
from behaviorlab.explorer import Catalog
from behaviorlab.jev_campaign import replay, software, EXECUTION
from behaviorlab.jev_atlas import read_record, write_record, now
from behaviorlab.jev_coverage import build_inventory
from behaviorlab.research_bundle import export_notebook


def audit(workspace):
    workspace=Path(workspace);root=workspace/EXECUTION;release=read_record(root/'release.json')
    require(software()==release['software_sha256'],'Frozen execution software differs')
    plan,results,attempts,ledger,fatal=replay(workspace,root,release)
    require(not fatal and len(results)==plan['counts']['logical_requests'],'Campaign is not fully complete')
    inventory,_=build_inventory(Catalog(workspace));require(fingerprint(inventory)==plan['inventory_sha256'],'Source inventory changed')
    elapsed=[];errors=[]
    for p in sorted((root/'attempts').glob('*/*.response.json')):
        r=read_record(p);elapsed.append(r['elapsed_seconds'])
        if r.get('http_status')!=200:errors.append({'target':p.parent.name,'response':p.name,'http_status':r.get('http_status'),'sha256':r['sha256']})
    timings=sorted(elapsed)
    answers=sum(len(v['answers']) for v in results.values())
    known=sum(e['known_nanodollars'] or 0 for e in ledger)/1e9
    reserved=sum(e['charge_nanodollars'] for e in ledger if e['known_nanodollars'] is None)/1e9
    reused_cost=sum(v['cost_usd'] for v in results.values() if v['origin']=='reuse')
    require(known+reserved<=release['usd_ceiling'],'Aggregate budget exceeded')
    return {'schema':'behaviorlab.jev-corpus-audit/1','at':now(),'author':'Codex','status':'complete',
        'plan_sha256':plan['sha256'],'release_sha256':release['sha256'],'software_unchanged':True,'source_inventory_unchanged':True,
        'visible_targets':len(plan['targets']),'questions':sum(len(p['questions']) for p in plan['packs'].values()),'topic_scores':answers,
        'new_attempts':len(ledger),'new_unique_requests':len(attempts),'reused_assessments':sum(v['origin']=='reuse' for v in results.values()),
        'complete_by_pack':dict(Counter(k[1] for k in results)),'retry_attempts':sum(n-1 for n in attempts.values()),'failures':errors,
        'known_new_cost_usd':known,'unknown_new_cost_reserved_usd':reserved,'committed_new_cost_usd':known+reserved,'new_ceiling_usd':release['usd_ceiling'],
        'reused_prior_cost_usd':reused_cost,'measured_input_tokens':sum((e['known_nanodollars'] or 0)//42 for e in ledger),
        'latency_seconds':{'median':median(timings),'p95_nearest_rank':timings[max(0,((95*len(timings)+99)//100)-1)],'maximum':max(timings)},
        'notebook_sha256':fingerprint(export_notebook((workspace/'explorer'/'notes.sqlite').resolve())),
        'human_semantic_validation':'pending','method':'Exact frozen inputs and complete response schemas were replayed. No new inference. '
            'Reported usage cost excludes unknown usage; its reserved upper bound remains in the aggregate ledger. Reused prior cost is reported separately.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',default='workspace');p.add_argument('--output',required=True);a=p.parse_args()
    report=audit(a.workspace);write_record(Path(a.output),report)
    import json
    print(json.dumps(report,indent=2))
