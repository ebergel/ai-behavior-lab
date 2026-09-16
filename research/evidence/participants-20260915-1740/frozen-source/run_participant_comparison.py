"""Explicit paid experiment entry point; Explorer never calls this script."""
import argparse
from pathlib import Path

from behaviorlab.common import canonical, fingerprint, read_json, sha256, timestamp
from behaviorlab.journal import read_events
from behaviorlab.participants import OpenRouter, credential, create, execute, make_plan, report, slots
from behaviorlab.runner import campaign_documents
from behaviorlab.seeds import require_clean


def prepare(base, backend):
    plan = make_plan()
    # Audit all discoverable frozen campaign nodes, not only successful requests.
    previous = []; inspected = {}
    for pattern in ('*/events.jsonl','*/*/events.jsonl'):
        for path in sorted(Path('workspace').glob(pattern)):
            if {'private','explorer'}.intersection(path.parts): continue
            events = read_events(path); inspected[str(path)] = sha256(path.read_bytes())
            if events[0]['kind'] == 'campaign_created':
                protocol, registry, _ = campaign_documents(events)
                for n in protocol.nodes():
                    m = registry.model(n.model)
                    previous.append({'id':str(path)+'/'+n.id,'model':m.digest or m.tag,'seed':n.seed,'matched_group':None})
            elif events[0]['kind'] == 'participant_comparison_created':
                old = events[0]['payload']['plan']; jobs = {j['id']:j for j in old['jobs']}
                for slot in slots(old):
                    previous.append({'id':str(path)+'/'+slot['id'],'model':old['models'][jobs[slot['job']]['model']]['model'],
                                     'seed':slot['seed'],'matched_group':None})
    jobs = {j['id']:j for j in plan['jobs']}
    entries = [{'id':s['id'],'model':plan['models'][jobs[s['job']]['model']]['model'],
                'seed':s['seed'],'matched_group':None} for s in slots(plan)]
    audit = require_clean(entries, previous)
    audit.update(allocations=entries, prior_journal_hashes=inspected,
                 haiku_seed_scope='Allocated IDs only; Haiku does not accept seeds. No matched random draws claimed.')
    verification = backend.verify(plan)
    files = ['behaviorlab/participants.py','behaviorlab/backends.py','behaviorlab/common.py','behaviorlab/journal.py',
             'scripts/run_participant_comparison.py','docs/PARTICIPANT-COMPARISON.md']
    code = {str(Path(p).resolve()):sha256(Path(p).read_bytes()) for p in files}
    create(base, plan, verification, audit, code)
    print(canonical({'created':str(base),'plan_sha256':fingerprint(plan),'max_calls':plan['max_calls'],
                     'budget_usd':plan['budget_usd'],'seed_audit_unexpected_collisions':audit['unexpected_collisions']}),flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('action',choices=['prepare','smoke','run','report']); p.add_argument('directory',type=Path)
    p.add_argument('--webui-token-file',default='workspace/private/webui-token'); args = p.parse_args()
    if args.action == 'report':
        print(canonical(report(read_events(args.directory/'events.jsonl'))))
    else:
        backend = OpenRouter(credential(args.webui_token_file))
        if args.action == 'prepare': prepare(args.directory,backend)
        else:
            def progress(stage,key):
                if stage == 'after_result' and (key.endswith(':1') or int(key.rsplit(':',1)[1])%10 == 0):
                    print(canonical({'at':timestamp(),'completed':key}),flush=True)
            print(canonical(execute(args.directory,backend,smoke_only=args.action=='smoke',hook=progress)),flush=True)
