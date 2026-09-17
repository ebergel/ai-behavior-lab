#!/usr/bin/env python3
"""Planning sensitivity from one first-six mean per discovery conversation.

Read saved scores only. No text, reserved lineages, model calls or sample-size freeze.
"""
import argparse
from collections import defaultdict, Counter
import json
import math
from pathlib import Path
import statistics


def calculate(matrix):
    groups=defaultdict(list)
    for row in matrix['rows']:
        if row.get('Inventory category')=='conversation':groups[row['Conversation ID']].append(row)
    fields=['Score · Mind & cognition','Score · Philosophy & knowledge']
    samples=defaultdict(lambda:defaultdict(list));excluded=Counter();seen=set()
    for rows in groups.values():
        if any(r.get('Reading split')=='reference_reserved' for r in rows):excluded['reserved']+=1;continue
        if any(r.get('Task')!='Open-ended' or r.get('Composition')!='Same model' for r in rows):excluded['not_same_model_open_ended']+=1;continue
        first=[r for r in rows if type(r.get('Turn')) is int and 1<=r['Turn']<=6]
        if len(first)!=6 or {r['Turn'] for r in first}!=set(range(1,7)):excluded['incomplete_or_ambiguous_opening']+=1;continue
        if any(r.get('Assessment status')!='Complete' or r.get('Observed history')!='Clean recorded path' for r in first):excluded['incomplete_assessment_or_flagged_history']+=1;continue
        if len({r['Model ID'] for r in first})!=1:excluded['mixed_opening']+=1;continue
        lineage=first[0]['Lineage']
        if lineage in seen:excluded['duplicate_exact_structure_group']+=1;continue
        seen.add(lineage)
        for field in fields:
            vs=[r.get(field) for r in first]
            if all(type(v) in (int,float) and math.isfinite(v) for v in vs):samples[first[0]['Model ID']][field].append(statistics.mean(vs))
    return {'schema':'behaviorlab.replication-precision-sensitivity/1','matrix_fingerprint':matrix['fingerprint'],
            'method':'One first-six mean per complete clean recorded same-model open-ended discovery record, exact transcript-structure groups deduplicated. Reserved records excluded. Historical independence and common protocol are not established; SDs inform sensitivity, not confirmatory power.',
            'excluded':dict(excluded),'models':[{'model':model,'outcomes':[{'topic':f.removeprefix('Score · '),'n':len(v),'mean':statistics.mean(v),'sd':statistics.stdev(v) if len(v)>1 else None} for f,v in sorted(outcomes.items())]} for model,outcomes in sorted(samples.items())],
            'scenarios':[{'sd':sd,'mean_half_width':h,'roots_per_cell_mean':math.ceil((1.96*sd/h)**2),
                          'difference_half_width':h,'roots_per_cell_two_cell_difference':math.ceil(2*(1.96*sd/h)**2)} for sd in (15,25,35) for h in (5,10)],
            'formula':'Normal approximation for a single 95% interval with planning SD held fixed: n=ceil((1.96*SD/h)^2) for a cell mean; n=ceil(2*(1.96*SD/h)^2) per cell for an independent equal-sized two-cell difference. No multiplicity, SD-estimation, clustering, bounded-score or attrition adjustment; this is not a power calculation.',
            'allocation_status':'No sample size selected or executed.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('matrix',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    result=calculate(json.loads(args.matrix.read_text()))
    with args.output.open('x') as out:json.dump(result,out,ensure_ascii=False,indent=2);out.write('\n')
