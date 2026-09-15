"""Full-size SYNTHETIC stress trial of repetition, caps, branches and probe availability."""
import argparse
from pathlib import Path

from behaviorlab.annotations import create_packet, save_new
from behaviorlab.common import canonical, read_json, require, sha256
from behaviorlab.evidence import completed_campaign
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.probes import create_batch, execute_probes
from behaviorlab.runner import FakeBackend, create_campaign, execute
from behaviorlab.seeds import protocol_entries, require_clean
from behaviorlab.trajectory_outcomes import RULES, report


class ScenarioBackend(FakeBackend):
    """Pure function of synthetic seed/history; never calls a model or network."""
    def __init__(self, seed_base):
        super().__init__(); self.seed_base=seed_base

    def generate(self, payload):
        self.calls += 1
        offset=payload['options']['seed']-self.seed_base
        root=(offset % 1000000)//10000; turn=(offset % 1000)//10
        require(1 <= root <= 5 and 1 <= turn <= 50, 'Unexpected synthetic seed coordinate')
        history=payload['messages']; recent=len(history)<=4 and turn>=31
        had_r=any('[SYNTHETIC] R-state' in m['content'] for m in history)
        if turn<=30: segment='prefix'
        elif turn<=40: segment='R' if recent else 'F'
        else: segment=('R' if had_r else 'F')+('R' if recent else 'F')
        capped=((root==2 and turn==28) or (root==3 and segment=='F' and turn==37)
                or (root==4 and segment=='FR' and turn==44) or (root==5 and segment=='R' and turn==40))
        if capped:
            content='[SYNTHETIC CAP FIXTURE]\n'+'Echo.\n'*12+'Ec'
        elif turn<25:
            content='[SYNTHETIC] ordinary message '+str(turn)
        elif segment in ('prefix','F','FF','RF'):
            content='[SYNTHETIC] Done.'
        elif segment=='R' and turn<33:
            content='[SYNTHETIC] R-state transition '+str(turn)
        elif segment in ('R','RR'):
            content='[SYNTHETIC] R-state.'
        else:
            content='[SYNTHETIC] FR departure '+str(turn)
        return canonical({'model':payload['model'],'fixture':True,'done':True,
            'done_reason':'length' if capped else 'stop','message':{'role':'assistant','content':content}})


def run(base):
    registry=Registry.load('design/models.json')
    protocol=Protocol.load('examples/outcomes-factorial.fake.json',registry)
    base.mkdir(parents=True,exist_ok=False)
    allocation=protocol_entries('synthetic',protocol,registry,paired_branches=True)
    save_new(base/'freeze.json',{'data_class':'synthetic_engineering_only','rules':RULES,
        'protocol_sha256':protocol.digest,'registry_sha256':registry.digest,
        'seed_audit':require_clean(allocation),'maximum_main_calls':1800,'maximum_probe_calls':400,
        'expected':{'valid':1340,'caps':16,'blocked':444,'available_annotation_targets':544,
                    'available_probe_snapshots':60,'available_probe_calls':240},
        'scenario':{'root_1':'all branches valid','root_2':'prefix cap at 28','root_3':'F cap at 37',
                    'root_4':'FR cap at 44','root_5':'R cap at 40'},
        'fixture_source_sha256':sha256(Path(__file__).read_bytes())})
    campaign=base/'campaign'; create_campaign(campaign,protocol,registry)
    first=ScenarioBackend(protocol.seed_base)
    execute(campaign,backend=first,max_calls=317)
    second=ScenarioBackend(protocol.seed_base); execute(campaign,backend=second)
    source=completed_campaign(campaign); result=report(source)
    require(result['summary']['availability']=={'valid':1340,'observed_output_cap':16,'unavailable_descendant':444}, 'Synthetic outcome counts differ')
    for pairing in result['pairings']:
        require(pairing['all_four_terminal_endpoints_valid_roots']==1, 'Selected-subset denominator differs')
        require([(c['valid_parent_roots'],c['both_endpoints_valid_roots']) for c in pairing['contrast_denominators']]
                ==[(4,2),(3,2),(3,3)], 'Branch contrast denominators differ')
    save_new(base/'trajectory-report.json',result)
    packet=create_packet(campaign,base/'review',seed=9151301)
    require(packet['targets']==544 and packet['unavailable_targets']==296,'Synthetic annotation availability differs')
    probes=create_batch(campaign,base/'probes',seed_base=515000000)
    require(probes['planned_calls']==240 and len(probes['unavailable_snapshots'])==40,'Synthetic probe availability differs')
    # The ordinary fake backend produces fixture text, so strict-JSON scores must
    # be review-required. This tests availability/durability, not task competence.
    probe_backend=FakeBackend(); probe_result=execute_probes(base/'probes',240,backend=probe_backend)
    require(all(j['result']['status']=='needs_manual_review' for j in probe_result['jobs']),'Unexpected fake probe score')
    before={str(p):p.read_bytes() for p in base.glob('*/events.jsonl')}
    replay=ScenarioBackend(protocol.seed_base); execute(campaign,backend=replay,max_calls=0)
    probe_replay=FakeBackend(); execute_probes(base/'probes',0,backend=probe_replay)
    require(replay.calls==probe_replay.calls==0 and all(Path(p).read_bytes()==raw for p,raw in before.items()),'Synthetic replay changed evidence')
    require(sha256((campaign/'events.jsonl').read_bytes())==source.identity['journal_sha256'], 'Derived work changed main source')
    validation={'schema':'behaviorlab.trajectory-stress-validation/1','data_class':'synthetic_engineering_only',
        'main_fixture_calls':first.calls+second.calls,'probe_fixture_calls':probe_backend.calls,'real_model_calls':0,
        'summary':result['summary'],'pairings':result['pairings'],'annotation_packet':packet,'probe_plan':probes,
        'replay_calls':0,'journal_bytes_unchanged':True,'probe_scores':'All require review because outputs are generic fixture text.'}
    save_new(base/'validation.json',validation)
    print(canonical(validation))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();run(Path(a.directory))
