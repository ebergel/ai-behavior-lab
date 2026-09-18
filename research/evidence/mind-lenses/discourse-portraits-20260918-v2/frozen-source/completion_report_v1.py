import json,time
from pathlib import Path
from statistics import mean
from behaviorlab.lab_jobs import status
from behaviorlab.discourse_view import build
from behaviorlab.discourse_portrait_probe import ROOT
from behaviorlab.jev_atlas import write_record,now
from behaviorlab.research_bundle import export_bundle
workspace=Path('workspace')
for _ in range(120):
    progress=status(workspace)
    if progress['status']=='complete':break
    if progress['status']=='blocked':raise RuntimeError('Job needs review; snapshot not started')
    time.sleep(10)
else:raise RuntimeError('Completion wait exhausted; job remains independently controlled')
view=build(workspace);root=workspace/ROOT
assert view['execution']['complete']==240
sample_by_id={s['id']:s for s in view['samples']}
contrasts=[]
for feature in view['spec']['features']:
    k=feature['id'];pairs=[]
    for s in view['samples']:
        if s['kind']=='transcript':
            a=s['probabilities']['name_and_portrait'][k];b=s['probabilities']['name_and_definition'][k]
            pairs.append({'sample_id':s['id'],'portrait':a,'named_definition':b,'difference':a-b,'words':s['words']})
    contrasts.append({'id':k,'label':feature['label'],'largest_changes':sorted(pairs,key=lambda x:-abs(x['difference']))[:5]})
report={'at':now(),'plan_sha256':view['plan_sha256'],'execution':view['execution'],'groups':view['groups'],'word_band_counts':view['word_band_counts'],'contrasts':contrasts,'interpretation':'Development screen, 48 one-per-lineage transcript targets and 12 separate synthetic controls. Wording changes are paired descriptive comparisons, not accuracy improvements, population prevalence or isolated stylistic effects.'}
write_record(root/'completed-analysis-v1.json',report)
e=view['execution'];lines=['# Mind & discourse: first completed comparison','',f"Completed {report['at']}. **240 / 240 unique requests; {e['attempts']} attempts; 6,480 probabilities. Reported cost ${e['known_cost_usd']:.9f}; unresolved-cost reserve ${e['unknown_reserved_usd']:.6f}.**",'',
'All 60 texts have all four question packs. The 48 transcript passages come from distinct lineages across 14 model variants; twelve Codex synthetic controls remain separate. This development screen does not estimate corpus prevalence or validate the classifier against human judgments.','',
'The first four requests were technical checks. A detached Python worker completed the remaining allocation with no supervising model calls. The researcher’s $10 default expenditure preference was honored while retaining this frozen batch’s stricter $2 cap. The allocation is now exhausted.','',
'## Transcript summaries','',
'Means are yes-probabilities in percent. Δ is the paired portrait minus named-definition difference in percentage points. The first three questions were preserved from the original proposal. Portraits change the operational construct and prompt length as well as the prose.','',
'| Lens | Names only | Definitions | Names + definitions | Names + portraits | Mean Δ |','|---|---:|---:|---:|---:|---:|']
for f in view['groups']['transcript']:
    if f['family']!='thinkers':continue
    c=f['conditions'];d=f['contrasts']['name_and_portrait']['mean_difference']
    lines.append('| '+f['label']+' | '+' | '.join(f"{c[v]['mean']*100:.1f}" for v in ['name_only','definition_only','name_and_definition','name_and_portrait'])+f' | {d*100:+.1f} |')
lines+=['','## Reading the contrast','',
'The Mind & discourse interface provides all four scores next to each exact source passage, both tails of each distribution, length/model filters, and a profile matrix. Its paired comparison selector separates the effect of appending a name from the difference produced by replacing the definition with a portrait. Several features may apply to one text, or none.','',
'The eleven discourse questions repeat unchanged between the two named conditions, but the other sixteen questions in their pack change. These are reference comparisons, not exact repeated full requests. The separate synthetic controls have intended contrasts, not independent ground-truth labels.','',
'## Largest portrait changes among transcripts','',
'These are deliberately selected extremes for inspecting the classifier, not representative examples or evidence of philosophical quality.','']
ranked=sorted([(abs(x['difference']),f,x) for f in contrasts if next(q for q in view['spec']['features'] if q['id']==f['id'])['family']=='thinkers' for x in f['largest_changes']],key=lambda x:-x[0])
used=set()
for _,f,x in ranked:
    s=sample_by_id[x['sample_id']]
    if s['id'] in used:continue
    used.add(s['id'])
    lines += [f"**{f['label']} · {s['model_label']} · {s['words']} words.** Named definition {x['named_definition']*100:.1f}%; portrait {x['portrait']*100:.1f}% ({x['difference']*100:+.1f} pp).",'',
              f"[Exact source passage](http://127.0.0.1:8765/#run={s['run_id']}&message={s['message_id']}).",'',
              '> '+s['text'].replace('\n','\n> '),'']
    if len(used)==4:break
Path('docs/MIND-DISCOURSE-RESULTS.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'completed':e},indent=2),flush=True)
result=export_bundle(workspace,Path('/tmp/lab-jobs-research-20260918-v1'))
print(json.dumps({'snapshot':result},indent=2),flush=True)
