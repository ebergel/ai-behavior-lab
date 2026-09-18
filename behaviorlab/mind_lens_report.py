"""Read-only analysis of the frozen Borges/Plato wording probe."""
from pathlib import Path
from statistics import mean, median
import json

from .common import require
from .jev_atlas import now, read_record, write_record
from .mind_lens_probe import ROOT, VARIANTS, receipts, summary


def build(workspace):
    root=Path(workspace)/ROOT;plan=read_record(root/'plan.json');execution=summary(root,plan)
    require(execution['complete']==72 and not execution['stopped'],'Complete all 72 requests before paired analysis')
    rows,_=receipts(root,plan);samples=[]
    for s in plan['samples']:
        probabilities={v:next(rows[i['id']][-1]['answers'] for i in plan['items'] if i['sample_id']==s['id'] and i['variant']==v) for v in VARIANTS}
        samples.append(dict(s,probabilities={v:{f:a['noul'] for f,a in values.items()} for v,values in probabilities.items()}))
    groups={}
    for kind in ('transcript','synthetic'):
        selected=[s for s in samples if s['kind']==kind];groups[kind]={}
        for f in ('a','b'):
            effects={}
            for other in ('name_only','name_and_definition'):
                differences=[s['probabilities'][other][f]-s['probabilities']['definition_only'][f] for s in selected]
                effects[other+'_minus_definition_only']={'n':len(selected),'mean_difference':mean(differences),
                    'mean_absolute_difference':mean(abs(d) for d in differences),'median_absolute_difference':median(abs(d) for d in differences),
                    'max_absolute_difference':max(abs(d) for d in differences)}
            groups[kind][f]={'mean_probability':{v:mean(s['probabilities'][v][f] for s in selected) for v in VARIANTS},
                'count_probability_at_least_80_percent':{v:sum(s['probabilities'][v][f]>=.8 for s in selected) for v in VARIANTS},'paired_differences':effects}
    base=next(s for s in samples if s['id']=='ordinary')
    cue_effects={s['id']:{v:{f:s['probabilities'][v][f]-base['probabilities'][v][f] for f in ('a','b')} for v in VARIANTS}
                for s in samples if s['id'] in ('ordinary_borges_cue','ordinary_plato_cue')}
    return {'schema':'behaviorlab.mind-lens-analysis/1','created_at':now(),'author':'Codex','plan_sha256':plan['sha256'],
        'execution':execution,'feature_labels':{f['id']:f['label'] for f in plan['spec']['features']},
        'samples':samples,'group_summaries':groups,'author_cue_differences':cue_effects,
        'interpretation':plan['interpretation']+' Each wording was assessed once per passage; there are no repeatability estimates. Named-defined versus definition-only also changes minor grammar. Synthetic controls are not a validated test set.'}


def markdown(result):
    lines=['# Borges-like and Plato-like: JEV test results','',
           f"Completed {result['execution']['complete']} requests in {result['execution']['attempts']} attempts; reported cost ${result['execution']['known_cost_usd']:.9f}.",'',
           'Values below are JEV’s probability of answering yes to each question. They are not degrees of similarity, author attribution probabilities, depth scores or human-validated labels. Each text can score highly on both features or neither.','',
           'Question definitions, selection and exact inputs: [prepared protocol](BORGES-PLATO-PROBE.md).','']
    for kind,title in [('synthetic','Synthetic controls — authored by Codex'),('transcript','Existing transcript passages')]:
        lines.extend(['## '+title,'', '| Passage | Borges: name | Definition | Both | Plato: name | Definition | Both |','|---|---:|---:|---:|---:|---:|---:|'])
        for n,s in enumerate(result['samples'],1):
            if s['kind']!=kind:continue
            label=s['title'] if kind=='synthetic' else s['model_label']
            values=[s['probabilities'][v][f] for f in ('a','b') for v in VARIANTS]
            lines.append(f"| [{n}. {label}](#passage-{n}) | "+' | '.join(f'{v*100:.1f}%' for v in values)+' |')
        lines.append('')
    lines.extend(['## Paired wording differences on the 16 transcript passages','',
                  '| Feature | Name-only vs definition: mean absolute difference | Named definition vs definition: mean absolute difference |',
                  '|---|---:|---:|'])
    for f,title in result['feature_labels'].items():
        d=result['group_summaries']['transcript'][f]['paired_differences']
        lines.append(f"| {title} | {d['name_only_minus_definition_only']['mean_absolute_difference']*100:.1f} points | {d['name_and_definition_minus_definition_only']['mean_absolute_difference']*100:.1f} points |")
    lines.extend(['',result['interpretation'],'','## Reading the passages',''])
    for n,s in enumerate(result['samples'],1):
        lines.extend([f'<a id="passage-{n}"></a>',f"### {n}. {s['title']}",'',f"{s['kind']} · {s['words']} words · `{s['id']}`.",''])
        if s['kind']=='transcript':lines.extend([f"{s['model_label']} · [Open conversation](http://127.0.0.1:8765/#run={s['run_id']}&message={s['message_id']}).",''])
        else:lines.extend([s['purpose'],''])
        lines.extend(['> '+s['text'].replace('\n','\n> '),''])
    return '\n'.join(lines)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',default='workspace');p.add_argument('--report',default='docs/BORGES-PLATO-RESULTS.md');a=p.parse_args()
    result=build(a.workspace);write_record(Path(a.workspace)/ROOT/'analysis.json',result)
    with Path(a.report).open('x') as f:f.write(markdown(result))
    print(json.dumps({'execution':result['execution'],'groups':result['group_summaries'],'author_cue_differences':result['author_cue_differences']},indent=2))
