"""Explicit finite GPT-4o screen; no inference control in the Explorer."""
import argparse
from pathlib import Path
from behaviorlab.common import canonical,fingerprint,read_json,sha256
from behaviorlab.journal import Journal,read_events
from behaviorlab.gpt4o_screen import execute,make_plan,replay,summary,validate
from behaviorlab.participants import credential

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);p.add_argument('directory',type=Path);a=p.parse_args()
    if a.action=='prepare':
        previous={}
        for pattern in ('*/events.jsonl','*/*/events.jsonl','*/reading.json'):
            for path in Path('workspace').glob(pattern):
                if not {'private','explorer'}.intersection(path.parts):previous[str(path.resolve())]=sha256(path.read_bytes())
        prior=[]
        plan=validate(make_plan(read_json((a.directory/'catalog.json').read_text()),read_json((a.directory/'routes.json').read_text()),prior))
        files=['behaviorlab/gpt4o_screen.py','behaviorlab/framing.py','behaviorlab/participants.py','behaviorlab/assessment.py','behaviorlab/backends.py','behaviorlab/common.py','behaviorlab/journal.py','scripts/run_gpt4o_screen.py']
        code={str(Path(f).resolve()):sha256(Path(f).read_bytes()) for f in files}
        (a.directory/'frozen-source').mkdir()
        for f in files:(a.directory/'frozen-source'/Path(f).name).write_bytes(Path(f).read_bytes())
        with Journal(a.directory,create=True) as j:j.append('gpt4o_screen_created',{'plan':plan,'plan_sha256':fingerprint(plan),'code_hashes':code,'prior_evidence_hashes':previous,'synthetic':False})
        print(canonical({'plan_sha256':fingerprint(plan),'max_calls':24,'budget_usd':'0.50','seed_allocations':0}))
    else:
        state=replay(read_events(a.directory/'events.jsonl')) if a.action=='report' else execute(a.directory,credential('workspace/private/webui-token'))
        print(canonical(summary(state)))
