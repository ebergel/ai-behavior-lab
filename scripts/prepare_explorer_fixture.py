"""Create explicitly synthetic evidence in a NEW workspace for UI verification."""
import argparse
from pathlib import Path
from behaviorlab.common import canonical, read_json
from behaviorlab.legacy import import_corpus
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import create_campaign, execute
from scripts.check_trajectory_outcomes import ScenarioBackend


def prepare(destination):
    destination.mkdir(parents=True,exist_ok=False)
    origin=destination/'fixture-source'/'data'/'runs'; origin.mkdir(parents=True)
    rows=[{'kind':'header','cond':'UI','cond_name':'synthetic UI example','pair_model':'SYNTHETIC demo model','run':1,
        'turns':6,'temperature':0.8,'num_predict':400,'num_ctx':12288,'system':'Synthetic UI verification only. No model inference.',
        'model_kind':'synthetic fixture','started':'2026-09-15 00:00:00'},
        {'kind':'message','turn':1,'speaker':'X','content':'Understanding begins with a question. A mirror offers another view. 🙂 café <script>alert(1)</script>','done_reason':'stop'},
        {'kind':'message','turn':2,'speaker':'Y','content':'This is a synthetic reply for testing search, selection and notes.','done_reason':'stop'},
        {'kind':'third','after_turn':2,'content':'A synthetic outside intervention.','topic':None},
        {'kind':'message','turn':3,'speaker':'X','content':'The meaning of a sentence depends on its context.','thinking':'Synthetic recorded reasoning.','done_reason':'stop'},
        {'kind':'message','turn':4,'speaker':'Y','content':'An intentionally capped fixture','done_reason':'length'},
        {'kind':'message','turn':5,'speaker':'X','content':'This historical continuation follows a cap.','done_reason':'stop'},
        {'kind':'message','turn':6,'speaker':'Y','content':'The end of the UI fixture.','done_reason':'stop'},
        {'kind':'footer','pair_turns':6}]
    (origin/'UI_run01.jsonl').write_text('\n'.join(canonical(r) for r in rows)+'\n')
    import_corpus(destination/'fixture-source',destination/'reference-fixture','synthetic-ui-fixture','fixture-only')
    registry=Registry.load('design/models.json'); data=read_json(Path('examples/outcomes-factorial.fake.json').read_text())
    data['roots']=[r for r in data['roots'] if r['id'] in ('AA-r01','AA-r02')]
    protocol=Protocol.from_dict(data,registry); campaign=destination/'branch-fixture'
    create_campaign(campaign,protocol,registry); backend=ScenarioBackend(protocol.seed_base); execute(campaign,backend=backend)
    (destination/'fixture.json').write_text(canonical({'purpose':'Synthetic UI testing only','real_model_calls':0,'main_fixture_calls':backend.calls})+'\n')
    print(destination)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('workspace');args=p.parse_args();prepare(Path(args.workspace))
