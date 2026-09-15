"""Execute only jobs and budgets in a previously written qualification freeze.

No retries, adaptive replacement roots, cloud routes, or factorial execution.
Use PYTHONPATH=. python3 scripts/run_prompt_qualification.py DIRECTORY.
"""
import argparse
from pathlib import Path

from behaviorlab.annotations import save_new
from behaviorlab.backends import HTTPBackend, http_request
from behaviorlab.common import canonical, read_json, require, sha256, timestamp
from behaviorlab.evidence import completed_campaign
from behaviorlab.journal import read_events
from behaviorlab.protocol import Protocol, Registry
from behaviorlab.runner import create_campaign, execute, summarize
from behaviorlab.seeds import protocol_entries, require_clean


def main():
    p = argparse.ArgumentParser(); p.add_argument('directory'); args = p.parse_args()
    base = Path(args.directory); frozen = read_json((base/'freeze.json').read_text())
    require(frozen['schema'] == 'behaviorlab.qualification-freeze/1', 'Unknown freeze')
    require(sum(j['max_calls'] for j in frozen['jobs']) == frozen['maximum_generation_calls'], 'Budget mismatch')
    for path, digest in frozen['file_sha256'].items():
        require(sha256(Path(path).read_bytes()) == digest, 'Frozen input changed: '+path)
    # Completed historical campaigns remain replayable. Any new generation must
    # pass the aggregate allocation check, including jobs not yet reached.
    if any(not (base/j['name']).exists() or not summarize(base/j['name'])['complete'] for j in frozen['jobs']):
        allocation = []
        for job in frozen['jobs']:
            registry = Registry.load(job['registry']); protocol = Protocol.load(job['protocol'], registry)
            allocation += protocol_entries(job['name'], protocol, registry)
        require_clean(allocation)
    if not (base/'initial-models.json').exists():
        response = http_request('http://127.0.0.1:11434', '/api/ps')
        save_new(base/'initial-models.json', {'at': timestamp(), 'response': read_json(response.raw)})
    backend = HTTPBackend(request_timeout=300)
    for job in frozen['jobs']:
        directory = base/job['name']
        if job['requires']:
            prerequisite = completed_campaign(base/job['requires'])
            if len(prerequisite.turns) != len(prerequisite.nodes):
                print(canonical({'job': job['name'], 'skipped': 'engineering prerequisite invalid'}), flush=True)
                continue
        registry = Registry.load(job['registry']); protocol = Protocol.load(job['protocol'], registry)
        require(read_json(protocol.document_json)['execution_class'] in ('engineering_local', 'qualification_local'), 'Wrong class')
        require(len(protocol.nodes()) == job['max_calls'], 'Frozen graph/budget differs')
        if not directory.exists():
            create_campaign(directory, protocol, registry)
        else:
            summary = summarize(directory)
            require(summary['protocol_sha256'] == protocol.digest and summary['registry_sha256'] == registry.digest,
                    'Campaign differs from freeze')
        # A saved request already consumes its budget, including unknown outcomes.
        used = sum(e['kind'] == 'request_saved' for e in read_events(directory/'events.jsonl'))
        print(canonical({'job': job['name'], 'at': timestamp(), 'already_attempted': used}), flush=True)
        result = execute(directory, backend=backend, max_calls=job['max_calls']-used)
        print(canonical({'job': job['name'], 'result': result}), flush=True)


if __name__ == '__main__':
    main()
