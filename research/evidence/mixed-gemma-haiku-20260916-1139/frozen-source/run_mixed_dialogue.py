"""Explicit prepare/run/report for the approved four-root local–cloud pilot."""
import argparse
from decimal import Decimal
from pathlib import Path

from behaviorlab.backends import HTTPBackend
from behaviorlab.common import canonical, fingerprint, read_json, require, sha256
from behaviorlab.journal import Journal, read_events
from behaviorlab.mixed_dialogue import execute, local_model, make_plan, replay, slots, summary, validate
from behaviorlab.participants import credential
from behaviorlab.protocol import Registry
from behaviorlab.runner import campaign_documents


def prepare(directory):
    d=Path(directory); registry=Registry.load('design/ollama-context-models.json')
    row=read_json(registry.model('B').metadata_json)
    routes=read_json((d/'routes.json').read_text()); route=next(r for r in routes['endpoints'] if r['tag']=='anthropic')
    metadata={'catalog_sha256':sha256((d/'catalog.json').read_bytes()),'routes_sha256':sha256((d/'routes.json').read_bytes()),
              'human_interpretation':'Reduced human steering is the operational target; an untouched model self is a hypothesis, not an established observation.'}
    plan=validate(make_plan(row,route,metadata)); allocated=set(plan['seed_allocations']); require(len(allocated)==36,'Local seed collision')
    prior={}; previous_seeds=set()
    def inspect(value,key=''):
        if isinstance(value,dict):
            for k,v in value.items():inspect(v,k)
        elif isinstance(value,list):
            for v in value:inspect(v,key)
        elif type(value) is int and 'seed' in key:previous_seeds.add(value)
    for pattern in ('*/events.jsonl','*/*/events.jsonl'):
        for path in sorted(Path('workspace').glob(pattern)):
            if {'private','explorer'}.intersection(path.parts):continue
            events=read_events(path); prior[str(path.resolve())]=sha256(path.read_bytes()); inspect(events)
            if events[0]['kind']=='campaign_created':
                protocol,_,_=campaign_documents(events); previous_seeds.update(n.seed for n in protocol.nodes())
    require(not allocated.intersection(previous_seeds),'Previously allocated seed reused')
    verification=HTTPBackend().verify(local_model(plan))
    # Empirical 18-message extrapolation from each of the four completed Haiku roots.
    from behaviorlab.paid_framing import replay as paid_replay
    calibration=Path('workspace/cheap-framing-20260916-0927/events.jsonl'); old=paid_replay(read_events(calibration)); estimates=[]
    for root in old['plan']['roots']:
        if old['plan']['candidates'][root['candidate']]['label']!='haiku':continue
        rows=[old['results'][root['id']+':'+str(t)] for t in range(1,13)]
        inputs=[r['usage']['prompt_tokens'] for r in rows]; outputs=[r['usage']['completion_tokens'] for r in rows]
        future_inputs=6*Decimal(inputs[-1])+Decimal(inputs[-1]-inputs[0])/11*21
        future_outputs=6*Decimal(sum(outputs))/12
        estimates.append(sum(Decimal(r['cost_usd']) for r in rows)+(future_inputs+5*future_outputs)/1000000)
    forecast={'expected_cloud_usd':str(2*sum(estimates)/len(estimates)),
        'calibration_sha256':sha256(calibration.read_bytes()),'method':'Two equivalent 18-message Haiku roots = 36 hosted calls. Extend measured 12-message input growth and mean output; average four roots. Mixed Gemma histories and the new prompt can change this estimate.',
        'ceiling_usd':'1.00','local_token_charge_usd':'0','hardware_energy_cost':'not estimated'}
    plan['metadata']['forecast']=forecast
    files=[p for p in Path('behaviorlab').glob('*.py') if 'explorer' not in p.name]+[Path(__file__),Path('design/ollama-context-models.json')]
    code={str(p.resolve()):sha256(p.read_bytes()) for p in files}
    frozen=d/'frozen-source'; frozen.mkdir()
    for p in files:(frozen/p.name).write_bytes(p.read_bytes())
    payload={'plan':plan,'plan_sha256':fingerprint(plan),'code_hashes':code,'synthetic':False,
        'verification':verification,'seed_audit':{'allocated':sorted(allocated),'prior_distinct_seeds':len(previous_seeds),'collisions':[]},'prior_evidence_hashes':prior}
    with Journal(d,create=True) as j:j.append('mixed_dialogue_created',payload)
    (d/'frozen-plan.json').write_text(canonical(payload)+'\n')
    print(canonical({'directory':str(d),'plan_sha256':fingerprint(plan),'max_calls':72,'local_calls':36,'cloud_calls':36,'additional_live_technical_calls':0,'forecast':forecast}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['prepare','run','report']); p.add_argument('directory',type=Path); a=p.parse_args()
    if a.action=='prepare':prepare(a.directory)
    else:
        # Report and closed resume require neither credentials nor network access.
        state=replay(read_events(a.directory/'events.jsonl'))
        if a.action=='run' and not state['finished']:state=execute(a.directory,credential('workspace/private/webui-token'))
        print(canonical(summary(state)),flush=True)
