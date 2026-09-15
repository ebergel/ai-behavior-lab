"""Disposable output-cap diagnostics on immutable saved request contexts.

Each case is an independently dispatched request. Results never enter a source
conversation. Raw replies are journaled before parsing; unknown calls cannot retry.
"""
from copy import deepcopy
from pathlib import Path

from .backends import HTTPBackend, LIVE_BACKEND, LIVE_PARSER, parse_live
from .common import fingerprint, read_json, require
from .evidence import completed_campaign
from .journal import Journal, read_events
from .protocol import Registry
from .runner import NeedsAttention
from .seeds import model_key


def create_plan(cases, output_caps, seeds):
    require(len(cases) == len(seeds), 'Each source case needs a seed')
    sources, jobs = {}, []
    for index, (directory, node_id) in enumerate(cases):
        source = completed_campaign(directory)
        node = next(n for n in source.nodes if n.id == node_id)
        kind, result = source.state.outcomes[node_id]
        require(kind == 'turn_invalid' and result['reason'] == 'output_cap', 'Capacity case must be a recorded cap')
        saved = source.state.requests[source.state.attempts[node_id]]
        identity = str(Path(directory).resolve())
        sources[identity] = {'identity': source.identity, 'registry': read_json(source.registry.document_json)}
        original = saved['request']
        for cap in (original['options']['num_predict'], output_caps[index]):
            payload = deepcopy(original)
            payload['options'].update(num_predict=cap, seed=seeds[index])
            jobs.append({'id': 'case-'+str(index+1)+'-cap-'+str(cap), 'source': identity,
                'source_node': node_id, 'model': node.model, 'original_request': original,
                'request': payload, 'matched_group': 'capacity-case-'+str(index+1)})
    plan = {'schema': 'behaviorlab.capacity-plan/1', 'data_class': 'local_engineering_capacity_diagnostic',
            'parser_version': LIVE_PARSER, 'sources': sources, 'jobs': jobs,
            'policy': 'Only cap and seed change. Paired caps use a declared shared seed; no retries, continuations, semantic gates or source edits.'}
    validate_plan(plan)
    return plan


def validate_plan(plan):
    require(plan['schema'] == 'behaviorlab.capacity-plan/1'
            and plan['data_class'] == 'local_engineering_capacity_diagnostic'
            and plan['parser_version'] == LIVE_PARSER, 'Unsupported capacity plan')
    require(plan['jobs'] and len({j['id'] for j in plan['jobs']}) == len(plan['jobs']), 'Duplicate/empty capacity jobs')
    registries = {key: Registry.from_dict(s['registry']) for key, s in plan['sources'].items()}
    for job in plan['jobs']:
        model = registries[job['source']].model(job['model'])
        row = read_json(model.metadata_json)
        require(row['backend'] == 'ollama' and row['location'] == 'local'
                and model.tag == job['request']['model'], 'Capacity diagnostic requires pinned local Ollama')
        expected = deepcopy(job['original_request'])
        options = job['request']['options']
        require(type(options['num_predict']) is int and 0 < options['num_predict'] <= options['num_ctx']
                and type(options['seed']) is int and 0 <= options['seed'] < 2**31, 'Invalid capacity cap/seed')
        expected['options'].update(num_predict=options['num_predict'], seed=options['seed'])
        require(expected == job['request'], 'Capacity request changed beyond cap and seed')
    return registries


def seed_entries(plan):
    registries = validate_plan(plan)
    return [{'id': 'snapshots/'+j['id'], 'model': model_key(registries[j['source']].model(j['model'])),
             'seed': j['request']['options']['seed'], 'matched_group': j['matched_group']} for j in plan['jobs']]


def result_for(response, job, model, parser):
    parsed = parse_live(response['raw_response'], job['request'], model, response['transport'], parser)
    data = read_json(response['raw_response'])
    return {'invalid_reason': parsed['invalid_reason'], 'visible_words': len(parsed['content'].split()),
            'generated_tokens': data['eval_count'], 'input_tokens': data['prompt_eval_count'],
            'content_sha256': fingerprint(parsed['content']), 'finish_reason': data['done_reason']}


def reconstruct(events):
    require(events and events[0]['kind'] == 'capacity_created', 'Not a capacity journal')
    header = events[0]['payload']; plan = header['plan']
    require(header['plan_sha256'] == fingerprint(plan), 'Capacity plan changed')
    registries = validate_plan(plan); jobs = {j['id']: j for j in plan['jobs']}
    requests, responses, results, errors = {}, {}, {}, set()
    for event in events[1:]:
        p = event['payload']; identity = p['job']; require(identity in jobs, 'Unknown capacity job')
        job = jobs[identity]; model = registries[job['source']].model(job['model'])
        if event['kind'] == 'capacity_request_saved':
            require(identity not in requests and p['request'] == job['request']
                    and p['model_digest'] == model.digest, 'Changed/repeated capacity request')
            requests[identity] = p
        elif event['kind'] == 'capacity_response_saved':
            require(identity in requests and identity not in responses and identity not in errors,
                    'Duplicate or unrequested capacity response')
            require(p['transport']['ollama_context'] == requests[identity]['preflight'], 'Capacity preflight mismatch')
            responses[identity] = p
        elif event['kind'] == 'capacity_result_saved':
            require(identity in responses and identity not in results and
                    p['result'] == result_for(responses[identity], job, model, plan['parser_version']),
                    'Capacity result differs from response')
            results[identity] = p['result']
        elif event['kind'] == 'capacity_error':
            require(identity in requests and identity not in responses and identity not in errors, 'Invalid capacity error')
            errors.add(identity)
        else:
            raise ValueError('Unknown capacity event')
    return plan, registries, requests, responses, results


def execute_capacity(directory, plan, max_calls, backend=None, hook=None):
    require(type(max_calls) is int and max_calls >= 0, 'Explicit capacity call budget required')
    validate_plan(plan)
    folder = Path(directory)
    if not folder.exists():
        folder.mkdir(parents=True)
        with Journal(folder, create=True) as journal:
            journal.append('capacity_created', {'plan': plan, 'plan_sha256': fingerprint(plan)})
    backend = backend or HTTPBackend(request_timeout=300)
    require(backend.identity == LIVE_BACKEND, 'Wrong capacity backend')
    with Journal(folder) as journal:
        saved, registries, requests, responses, results = reconstruct(journal.events)
        require(saved == plan, 'Capacity plan differs from journal')
        calls = 0
        for job in plan['jobs']:
            identity = job['id']; model = registries[job['source']].model(job['model'])
            if identity in results:
                continue
            if identity in requests and identity not in responses:
                raise NeedsAttention('Unresolved capacity request '+identity+'; no automatic retry')
            if identity not in requests:
                if calls >= max_calls:
                    break
                observation = backend.verify(model)
                preflight = backend.preflight(job['request'], model)
                journal.append('capacity_request_saved', {'job': identity, 'request': job['request'],
                    'model_digest': model.digest, 'observation': observation, 'preflight': preflight})
                if hook: hook('after_request', job)
                try:
                    response = backend.generate(job['request'], model)
                except Exception as exc:
                    journal.append('capacity_error', {'job': identity, 'error_type': type(exc).__name__})
                    raise NeedsAttention('Capacity transport outcome unknown for '+identity) from exc
                calls += 1
                p = {'job': identity, 'raw_response': response.raw, 'transport': response.evidence}
                journal.append('capacity_response_saved', p); responses[identity] = p
                if hook: hook('after_response', job)
            result = result_for(responses[identity], job, model, plan['parser_version'])
            journal.append('capacity_result_saved', {'job': identity, 'result': result})
            results[identity] = result
        return {'planned': len(plan['jobs']), 'results': results, 'new_calls': calls,
                'complete': len(results) == len(plan['jobs'])}
