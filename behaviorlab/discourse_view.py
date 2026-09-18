"""Read-only descriptive classifier data, paired contrasts and review packet."""
from collections import Counter
from pathlib import Path
from statistics import mean
import math

from .jev_atlas import read_record, locked
from . import discourse_probe, discourse_portrait_probe
from .discourse_probe import ROOT, SPEC, VARIANTS

def release(workspace):
    return discourse_portrait_probe if (Path(workspace)/discourse_portrait_probe.ROOT/"plan.json").exists() else discourse_probe

def export_plan(workspace):
    return read_record(Path(workspace)/release(workspace).ROOT/"plan.json")


def correlation(pairs):
    if len(pairs)<3:return None
    x,y=zip(*pairs);mx,my=mean(x),mean(y)
    den=math.sqrt(sum((v-mx)**2 for v in x)*sum((v-my)**2 for v in y))
    return sum((a-mx)*(b-my) for a,b in pairs)/den if den else None


def feature_stats(samples,features,variants=VARIANTS):
    result=[]
    for feature in features:
        key=feature['id'];conditions={}
        for variant in variants:
            observed=[s for s in samples if key in s['probabilities'][variant]]
            values=[s['probabilities'][variant][key] for s in observed]
            conditions[variant]={'n':len(values),'mean':mean(values) if values else None,
                'at_least_80':sum(v>=.8 for v in values),
                'word_correlation':correlation([(s['words'],s['probabilities'][variant][key]) for s in observed])}
        contrasts={}
        for variant in [v for v in variants if v!='definition_only']:
            baseline='name_and_definition' if variant=='name_and_portrait' else 'definition_only'
            diffs=[s['probabilities'][variant][key]-s['probabilities'][baseline][key] for s in samples
                   if key in s['probabilities'][variant] and key in s['probabilities'][baseline]]
            contrasts[variant]={'baseline':baseline,'n':len(diffs),'mean_difference':mean(diffs) if diffs else None,
                               'mean_absolute_difference':mean(abs(d) for d in diffs) if diffs else None}
        result.append(dict(feature,conditions=conditions,contrasts=contrasts))
    return result


def build(workspace,catalog=None):
    module=release(workspace);variants=module.VARIANTS;root=Path(workspace)/module.ROOT
    if not (root/'plan.json').exists():
        import json
        return {'status':'not_prepared','spec':json.loads(SPEC.read_text()),'samples':[], 'features':[], 'groups':{}}
    plan=read_record(root/'plan.json');histories,_=module.receipts(root,plan);execution=module.summary(root,plan)
    active=False
    try:
        with locked(root/'.runner.lock',blocking=False):pass
    except BlockingIOError:active=True
    by_sample={}
    for item in plan['items']:
        h=histories.get(item['id'],[]);last=h[-1] if h else {}
        by_sample.setdefault(item['sample_id'],{})[item['variant']]=last
    samples=[]
    for source in plan['samples']:
        probs={v:{f:a['noul'] for f,a in by_sample[source['id']][v].get('answers',{}).items()}
               if by_sample[source['id']][v].get('status')=='complete' else {} for v in variants}
        sample=dict(source,probabilities=probs,assessment_status={v:by_sample[source['id']][v].get('status','unassessed') for v in variants})
        sample['source_current']=None
        if catalog is not None and source['kind']=='transcript':
            run=catalog.runs.get(source['run_id'],{})
            msg=next((m for m in run.get('messages',[]) if m['id']==source['message_id']),{})
            sample['source_current']=run.get('source',{}).get('sha256')==source['source_sha256'] and msg.get('text')==source['text']
        samples.append(sample)
    groups={kind:feature_stats([s for s in samples if s['kind']==kind],plan['spec']['features'],variants) for kind in ('transcript','synthetic')}
    base=next(s for s in samples if s['id']=='ordinary')
    cue_differences={s['id']:{v:{k:p-base['probabilities'][v][k] for k,p in s['probabilities'][v].items() if k in base['probabilities'][v]} for v in variants}
                     for s in samples if s['id'] in ('ordinary_borges_cue','ordinary_plato_cue')}
    return {'schema':'behaviorlab.discourse-view/1','status':'complete' if execution['complete']==len(plan['items']) else 'in_progress' if active else 'stopped' if execution['stopped'] else 'in_progress' if execution['attempts'] else 'prepared',
            'plan_sha256':plan['sha256'],'root':module.ROOT,'variants':list(variants),'spec':plan['spec'],'conditions':plan['conditions'],'execution':execution,
            'budget':plan['budget'],'selection':{k:v for k,v in plan['selection'].items() if k!='reserved_lineages'},
            'interpretation':plan['interpretation'],'samples':samples,'groups':groups,'author_cue_differences':cue_differences,
            'word_band_counts':dict(Counter('1–50' if s['words']<=50 else '51–100' if s['words']<=100 else '101–150' if s['words']<=150 else '151+' for s in samples if s['kind']=='transcript')),
            'review_guide':'Judge whether the classifier makes useful, coherent distinctions across passages and wording conditions. No personal passage ratings are required. Probabilities describe yes answers to these questions, not similarity degree, provenance or quality. Synthetic controls remain separate.'}


def review_markdown(plan):
    lines=['# Mind & discourse: expanded classifier screen','',
           '**Prepared, not yet executed.** A separate descriptive classifier, preserving Gem Finder and all existing scores.','',
           '## Exact scope','',
           f"Plan: `{plan['sha256']}`. Destination: `{plan['endpoint']}`. Pinned model: `{plan['model']}`.",'',
           '48 existing nonconfidential model-output passages from 48 lineages, plus 12 Codex-authored synthetic controls. Each text receives three requests: names only, definitions only, and the identical definitions with a label line appended. All 27 independent Noul questions are included in each request: 180 unique requests and 4,860 prospective probabilities.','',
           'New ceiling: **$2 total**, at most 192 attempts (12 aggregate retries, only explicit HTTP 429/529, at most three attempts per request). Failed, malformed or uncertain responses stop dispatch. The runner requires explicit confirmation bound to this exact frozen plan before reading a credential or dispatching. No earlier unused budget is reopened.','',
           'Assessment state contains **only the target text**. No preceding context, source model name, personal notebook, Gem score or expected control classification is sent. The full payloads can be regenerated exactly from the immutable plan and hashes. API credentials remain in private runtime storage.','',
           '## What is being tested','',plan['interpretation'],'',plan['spec']['evaluation'],'',
           'The named features are deliberately narrow, Codex-authored operational proposals. They do not summarize an author’s complete work or establish source attribution. Discourse features describe rhetorical practice; they do not identify the website on which a passage appeared. There is no grand quality score.','',
           'Name-and-definition differs from definition-only by exactly one appended label line. Name-only asks about the learned label and is a different operational question. Independent features can overlap or all be absent; their probabilities need not sum to one. Each condition is assessed once, so wording contrasts are descriptive and include possible response variability.','',
           '## Selection','',plan['selection']['method'],'',
           'The sampling frame is the 1,000 Gem development targets, not the full corpus. No Gem scores enter selection or assessment. All 60 reserved validation lineages remain excluded. No reference-author passages or human labels are used. Word count means whitespace-separated words.','',
           '| Source model | Targets |','|---|---:|']
    lines += [f'| {model} | {n} |' for model,n in plan['selection']['models'].items()]
    lines += ['', '## Operational codebook', '', plan['spec']['scope'], '']
    for family,title in [('thinkers','Sixteen thinkers and writers'),('discourse','Eleven discourse practices')]:
        lines+=['### '+title,'']
        for f in plan['spec']['features']:
            if f['family']==family:lines += [f"**{f['id']} · {f['label']}**",'',f['definition'],'']
    lines += ['## Exact question conditions','','The shared scope above prefixes every question. Feature IDs are opaque to avoid leaking a name in definition-only conditions. Each definition-only question is `Does the target passage exhibit the pattern described below?` followed by `Pattern: [the exact definition above]`. The named-definition condition appends only `Label: [name]`. Names-only asks `Does the target passage exhibit a way of thinking, literary form, or discourse practice associated with this label?` followed by `Label: [name]`. All have `type: noul`.','','## Frozen passages','']
    for n,s in enumerate(plan['samples'],1):
        lines += [f"### {n}. {s['title']}",'',f"{s['kind']} · {s['words']} words · `{s['id']}`.",'']
        if s['kind']=='transcript':lines += [f"{s['model_label']} · [Source conversation](http://127.0.0.1:8765/#run={s['run_id']}&message={s['message_id']}) · source SHA-256 `{s['source_sha256']}`.",'']
        else:lines += [s['purpose'],'']
        lines += ['> '+s['text'].replace('\n','\n> '),'']
    return '\n'.join(lines)+'\n'
