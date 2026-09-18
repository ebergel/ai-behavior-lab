"""Read the separately frozen corpus through the existing descriptive viewer."""
from pathlib import Path
from . import discourse_corpus as corpus
from .jev_atlas import read_record, locked


def load(workspace):
    root=Path(workspace)/corpus.EXECUTION
    release=read_record(root/'release.json');plan=read_record(Path(workspace)/corpus.ROOT/'plan.json')
    from .common import require
    require(plan['sha256']==release['plan_sha256'], 'Corpus view release differs')
    _,results,_,ledger,fatal=corpus.replay(workspace,root,release,plan)
    active=False
    try:
        with locked(root/'.runner.lock',blocking=False):pass
    except BlockingIOError:active=True
    progress=corpus.status(plan,release,results,ledger)
    variants=tuple(plan['packs']);histories={};items=[]
    for t in plan['targets']:
        for v in variants:
            identity=t['id']+':'+v;items.append({'id':identity,'sample_id':t['id'],'variant':v})
            if (t['id'],v) in results:histories[identity]=[dict(results[(t['id'],v)],status='complete')]
    viewplan=dict(plan,samples=plan['targets'],items=items,conditions={v:plan['packs'][v]['questions'] for v in variants})
    execution={'planned':progress['logical_requests'],'complete':progress['completed_assessments'],
               'attempts':progress['new_attempts'],'known_cost_usd':progress['known_cost_usd'],
               'unknown_reserved_usd':progress['unknown_cost_reserved_usd'],'reused':plan['counts']['reuse_requests'],
               'stopped':fatal if not active else []}
    return viewplan,histories,execution,active
