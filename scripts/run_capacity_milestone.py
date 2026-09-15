"""Run an immutable, finite capacity freeze. No replacement attempts or semantic gates."""
import argparse
import fcntl
from pathlib import Path

from behaviorlab.annotations import save_new
from behaviorlab.backends import HTTPBackend, json_request
from behaviorlab.capacity import execute_capacity, seed_entries, reconstruct
from behaviorlab.common import canonical, read_json, require, sha256, timestamp
from behaviorlab.evidence import completed_campaign
from behaviorlab.journal import read_events
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import create_campaign, execute, summarize
from behaviorlab.seeds import protocol_entries, require_clean


def run(base):
    frozen = read_json((base/'freeze.json').read_text())
    require(frozen['schema'] == 'behaviorlab.capacity-freeze/1', 'Unknown capacity freeze')
    for path, digest in frozen['file_sha256'].items():
        require(sha256(Path(path).read_bytes()) == digest, 'Frozen file changed: '+path)
    plan = read_json((base/'snapshot-plan.json').read_text())
    entries = seed_entries(plan); loaded = []
    for job in frozen['jobs']:
        registry = Registry.load(job['registry']); protocol = Protocol.load(job['protocol'], registry)
        require(read_json(protocol.document_json)['schema'] == 'behaviorlab.protocol/2', 'Capacity jobs are engineering')
        require(len(protocol.nodes()) == job['max_calls'], 'Capacity graph/budget mismatch')
        entries += protocol_entries(job['name'], protocol, registry)
        loaded.append((job, protocol, registry))
    require(frozen['maximum_generation_calls'] == len(entries), 'Aggregate capacity budget mismatch')
    require(require_clean(entries, frozen['previous_seed_entries']) == frozen['seed_audit'], 'Seed audit changed')
    for path, source in plan['sources'].items():
        require(completed_campaign(path).identity == source['identity'], 'Capacity source changed')
    if not (base/'initial-models.json').exists():
        save_new(base/'initial-models.json', {'at': timestamp(), 'models': json_request('http://127.0.0.1:11434', '/api/ps')})
    backend = HTTPBackend(request_timeout=300)
    path = base/'snapshots'
    used = len(reconstruct(read_events(path/'events.jsonl'))[2]) if path.exists() else 0
    result = execute_capacity(path, plan, len(plan['jobs'])-used, backend)
    print(canonical({'job': 'snapshots', 'result': result}), flush=True)
    for job, protocol, registry in loaded:
        path = base/job['name']
        if job['requires']:
            prerequisite = completed_campaign(base/job['requires'])
            if len(prerequisite.turns) != len(prerequisite.nodes):
                print(canonical({'job': job['name'], 'skipped': 'invalid smoke prerequisite'}), flush=True)
                continue
        if not path.exists(): create_campaign(path, protocol, registry)
        summary = summarize(path)
        require((summary['protocol_sha256'], summary['registry_sha256']) == (protocol.digest, registry.digest), 'Wrong campaign')
        events = read_events(path/'events.jsonl')
        require(not any(e['kind'] == 'attempt_retry_authorized' for e in events), 'Capacity freeze prohibits retry')
        used = sum(e['kind'] == 'request_saved' for e in events)
        require(used <= job['max_calls'], 'Capacity budget exhausted')
        def progress(event, node):
            if event == 'after_commit' and node.turn % 5 == 0:
                print(canonical({'at': timestamp(), 'job': job['name'], 'node': node.id}), flush=True)
        result = execute(path, backend=backend, max_calls=job['max_calls']-used, hook=progress)
        print(canonical({'job': job['name'], 'result': result}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('directory'); args = p.parse_args()
    base = Path(args.directory)
    with (base/'driver.lock').open('a+b') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(base)
