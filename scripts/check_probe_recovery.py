"""Bounded 16-call local probe check with recovery after saved response eight."""
import argparse
from pathlib import Path

from behaviorlab.annotations import save_new
from behaviorlab.backends import HTTPBackend
from behaviorlab.common import read_json, require, sha256, timestamp
from behaviorlab.journal import read_events
from behaviorlab.probes import execute_probes, reconstruct


class PlannedInterruption(BaseException):
    pass


def main():
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=('first','resume'))
    p.add_argument('directory'); p.add_argument('--source', required=True)
    args = p.parse_args(); folder = Path(args.directory); journal = folder/'events.jsonl'
    source = Path(args.source)/'events.jsonl'; source_before = source.read_bytes()
    meta, _, _, requests, responses, results, _ = reconstruct(read_events(journal))
    require(len(meta['plan']['jobs']) == 16 and sha256(source_before) == meta['plan']['source']['journal_sha256'],
            'Wrong probe budget or changed source journal')
    checkpoint = folder.parent/'probe-recovery-checkpoint.json'
    if args.phase == 'first':
        require(not requests, 'First phase requires an unstarted batch')
        eighth = meta['plan']['jobs'][7]['id']
        def hook(stage, identity):
            if stage == 'after_result': print('Saved result', identity, flush=True)
            if stage == 'after_response' and identity == eighth: raise PlannedInterruption()
        try:
            execute_probes(folder, 8, HTTPBackend(request_timeout=300), hook)
        except PlannedInterruption:
            _,_,_,q,a,r,_ = reconstruct(read_events(journal))
            require(len(q)==len(a)==8 and len(r)==7, 'Unexpected probe checkpoint state')
            require(source.read_bytes()==source_before, 'Probe execution modified source journal')
            raw=journal.read_bytes()
            save_new(checkpoint, {'at':timestamp(), 'journal_prefix_bytes':len(raw),
                'journal_prefix_sha256':sha256(raw), 'saved_job':eighth,
                'response_sha256':sha256(a[eighth]['raw_response'].encode()),
                'requests':8,'responses':8,'results':7, 'source_sha256':sha256(source_before)})
        else: raise RuntimeError('Expected a deliberate save/score interruption')
    else:
        before=read_json(checkpoint.read_text()); prefix=journal.read_bytes()
        require(len(prefix)==before['journal_prefix_bytes'] and sha256(prefix)==before['journal_prefix_sha256'],
                'Probe evidence changed before resume')
        result=execute_probes(folder,8,HTTPBackend(request_timeout=300))
        _,_,_,q,a,_,_=reconstruct(read_events(journal))
        require(result['complete'] and len(q)==len(a)==16 and journal.read_bytes().startswith(prefix)
                and sha256(a[before['saved_job']]['raw_response'].encode())==before['response_sha256']
                and source.read_bytes()==source_before, 'Probe recovery or source isolation failed')
        save_new(folder.parent/'probe-recovery-result.json', {'at':timestamp(), 'new_generation_calls':8,
            'total_generation_calls':16, 'saved_response_reused':True, 'journal_prefix_preserved':True,
            'source_unchanged':True, 'result':result})


if __name__ == '__main__': main()
