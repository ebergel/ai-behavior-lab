"""Prepare once, then run the frozen free-model screen. No paid fallback."""
import argparse
from pathlib import Path
from behaviorlab.assessment import execute, make_plan, make_followup, validate
from behaviorlab.common import canonical, fingerprint, read_json, sha256
from behaviorlab.journal import Journal, read_events
from behaviorlab.participants import credential

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['prepare','run']); p.add_argument('directory',type=Path)
    p.add_argument('--followup-of',type=Path)
    a=p.parse_args()
    if a.action=='prepare':
        catalog=read_json((a.directory/'catalog.json').read_text()); routes=read_json((a.directory/'routes.json').read_text())
        plan=validate(make_followup(catalog,routes,read_events(a.followup_of/'events.jsonl')) if a.followup_of else make_plan(catalog,routes))
        files=['behaviorlab/assessment.py','behaviorlab/backends.py','behaviorlab/common.py','behaviorlab/journal.py','scripts/run_model_assessment.py']
        code={str(Path(f).resolve()):sha256(Path(f).read_bytes()) for f in files}
        frozen=a.directory/'frozen-source'; frozen.mkdir()
        for f in files: (frozen/Path(f).name).write_bytes(Path(f).read_bytes())
        with Journal(a.directory,create=True) as j:
            j.append('model_assessment_created',{'plan':plan,'plan_sha256':fingerprint(plan),'code_hashes':code,'synthetic':False})
        print(canonical({'plan_sha256':fingerprint(plan),'max_calls':plan['max_calls'],'eligible_calls':sum(8 for c in plan['candidates'] if c['route']),'budget_usd':'0'}))
    else:
        state=execute(a.directory,credential('workspace/private/webui-token'))
        print(canonical({'finished':state['finished'],'calls':len(state['requests'])}))
