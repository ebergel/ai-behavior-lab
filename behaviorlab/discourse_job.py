"""Allowlisted detached full-corpus classifier job; no model supervises execution."""
from datetime import datetime, timezone
import json
from pathlib import Path

from .common import require
from .jev_atlas import read_record, locked
from . import discourse_corpus as corpus

JOB_ID = 'mind-discourse-corpus-v1'
PLAN_SHA = '5f7bebae4472d6cab782364479b6999c120c472118c0e5e02ff0f208c71f60ac'
RELEASE_SHA = '9f849cabccd155bfe0752a4fb594eea0352562db337a88c557c178435319f168'
RECOVERY_SHA = 'cf1eacffeaf51663069fb146b54f30f2686633bbd440260f6f868c094ec8f2b5'
_cache = {}


def check(workspace):
    root=Path(workspace)/corpus.EXECUTION;pp=Path(workspace)/corpus.ROOT/'plan.json';rp=root/'release.json'
    sig=tuple((str(p.resolve()),p.stat().st_mtime_ns,p.stat().st_size) for p in (pp,rp))
    if sig not in _cache:
        plan=read_record(pp);release=read_record(rp)
        require(plan['sha256']==PLAN_SHA and release['sha256']==RELEASE_SHA and release['plan_sha256']==plan['sha256'], 'Registered corpus allocation differs')
        require(release['usd_ceiling']==10 and release['ceiling_nanodollars']==10_000_000_000, 'Corpus budget differs')
        _cache.clear();_cache[sig]=(plan,release)
    plan,release=_cache[sig]
    require(release['software_sha256']==corpus.software(),'Frozen corpus software changed')
    if (root/'recovery-20260919-v2.json').exists():
        from . import discourse_recovery_v2 as recovery
        r=read_record(root/recovery.RECOVERY)
        require(r['sha256']==RECOVERY_SHA and r['software_sha256']==recovery.recovery_software(),'Registered recovery differs')
    return root,plan,release


def status(workspace):
    from . import lab_jobs
    runtime=lab_jobs.directory(workspace,JOB_ID);state=lab_jobs.read_state(runtime)
    out={'id':JOB_ID,'title':'Mind & discourse · full corpus · two wordings','status':'prepared','planned':19316,
         'complete':0,'attempts':0,'known_cost_usd':0,'unknown_reserved_usd':0,'effective_ceiling_usd':10,
         'default_ceiling_usd':10,'can_start':False,'can_pause':False,
         'result_url':'/#view=discourse&lens=%7B%22batch%22%3A%22corpus%22%7D','error':'','updated_at':state.get('updated_at')}
    try:
        root,plan,release=check(workspace);progress={}
        if (root/'.status.json').exists():progress=json.loads((root/'.status.json').read_text())
        if progress:require(progress['plan_sha256']==PLAN_SHA and progress['release_sha256']==RELEASE_SHA,'Progress allocation differs')
        out.update(planned=plan['counts']['logical_requests'],complete=progress.get('completed_assessments',plan['counts']['reuse_requests']),
                   attempts=progress.get('new_attempts',0),known_cost_usd=progress.get('known_cost_usd',0),
                   unknown_reserved_usd=progress.get('unknown_cost_reserved_usd',0),updated_at=progress.get('at',out['updated_at']))
        launching=state.get('status')=='starting' and 0<=(datetime.now(timezone.utc)-datetime.fromisoformat(state['updated_at'])).total_seconds()<30
        active=lab_jobs.busy(runtime/'worker.lock') or lab_jobs.busy(root/'.runner.lock') or launching
        if active:out.update(status='running',can_pause=True)
        elif progress.get('state')=='complete':out['status']='complete'
        elif progress.get('state')=='complete_with_unknowns':
            out.update(status='complete_with_unknowns',error='Continuation finished. Four preserved transport outcomes remain unknown and were not repeated.')
        elif (root/'recovery-20260919-v2.json').exists() and progress.get('new_attempts')==18175:
            out.update(status='paused',can_start=True,error='Frozen continuation: 1,021 never-dispatched assessments; four preserved unknowns remain excluded.')
        elif progress.get('state') in ('stopped','running','backoff','draining') or state.get('status')=='blocked':
            out.update(status='blocked',error='Worker stopped; inspect durable receipts before resuming. Unknown requests are never repeated.')
        else:out.update(status='paused' if out['attempts'] else 'prepared',can_start=True)
        out['pause_requested']=(root/'PAUSE').exists()
    except (OSError,ValueError,KeyError,TypeError):out.update(status='blocked',error='The frozen corpus allocation or evidence needs review.')
    return out


def worker(workspace):
    from . import lab_jobs
    runtime=lab_jobs.directory(workspace,JOB_ID)
    try:
        with locked(runtime/'worker.lock',blocking=False):
            root,_,_=check(workspace);lab_jobs.write_state(runtime,status='running')
            if (root/'recovery-20260919-v2.json').exists():
                from . import discourse_recovery_v2
                report=discourse_recovery_v2.run(workspace,root)
            else:report=corpus.run(workspace,root)
            state=report['state'] if report['state'] in ('complete','complete_with_unknowns') else 'paused' if report['state']=='paused' else 'blocked'
            lab_jobs.write_state(runtime,status=state)
    except BlockingIOError:return
    except Exception:lab_jobs.write_state(runtime,status='blocked',error='Corpus worker stopped. Inspect preserved evidence; no automatic restart.')
