"""Read-only summary of the frozen two-tier qualification; never sends model calls."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics

from behaviorlab.common import require
from behaviorlab.jev_atlas import JevAtlas, now, read_record, write_record


def summarize(workspace,coverage):
    store=JevAtlas(workspace);protocol=read_record(Path(coverage)/'qualification.json')
    plans={a['variant']:store.plan(a['batch']) for a in protocol['allocations']}
    results={k:store.results(p) for k,p in plans.items()}
    expanded=results['expanded'];anchor=results['anchors'];questions=[]
    for topic in plans['expanded']['dictionary']:
        key='topic_'+topic['id'];strata={}
        for scope in ('all','root_sample','challenge'):
            rows=[r for r in expanded if r['status']=='complete' and
                  (scope=='all' or (r['sampling_stratum']=='root_sample')==(scope=='root_sample'))]
            values=[r['answers'][key]['noul'] for r in rows]
            strata[scope]={'scored':len(values),'candidates':sum(v>=.8 for v in values),
                'uncertain':sum(.2<v<.8 for v in values),
                'mean':statistics.mean(values) if values else None,'median':statistics.median(values) if values else None}
        questions.append({'id':topic['id'],'title':topic['title'],'group':topic['group'],'strata':strata})
    by_id={r['id']:r for r in expanded};pairs=[]
    for r in anchor:
        other=by_id[r['id']]
        if r['status']!='complete' or other['status']!='complete':continue
        for key,answer in r['answers'].items():
            x=other['answers'][key]['noul'];y=answer['noul']
            pairs.append({'item_id':r['id'],'question':key,'expanded':x,'anchor_only':y,'delta':x-y})
    usage=Counter()
    for variant,plan in plans.items():
        for r in results[variant]:
            if r['status']!='complete':continue
            raw=json.loads(read_record(store.batch_path(plan['id'])/'responses'/(r['id']+'.json'))['raw_text'])
            usage.update(raw['usage'])
    summaries=[store.summary(p,results[k]) for k,p in plans.items()]
    return {'schema':'behaviorlab.jev-two-tier-summary/1','at':now(),'author':'Codex',
        'qualification_sha256':protocol['sha256'],'status':'complete' if all(s['status']=='complete' for s in summaries) else 'incomplete',
        'batches':summaries,'calls_started':sum(s['started'] for s in summaries),
        'cost_usd':sum(s['cost_usd'] for s in summaries),'reported_usage':dict(usage),
        'questions':questions,'anchor_pairs':pairs,
        'anchor_comparison':{'pairs':len(pairs),'exact_equal':sum(p['delta']==0 for p in pairs),
            'mean_absolute_difference':statistics.mean(abs(p['delta']) for p in pairs) if pairs else None,
            'maximum_absolute_difference':max((abs(p['delta']) for p in pairs),default=None),
            'candidate_threshold_crossings':sum((p['expanded']>=.8)!=(p['anchor_only']>=.8) for p in pairs)},
        'limitations':['Root sample and challenge counts remain separate. Neither establishes model preference rates.',
            'One draw per pack cannot isolate a question-pack effect from service variability.',
            'Codex descriptions are development observations, not independent reference labels.',
            'No whole-corpus assessment or calibration claim.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workspace',default='workspace')
    parser.add_argument('--coverage',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    result=summarize(args.workspace,args.coverage)
    require(result['status']=='complete','Qualification is not complete; keep failures or pending calls explicit')
    write_record(args.output,result)
    print(json.dumps({k:result[k] for k in ('status','calls_started','cost_usd','reported_usage','anchor_comparison')},indent=2))
