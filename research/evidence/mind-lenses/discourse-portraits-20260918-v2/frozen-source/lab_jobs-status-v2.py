"""Allowlisted local Python jobs. Model inference stays in frozen runners.

The UI never supplies code, paths, provider URLs, credentials or request payloads.
A worker survives the Explorer and browser. Receipts remain the source of truth.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .common import require
from .jev_atlas import locked, now, read_record
from . import discourse_portrait_probe as portrait

DEFAULT_CEILING = 10.0
JOB_ID = 'mind-portraits-v2'
PLAN_SHA = '49f5b17c48e18825b7635c591163e9505cc3806fe1bbe15b7bf28e548de3e0b3'


def directory(workspace, identity):
    require(identity == JOB_ID, 'Unknown lab job')
    return Path(workspace) / '.lab-jobs' / identity


def busy(path):
    try:
        with locked(path, blocking=False):return False
    except BlockingIOError:return True


def read_state(root):
    try:return json.loads((root/'state.json').read_text())
    except FileNotFoundError:return {}


def write_state(root, **values):
    root.mkdir(parents=True, exist_ok=True)
    target=root/'state.json';temp=root/f'.state-{os.getpid()}.tmp'
    with temp.open('w') as f:
        json.dump(dict(values, updated_at=now()),f);f.flush();os.fsync(f.fileno())
    os.replace(temp,target)


def check(workspace):
    root=Path(workspace)/portrait.ROOT;plan=read_record(root/'plan.json')
    require(plan['sha256']==PLAN_SHA, 'Job plan differs from registered allocation')
    require(plan['software_sha256']==portrait.software(), 'Frozen assessment software changed')
    require(plan['budget']==portrait.BUDGET and plan['endpoint']==portrait.ENDPOINT and plan['model']==portrait.MODEL, 'Frozen route or budget differs')
    require(0 < plan['budget']['usd_ceiling'] <= DEFAULT_CEILING, 'Job exceeds the $10 expenditure ceiling')
    require((root/'authorization.json').is_file(), 'Job authorization has not been registered')
    auth=read_record(root/'authorization.json')
    require(auth.get('explicit_confirmation') is True and auth.get('plan_sha256')==plan['sha256'] and auth.get('endpoint')==plan['endpoint'] and auth.get('unique_requests')==240 and auth.get('max_attempts')==252 and auth.get('usd_ceiling')==plan['budget']['usd_ceiling'], 'Registered authorization differs from the frozen job')
    return root,plan


def status(workspace, identity=JOB_ID):
    runtime=directory(workspace,identity);state=read_state(runtime)
    result={'id':identity,'title':'Mind & discourse · four-wording comparison','status':'prepared','planned':240,'complete':0,'attempts':0,'known_cost_usd':0,'unknown_reserved_usd':0,'effective_ceiling_usd':2,'default_ceiling_usd':DEFAULT_CEILING,'can_start':False,'can_pause':False,'result_url':'/#view=discourse','error':'','updated_at':state.get('updated_at')}
    try:
        root,plan=check(workspace);report=portrait.summary(root,plan)
        result.update({k:report[k] for k in ('planned','complete','attempts','known_cost_usd','unknown_reserved_usd')})
        histories,_=portrait.receipts(root,plan)
        exhausted=(report['attempts']>=252 or any(len(h)>=3 and h[-1]['status']=='overload' for h in histories.values()) or (sum(max(0,len(h)-1) for h in histories.values())>=12 and any(h[-1]['status']=='overload' for h in histories.values())))
        launching=False
        if state.get('status')=='starting':
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(state['updated_at'])).total_seconds()
            launching=0<=age<30
        worker_active=busy(runtime/'worker.lock')
        runner_active=busy(root/'.runner.lock')
        if report['complete']==report['planned']:result['status']='complete'
        elif worker_active or runner_active or launching:
            # A durable request precedes its response; pending in-flight receipts are normal.
            result.update(status='running',can_pause=worker_active or launching)
        elif report['stopped'] or exhausted:
            result.update(status='blocked',error='The saved evidence requires review; no failed or uncertain request will be repeated.')
        elif state.get('status')=='blocked':result.update(status='blocked',error=state.get('error','Worker stopped; inspect saved evidence.'))
        else:result.update(status='paused' if report['attempts'] else 'prepared',can_start=True)
        result['pause_requested']=(runtime/'pause').exists()
    except (OSError,ValueError,KeyError,TypeError):
        result.update(status='blocked',error='The registered plan, authorization or frozen software needs review.')
    return result


def listing(workspace):
    return {'default_ceiling_usd':DEFAULT_CEILING,'jobs':[status(workspace)]}


def start(workspace, identity, spawn=subprocess.Popen):
    runtime=directory(workspace,identity);workspace=Path(workspace).resolve()
    with locked(runtime/'control.lock'):
        current=status(workspace,identity)
        if current['status'] in ('running','complete'):return current
        require(current['can_start'],current['error'] or 'Job cannot start')
        (runtime/'pause').unlink(missing_ok=True)
        write_state(runtime,status='starting')
        env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
        # Discard bulk logs; the durable receipt ledger and compact state are authoritative.
        try:
            spawn([sys.executable,'-m','behaviorlab.lab_jobs','worker','--workspace',str(workspace),'--id',identity],cwd=str(Path(__file__).resolve().parents[1]),env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
        except OSError:
            write_state(runtime,status='blocked',error='Could not start the Python worker.')
            raise ValueError('Could not start the Python worker') from None
    return status(workspace,identity)


def pause(workspace, identity):
    root=directory(workspace,identity)
    with locked(root/'control.lock'):
        current=status(workspace,identity)
        if current['can_pause']:(root/'pause').touch()
    return status(workspace,identity)


def worker(workspace, identity, execute=None, sleep=time.sleep):
    runtime=directory(workspace,identity)
    try:
        with locked(runtime/'worker.lock',blocking=False):
            check(workspace);write_state(runtime,status='running')
            execute=execute or portrait.execute
            while True:
                if (runtime/'pause').exists():write_state(runtime,status='paused');return
                # One request at a time makes a pause graceful, preserving any in-flight receipt.
                report=execute(workspace,max_calls=1)
                write_state(runtime,status='running')
                if report['stopped']:
                    write_state(runtime,status='blocked',error='Assessment stopped; inspect the preserved response before further work.');return
                if report['complete']==report['planned']:
                    # The frozen runner writes its final summary on the last allocated request.
                    write_state(runtime,status='complete');return
                sleep(portrait.EXECUTION['minimum_interval_seconds'])
    except BlockingIOError:return  # Another worker owns this allocation.
    except Exception:
        # Never echo exception strings: provider failures can contain secrets.
        write_state(runtime,status='blocked',error='Worker stopped. Check the frozen plan and saved receipts; no automatic restart.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['start','status','pause','worker']);p.add_argument('--workspace',default='workspace');p.add_argument('--id',default=JOB_ID);a=p.parse_args()
    if a.action=='worker':worker(a.workspace,a.id)
    else:print(json.dumps({'start':start,'status':status,'pause':pause}[a.action](a.workspace,a.id),indent=2))

if __name__=='__main__':main()
