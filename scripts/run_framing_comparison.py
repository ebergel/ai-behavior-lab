"""Explicit finite framing screen; no generation is exposed through the app."""
import argparse
from pathlib import Path
from behaviorlab.common import canonical, fingerprint, read_json, sha256
from behaviorlab.framing import execute, make_plan, replay, summary, validate
from behaviorlab.journal import Journal, read_events
from behaviorlab.participants import credential

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);p.add_argument('directory',type=Path);a=p.parse_args()
    if a.action=='prepare':
        plan=validate(make_plan(read_json((a.directory/'catalog.json').read_text()),read_json((a.directory/'routes.json').read_text())))
        files=['behaviorlab/framing.py','behaviorlab/assessment.py','behaviorlab/backends.py','behaviorlab/common.py','behaviorlab/journal.py','scripts/run_framing_comparison.py']
        code={str(Path(f).resolve()):sha256(Path(f).read_bytes()) for f in files}
        (a.directory/'frozen-source').mkdir()
        for f in files:(a.directory/'frozen-source'/Path(f).name).write_bytes(Path(f).read_bytes())
        prior={str(f.resolve()):sha256(f.read_bytes()) for f in Path('workspace').glob('model-assessment*/*') if f.name in ('events.jsonl','reading.json')}
        with Journal(a.directory,create=True) as j:j.append('framing_comparison_created',{'plan':plan,'plan_sha256':fingerprint(plan),'code_hashes':code,'prior_evidence_hashes':prior,'synthetic':False})
        print(canonical({'plan_sha256':fingerprint(plan),'max_calls':48,'budget_usd':'0','seed_allocations':0}))
    else:
        state=replay(read_events(a.directory/'events.jsonl')) if a.action=='report' else execute(a.directory,credential('workspace/private/webui-token'))
        print(canonical(summary(state)))
