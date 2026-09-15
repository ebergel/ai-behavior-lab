"""Offline audit of annotation packets, probe isolation, and recovery evidence."""
import argparse
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from behaviorlab.annotations import annotation_report, load_packet, mechanical_report
from behaviorlab.common import canonical, fingerprint, read_json, require, sha256, timestamp
from behaviorlab.evidence import completed_campaign
from behaviorlab.history import ancestry
from behaviorlab.journal import read_events
from behaviorlab.probes import execute_probes, probe_report, reconstruct
from scripts.summarize_mtplx_qualification import OfflineBackend


def verify_packet(folder, source):
    packet,key=load_packet(folder)
    require(key['source']==source.identity, 'Packet source identity changed')
    def opaque(value): return fingerprint({'salt':key['id_salt'],'value':value})[:24]
    count=0; seen=set()
    for w in packet['windows']:
        mapping=key['windows'][w['id']]
        first=source.turns[mapping['targets'][w['messages'][0]['id']]]
        context=ancestry(first.parent_id,source.turns)
        require([(m['id'],m['text']) for m in w['context']]==[(opaque(t.node_id),t.content) for t in context],
                'Review context differs from source')
        for m in w['messages']:
            t=source.turns[mapping['targets'][m['id']]]
            require(m['text']==t.content and m['id']==opaque(t.node_id) and t.node_id not in seen,
                    'Review target changed or duplicated')
            seen.add(t.node_id);count+=1
    require(read_json((folder/'mechanics.json').read_text())==mechanical_report(source), 'Mechanical report changed')
    status=annotation_report(folder)
    require(not status['active_raters'], 'Engineering packet unexpectedly contains semantic ratings')
    return {'packet_sha256':key['packet_sha256'],'windows':len(packet['windows']),
            'unique_targets':count,'source_text_verified':True,'semantic_ratings':0}


def audit_batch(folder, source):
    raw=(folder/'events.jsonl').read_bytes()
    meta,_,_,requests,responses,results,complete=reconstruct(read_events(folder/'events.jsonl'))
    require(meta['plan']['source']==source.identity and complete, 'Probe source changed or batch incomplete')
    for snapshot in meta['plan']['snapshots']:
        expected=[dict(asdict(t),thinking=None) for t in ancestry(snapshot['node'],source.turns)]
        require(snapshot['history']==expected, 'Probe snapshot differs from main ancestry')
    report=probe_report(folder); details=[]
    for job in report['jobs']:
        response=responses[job['id']]; saved=requests[job['id']]
        row={'job':job['id'],'request_sha256':saved['request_sha256'],
             'response_sha256':sha256(response['raw_response'].encode())}
        if 'transport' in response:
            d=read_json(response['raw_response']);e=saved['preflight']
            row.update(input_tokens=e['input_tokens'],reported_input_tokens=d['prompt_eval_count'],
                output_tokens=d['eval_count'],context_headroom=e['context_headroom'],
                cached_tokens=d['prompt_eval_cached_count'],http_seconds=response['transport']['elapsed_seconds'],
                started_at=response['transport']['started_at'],finished_at=response['transport']['finished_at'])
        details.append(row)
    require((folder/'events.jsonl').read_bytes()==raw, 'Audit changed probe journal')
    return {'report':report,'calls':details,'journal_sha256':sha256(raw),'journal_bytes':len(raw),
            'snapshots_verified_against_source':True}


def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--source',required=True);p.add_argument('--synthetic-source',required=True)
    args=p.parse_args();base=Path(args.directory)
    source=completed_campaign(args.source); synthetic=completed_campaign(args.synthetic_source)
    packet=verify_packet(base/'review',source);fake_packet=verify_packet(base/'factorial-review',synthetic)
    main=audit_batch(base/'probes',source);fake=audit_batch(base/'factorial-probes',synthetic)
    require(packet['unique_targets']==18 and fake_packet['unique_targets']==840
            and main['report']['requests']==16 and fake['report']['requests']==400,'Unexpected qualification counts')
    for recipient in ('X','Y'):
        variants=Counter(j['variant'] for j in fake['report']['jobs'] if j['recipient']==recipient and j['item']=='source')
        require(variants=={0:25,1:25,2:25,3:25},'Source variants unbalanced')
    before=(base/'probes/events.jsonl').read_bytes()
    execute_probes(base/'probes',0,backend=OfflineBackend())
    require((base/'probes/events.jsonl').read_bytes()==before,'Completed live replay changed evidence')
    checkpoint=read_json((base/'probe-recovery-checkpoint.json').read_text())
    recovery=read_json((base/'probe-recovery-result.json').read_text())
    require(sha256(before[:checkpoint['journal_prefix_bytes']])==checkpoint['journal_prefix_sha256']
            and checkpoint['requests']==checkpoint['responses']==8 and checkpoint['results']==7
            and recovery['new_generation_calls']==8 and recovery['saved_response_reused']
            and recovery['source_unchanged'],'Recovery prefix/count mismatch')
    inspection=read_json((base/'codex-probe-inspection.json').read_text())
    require(inspection['plan_sha256']==main['report']['plan_sha256'] and inspection['automatic_scores_unchanged'],
            'Inspection associated with wrong batch')
    by_job={j['id']:j for j in main['report']['jobs']}; call={c['job']:c for c in main['calls']}
    for row in inspection['reviewed_answers']:
        require(row['quote']==by_job[row['job']]['result']['content']
                and row['response_sha256']==call[row['job']]['response_sha256'], 'Inspection quote changed')
    summary={'schema':'behaviorlab.annotation-probes-validation/1','created_at':timestamp(),
        'data_class':'engineering_validation_not_semantic_findings','main_source':source.identity,
        'review_packet':packet,'live_probes':main,'recovery_checkpoint':checkpoint,'recovery':recovery,
        'content_inspection':inspection,'synthetic':{'source':synthetic.identity,'review_packet':fake_packet,
            'probes_planned':400,'probes_completed':fake['report']['scored'],'journal_sha256':fake['journal_sha256'],
            'variant_counts_per_recipient':[25,25,25,25]},
        'total_real_generation_calls':16,'total_fake_generation_calls':400,
        'live_completed_replay_preserved_journal':True,
        'webui':read_json((base/'probes-webui.receipt.json').read_text()),
        'limits':['No human semantic annotations or validated semantic scorer.',
            'Live probes used full-history snapshots at turns 30 and 50; recent-history probe construction was tested synthetically.',
            'Strict JSON formatting and factual answer content are separate records; Codex inspection is not independent human adjudication.',
            'Simple task performance on one engineering conversation does not establish general competence, a nonduality effect, or subjective experience.',
            'Native caching remains enabled. Recipient preflight/count agreement is not generation-token capture or per-call final sampler telemetry.']}
    print(canonical(summary))


if __name__=='__main__': main()
