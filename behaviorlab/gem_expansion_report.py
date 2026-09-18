"""Descriptive, reproducible comparison of the two frozen Gem development samples."""
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median

from .common import require
from .gem_expansion import EXPANSION, BANDS, length_band
from .gem_plan import PILOT
from .gem_runner import receipts, summary
from .jev_atlas import read_record, write_record, now


def correlation(x,y):
    if len(x)<3:return None
    mx,my=mean(x),mean(y)
    a=[v-mx for v in x];b=[v-my for v in y]
    denominator=math.sqrt(sum(v*v for v in a)*sum(v*v for v in b))
    return sum(u*v for u,v in zip(a,b))/denominator if denominator else None


def describe(items,axes):
    words=[i['words'] for i in items]
    return {'n':len(items),'lineages':len({i['lineage'] for i in items}),
        'models':dict(Counter(i['model'] for i in items)),
        'length_bands':dict(Counter(length_band(i['words']) for i in items)),
        'words':{'min':min(words),'max':max(words),'mean':mean(words),'median':median(words)},
        'axes':{a:{'mean':mean(i['scores'][a] for i in items),'median':median(i['scores'][a] for i in items),
                  'min':min(i['scores'][a] for i in items),'max':max(i['scores'][a] for i in items),
                  'at_least_80':sum(i['scores'][a]>=80 for i in items),
                  'pearson_r_words':correlation(words,[i['scores'][a] for i in items])} for a in axes}}


def build(workspace):
    workspace=Path(workspace);groups={};plans={};execution={}
    for name,directory in [('original',PILOT),('expansion',EXPANSION)]:
        root=workspace/directory;plan=read_record(root/'plan.json');plans[name]=plan['sha256']
        execution[name]=summary(root,plan)
        require(execution[name]['complete']==len(plan['items']),'Complete this frozen sample before reporting')
        rows,_=receipts(root,plan)
        groups[name]=[dict(i,scores={a:v['normalized_score'] for a,v in rows[i['id']][-1]['answers'].items()}) for i in plan['items']]
    axes=[a['id'] for a in plan['rubric']['axes']];groups['combined']=groups['original']+groups['expansion']
    fresh=groups['expansion']
    return {'schema':'behaviorlab.gem-expansion-analysis/1','created_at':now(),'author':'Codex',
        'plan_sha256':plans,'execution':execution,'rubric_version':plan['rubric']['version'],
        'scope':'Post-hoc descriptive measurement development. Stratified, availability-limited samples; repeated passages share lineages. Correlations are unadjusted, not causal or population estimates. No researcher ratings are inferred.',
        'samples':{k:describe(v,axes) for k,v in groups.items()},
        'fresh_within_model':{m:describe([i for i in fresh if i['model']==m],axes) for m in sorted({i['model'] for i in fresh})},
        'fresh_within_length':{b:describe([i for i in fresh if length_band(i['words'])==b],axes) for b in BANDS if any(length_band(i['words'])==b for i in fresh)},
        'short_candidates':{a:[{'id':i['id'],'run_id':i['run_id'],'message_id':i['message_id'],'words':i['words'],'score':i['scores'][a]} for i in fresh if i['words']<=50 and i['scores'][a]>=80] for a in axes},
        'interpretation':'Short candidate lists are classifier-selected passages for reading, not established gems. No scores were divided by length, residualized or redefined. Model and length coverage remain uneven; 301+ words is mostly OLMo Think.'}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workspace',default='workspace')
    args=parser.parse_args();result=build(args.workspace)
    write_record(Path(args.workspace)/EXPANSION/'descriptive-analysis.json',result)
    print(json.dumps({'samples':result['samples'],'short_candidate_counts':{a:len(v) for a,v in result['short_candidates'].items()}},indent=2))
