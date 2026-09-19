"""Frozen recovery: dispatch only originally unstarted requests, retain unknowns.

Original release, source, receipts and aggregate ledger remain authoritative.
The recovery manifest authorizes the exact remaining keys and pins this module.
"""
from .discourse_corpus import *
from . import discourse_corpus as original

RECOVERY = 'recovery-20260919-v1.json'

def recovery_software():
    return dict(software(), discourse_recovery=sha256(Path(__file__).read_bytes()))

def validate_recovery(record, release, ledger, fatal):
    require(record['software_sha256']==recovery_software(),'Recovery software changed')
    require(record['release_sha256']==release['sha256'],'Recovery release changed')
    baseline=record['baseline_ledger']
    require(len(ledger)>=len(baseline) and canonical(ledger[:len(baseline)])==canonical(baseline),'Recovery baseline changed')
    excluded={tuple(x['key']) for x in record['excluded']}
    allowed={tuple(x) for x in record['order']}
    baseline_keys={tuple(x['key']) for x in baseline}
    require(not allowed & baseline_keys and not allowed & excluded,'Recovery would repeat an original request')
    require(allowed=={tuple(x) for x in release['order']}-baseline_keys,'Recovery remaining allocation differs')
    require({x['sequence'] for x in record['excluded']}=={x['sequence'] for x in fatal if x['sequence']<=len(baseline)},'Original unknown outcomes changed')
    require(all(tuple(x['key']) in allowed for x in ledger[len(baseline):]),'Request outside recovery allocation')
    return excluded

def prepare_recovery(workspace,directory):
    directory=Path(directory)
    with locked(directory/'.runner.lock',blocking=False):
        require(not (directory/RECOVERY).exists(),'Recovery is already frozen')
        release=read_record(directory/'release.json')
        require(release['software_sha256']==software(),'Original software changed')
        plan,results,attempts,ledger,fatal=replay(workspace,directory,release)
        require(fatal,'Recovery requires inspected unresolved outcomes')
        excluded=[e for e in ledger if e['sequence'] in {f['sequence'] for f in fatal}]
        require(all(e['http_status'] is None and e['known_nanodollars'] is None for e in excluded),'Only inspected transport-unknown outcomes may be set aside')
        order=[k for k in release['order'] if tuple(k) not in attempts and tuple(k) not in results]
        record={'schema':'behaviorlab.discourse-recovery/1','at':now(),'release_sha256':release['sha256'],
            'approval':'Researcher, 19 September 2026: I agree with next plan steps, go. Continue never-dispatched requests; retain uncertain outcomes and original aggregate $10 cap.',
            'baseline_ledger':ledger,'excluded':excluded,'order':order,'software_sha256':recovery_software(),
            'policy':'Preserve original unknowns. Dispatch only frozen never-started keys. Stop on any new unknown. Original total attempt, retry and spending ceilings apply. Maximum four workers and four starts/second.'}
        validate_recovery(record,release,ledger,fatal)
        write_record(directory/RECOVERY,record)
        (directory/'frozen-source'/'discourse_recovery.py').write_bytes(Path(__file__).read_bytes())
        return {'remaining':len(order),'excluded':len(excluded),'committed_usd':sum(x['charge_nanodollars'] for x in ledger)/1e9}

def run(workspace, directory, max_calls=None, send=None, key=None, pause=time.sleep):
    directory=Path(directory); stop_requested=[False]
    with locked(directory/'.runner.lock',blocking=False):
        release=read_record(directory/'release.json')
        require(release['software_sha256']==software(),'Execution software changed after freeze')
        plan,results,attempts,ledger,fatal=replay(workspace,directory,release)
        recovery=read_record(directory/RECOVERY)
        excluded=validate_recovery(recovery,release,ledger,fatal)
        release=dict(release,max_workers=min(4,release['max_workers']),max_requests_per_second=min(4,release['max_requests_per_second']))
        targets={t['id']:t for t in plan['targets']}
        if len(results)+len(excluded)==plan['counts']['logical_requests']:
            out=status(plan,release,results,ledger,'complete_with_unknowns','Recovery exhausted; original unknown outcomes preserved');atomic_status(directory,out);return out
        if any(e['sequence'] not in {x['sequence'] for x in recovery['excluded']} for e in fatal):
            out=status(plan,release,results,ledger,'stopped','Unresolved/non-retryable saved attempt; inspect evidence');atomic_status(directory,out);return out
        require(max_calls is None or type(max_calls) is int and max_calls>0,'Invalid call slice')
        if send is None: key=credential(workspace);send=transport
        queue=deque(tuple(k) for k in release['order'] if tuple(k) not in results and tuple(k) not in excluded)
        active={}; started=0; reason=None; cooldown=0; next_dispatch=0; published=0
        new_complete=sum(v['origin']=='execution' for v in results.values())
        for k,n in attempts.items():
            if k in results or k in excluded: continue
            if n>=release['max_attempts_per_request']:reason='Retry limit reached';break
            last=next(e for e in reversed(ledger) if e['key']==k)
            elapsed=max(0,time.time()-datetime.fromisoformat(last['at']).timestamp())
            delay=max(release['backoff_seconds'][n-1],last['retry_after'])
            cooldown=max(cooldown,time.monotonic()+max(0,delay-elapsed))
        def halt(signum,frame):stop_requested[0]=True
        import threading
        original_signals={}
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGINT,signal.SIGTERM):original_signals[sig]=signal.signal(sig,halt)
        try:
            with ThreadPoolExecutor(max_workers=release['max_workers']) as pool:
                while queue or active:
                    if stop_requested[0] or (directory/'PAUSE').exists(): reason=reason or 'Pause requested; inflight calls drained'
                    workers=min(release['max_workers'],1 if new_complete<release['warmup'][0] else 4 if new_complete<release['warmup'][1] else release['max_workers'])
                    if max_calls is not None and started>=max_calls: reason=reason or 'Requested slice complete'
                    clock=time.monotonic()
                    if not reason and queue and len(active)<workers and clock>=max(cooldown,next_dispatch):
                        k=queue.popleft();n=attempts[k]+1
                        charge=sum(e['charge_nanodollars'] for e in ledger)
                        retries=sum(max(0,v-1) for v in attempts.values())
                        if len(ledger)>=release['max_attempts'] or (n>1 and retries>=release['retry_allowance']):reason='Aggregate attempt allocation exhausted'
                        elif n>release['max_attempts_per_request']:reason='Per-request retry limit reached'
                        elif charge+RESERVE>release['ceiling_nanodollars']:reason='Spending ceiling reached'
                        else:
                            raw=payload(plan,targets[k[0]],k[1]);expected=targets[k[0]]['requests'][k[1]]
                            require(fingerprint(raw)==expected['payload_sha256'],'Frozen request changed')
                            marker={'recovery_sha256':recovery['sha256'],'release_sha256':release['sha256'],'target_id':k[0],'variant':k[1],'attempt':n,'sequence':len(ledger)+1,'at':now(),'payload':raw,'reserved_nanodollars':RESERVE}
                            rp,_=paths(directory,k,n);write_record(rp,marker);req=read_record(rp)
                            entry={'key':k,'attempt':n,'sequence':marker['sequence'],'request_sha256':req['sha256'],'response_sha256':None,'http_status':None,'charge_nanodollars':RESERVE,'known_nanodollars':None,'at':marker['at'],'retry_after':0}
                            ledger.append(entry);attempts[k]=n;started+=1
                            active[pool.submit(dispatch,directory,req,send,key)]=entry
                            next_dispatch=clock+max(1/release['max_requests_per_second'],expected['bytes']/release['max_request_bytes_per_second'])
                    done=wait(active,timeout=.02,return_when=FIRST_COMPLETED).done if active else set()
                    for future in done:
                        entry=active.pop(future);res=future.result();k=entry['key']
                        answers,charge=evaluate(res,plan['packs'][k[1]]['questions'])
                        entry.update(response_sha256=res['sha256'],http_status=res['http_status'],at=res['at'],retry_after=res['retry_after_seconds'])
                        if answers is not None:
                            entry.update(known_nanodollars=charge,charge_nanodollars=charge)
                            new_complete += 1
                            results[k]={'answers':answers,'origin':'execution','receipt':dict(entry),'cost_usd':charge/1e9}
                        elif res['http_status'] in release['retryable_http'] and not res['error'] and entry['attempt']<release['max_attempts_per_request']:
                            delay=max(release['backoff_seconds'][entry['attempt']-1],res['retry_after_seconds'])
                            cooldown=max(cooldown,time.monotonic()+delay);queue.appendleft(k)
                        else:reason=reason or 'Non-retryable/invalid response or exhausted request retries'
                    if time.monotonic()-published>=5 or done and (len(results)%50==0):
                        out=status(plan,release,results,ledger,'draining' if reason and active else 'backoff' if time.monotonic()<cooldown else 'running',reason,len(active));atomic_status(directory,out)
                        print(canonical(out),flush=True);published=time.monotonic()
                    if reason and not active:break
                    if not active and queue:pause(min(.2,max(.001,max(cooldown,next_dispatch)-time.monotonic())))
            state='complete_with_unknowns' if len(results)+len(excluded)==plan['counts']['logical_requests'] else 'paused' if reason in ('Requested slice complete','Pause requested; inflight calls drained') else 'stopped'
            out=status(plan,release,results,ledger,state,reason);atomic_status(directory,out)
            write_record(directory/'summaries'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),out)
            return out
        finally:
            for sig,handler in original_signals.items():signal.signal(sig,handler)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);p.add_argument('--workspace',default='workspace');a=p.parse_args()
    ws=Path(a.workspace);directory=ws/EXECUTION
    print(canonical(prepare_recovery(ws,directory) if a.action=='prepare' else run(ws,directory)),flush=True)

if __name__=='__main__':main()
