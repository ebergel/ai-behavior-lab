"""Describe the frozen corpus assessment without claiming calibrated prevalence."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path

from behaviorlab.analysis_corpus import matrix
from behaviorlab.explorer import Catalog
from behaviorlab.jev_atlas import now, write_record


def stats(rows, topics):
    output=[]
    for t in topics:
        observed=[r for r in rows if r[t['field']] is not None]
        values=[r[t['field']] for r in observed]
        output.append({'topic':t['id'],'title':t['title'],'group':t['group'],'observed':len(values),
            'missing':len(rows)-len(values),'mean_score':sum(values)/len(values) if values else None,
            'at_threshold':{str(c):{'passages':sum(v>=c for v in values),
                'conversations':len({r['Conversation ID'] for r in observed if r[t['field']]>=c}),
                'share_observed':sum(v>=c for v in values)/len(values) if values else None} for c in [50,80,90]}})
    return output


def summarize(data):
    rows=[r for r in data['rows'] if r['Inventory category']=='conversation']
    cohorts={'all_visible_conversation_targets':rows,
             'clean_recorded_history':[r for r in rows if r['Observed history']=='Clean recorded path'],
             'flagged_or_unavailable_history':[r for r in rows if r['Observed history']!='Clean recorded path'],
             'technical_or_short':[r for r in data['rows'] if r['Inventory category']=='technical_or_short']}
    coverage=[]
    grouped=defaultdict(list)
    for r in rows:grouped[(r['Model ID'],r['Condition'])].append(r)
    for (model,condition),group in sorted(grouped.items()):
        coverage.append({'model':model,'condition':condition,'passages':len(group),
                         'complete':sum(r['Assessment status']=='Complete' for r in group),
                         'conversations':len({r['Conversation ID'] for r in group}),
                         'topics':stats(group,data['topics'])})
    return {'schema':'behaviorlab.jev-corpus-description/1','at':now(),'author':'Codex','dataset_fingerprint':data['fingerprint'],
        'coverage':data['coverage'],'complete':data['coverage']['complete']==len(data['rows']),
        'cohorts':{k:{'passages':len(v),'conversations':len({r['Conversation ID'] for r in v}),
                      'lineages':len({r['Lineage'] for r in v}),'topics':stats(v,data['topics'])} for k,v in cohorts.items()},
        'speaker_model_and_condition':coverage,
        'method':'Descriptive JEV scores for a fixed historical corpus. Thresholds 50, 80 and 90 were specified in its frozen plan. '
                 'Topic questions overlap; shares do not sum to 100%. Missing assessments are excluded question by question. '
                 'Conversation counts are any-candidate and depend on dialogue length. No independent human calibration or causal model comparison is implied. '
                 'Clean recorded history does not prove missing historical runtime metadata valid.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',default='workspace');p.add_argument('--output',required=True);a=p.parse_args()
    d=matrix(a.workspace,Catalog(a.workspace));report=summarize(d);write_record(Path(a.output),report)
    print({'complete':report['complete'],'coverage':report['coverage']})
