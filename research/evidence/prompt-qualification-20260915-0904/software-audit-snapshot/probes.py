"""Independent, durable probe batches derived from immutable main snapshots."""
from dataclasses import asdict
from pathlib import Path
import time
import uuid

from .backends import HTTPBackend, LIVE_BACKEND, LIVE_PARSER, LIVE_PARSERS, parse_live, prepare_request
from .common import canonical, fingerprint, read_json, require
from .evidence import completed_campaign
from .history import Turn, ancestry, messages
from .journal import Journal, read_events
from .protocol import Protocol, Registry
from .runner import FakeBackend, NeedsAttention, PARSER_VERSION, parse_response

DELIMITER = '\n\n[Researcher probe — separate from the conversation]\n'
SPEC = {
    'schema': 'behaviorlab.probe-spec/1', 'delimiter': DELIMITER, 'scorer': 'strict-json/1',
    'pens': 'A drawer contains three red pens and two blue pens. One red pen is removed. How many pens remain, and how many are blue?\nRespond only with a JSON object whose keys are "total" and "blue", each with an integer value.',
    'source': 'In this separate, hypothetical exchange:\n{first}: The marker is {color}.\n{second}: I agree.\nWho first supplied the color, and what was it?\nRespond only with a JSON object whose keys are "speaker" and "color", each with a string value.',
    'source_variants': [{'first': 'X', 'color': 'amber'}, {'first': 'Y', 'color': 'violet'},
                        {'first': 'X', 'color': 'violet'}, {'first': 'Y', 'color': 'amber'}],
    'baseline_rule': 'Same model, system, probe, settings and seed, with no participant history or opening cue.',
    'append_rule': 'Merge delimiter and question into the last user message when present; otherwise append one user message.',
}


def question(job, spec):
    if job['item'] == 'pens':
        return spec['pens'], {'total': 4, 'blue': 2}
    v = spec['source_variants'][job['variant']]
    return spec['source'].format(first=v['first'], second='Y' if v['first']=='X' else 'X', color=v['color']), {'speaker': v['first'], 'color': v['color']}


def validate_plan(plan):
    require(set(plan) == {'schema', 'source', 'source_protocol', 'registry', 'snapshots', 'jobs', 'unavailable_snapshots', 'spec', 'seed_base', 'include_baselines'}
            and plan['schema'] == 'behaviorlab.probe-plan/1' and plan['spec'] == SPEC, 'Unsupported probe plan/spec')
    registry = Registry.from_dict(plan['registry'])
    protocol = Protocol.from_dict(plan['source_protocol'], registry)
    require(plan['source']['protocol_sha256'] == protocol.digest and plan['source']['registry_sha256'] == registry.digest,
            'Source protocol identity changed')
    require(type(plan['seed_base']) is int and 0 <= plan['seed_base'] < 10**9
            and type(plan['include_baselines']) is bool, 'Invalid probe seed/baseline setting')
    lookup = {n.id: n for n in protocol.nodes()}
    require(len({s['node'] for s in plan['snapshots']}) == len(plan['snapshots']), 'Duplicate probe snapshot')
    for snapshot in plan['snapshots']:
        n = lookup[snapshot['node']]
        hist = [Turn(**t) for t in snapshot['history']]
        require(hist and hist[-1].node_id == n.id and len(hist) == n.turn and snapshot['policy'] == n.history,
                'Incomplete or changed probe snapshot')
        for t in hist:
            actual = lookup[t.node_id]
            require((t.root, t.parent_id, t.number, t.speaker) == (actual.root, actual.parent, actual.turn, actual.speaker)
                    and t.thinking is None, 'Snapshot graph or trace isolation mismatch')
        messages(protocol, hist, 'X', snapshot['policy'])
    require(plan['jobs'] == scheduled_jobs(plan['snapshots'], plan['seed_base'], plan['include_baselines']),
            'Probe schedule, variant balance or seeds changed')
    return protocol, registry


def scheduled_jobs(snapshots, seed_base, baselines):
    jobs = []
    for index, snapshot in enumerate(snapshots):
        for participant, offset in [('X', 0), ('Y', 2)]:
            for item_index, item in enumerate(('pens', 'source')):
                seed = seed_base + index*10 + offset*2 + item_index
                for baseline in ([False, True] if baselines else [False]):
                    jobs.append({'id': 'probe-'+str(len(jobs)+1).zfill(4), 'snapshot': snapshot['node'],
                        'recipient': participant, 'item': item, 'variant': (index+offset)%4 if item == 'source' else None,
                        'seed': seed, 'baseline': baseline})
    return jobs


def create_batch(campaign, directory, snapshot_turns=(30, 50), include_baselines=False, seed_base=15092026):
    source = completed_campaign(campaign)
    require(read_json(source.protocol.document_json)['schema'] in ('behaviorlab.protocol/1', 'behaviorlab.protocol/2'),
            'Qualification probes require a separately budgeted extension; this command supports engineering sources')
    require(snapshot_turns and len(set(snapshot_turns)) == len(snapshot_turns)
            and all(type(n) is int and 1 <= n <= 99 for n in snapshot_turns), 'Invalid snapshot turns')
    snapshots, unavailable = [], []
    for node in source.nodes:
        if node.turn not in snapshot_turns: continue
        if node.id not in source.turns:
            unavailable.append({'node': node.id, 'outcome': source.state.outcomes[node.id][0]}); continue
        snapshots.append({'node': node.id, 'policy': node.history,
            'history': [dict(asdict(t), thinking=None) for t in ancestry(node.id, source.turns)]})
    plan = {'schema': 'behaviorlab.probe-plan/1', 'source': source.identity,
        'source_protocol': read_json(source.protocol.document_json), 'registry': read_json(source.registry.document_json),
        'snapshots': snapshots, 'jobs': scheduled_jobs(snapshots, seed_base, include_baselines),
        'unavailable_snapshots': unavailable, 'spec': SPEC, 'seed_base': seed_base, 'include_baselines': include_baselines}
    validate_plan(plan)
    folder = Path(directory); folder.mkdir(parents=True, exist_ok=False)
    live = source.state.meta['backend'] == LIVE_BACKEND
    with Journal(folder, create=True) as journal:
        journal.append('probe_batch_created', {'plan': plan, 'plan_sha256': fingerprint(plan),
            'backend': LIVE_BACKEND if live else FakeBackend.identity,
            'parser_version': LIVE_PARSER if live else PARSER_VERSION,
            'data_class': 'local_engineering_disposable_probes' if live else 'synthetic_probe_fixture'})
    return {'directory': str(folder.resolve()), 'plan_sha256': fingerprint(plan), 'planned_calls': len(plan['jobs']),
            'unavailable_snapshots': unavailable, 'source_unchanged': True}


def probe_request(plan, job, protocol, registry):
    snapshot = next(s for s in plan['snapshots'] if s['node'] == job['snapshot'])
    history = [Turn(**t) for t in snapshot['history']]
    root = next(r for r in protocol.roots if r.name == history[-1].root)
    model = registry.model(root.x_model if job['recipient'] == 'X' else root.y_model)
    selected = [{'role': 'system', 'content': protocol.system}] if job['baseline'] else messages(protocol, history, job['recipient'], snapshot['policy'])
    prompt, expected = question(job, plan['spec'])
    if selected[-1]['role'] == 'user':
        selected[-1]['content'] += plan['spec']['delimiter']+prompt
    else:
        selected.append({'role': 'user', 'content': plan['spec']['delimiter']+prompt})
    settings = read_json(protocol.settings_json)
    if 'by_model' in settings:
        payload = prepare_request(model, settings['by_model'][model.label], selected, job['seed'])
    else:
        payload = settings; payload.update(model=model.tag, messages=selected); payload['options']['seed'] = job['seed']
    return payload, model, expected


def score_content(content, expected):
    try:
        answer = read_json(content)
    except (ValueError, TypeError):
        return {'status': 'needs_manual_review', 'reason': 'not_strict_json'}
    if not isinstance(answer, dict) or set(answer) != set(expected) or any(type(answer[k]) is not type(v) for k,v in expected.items()):
        return {'status': 'needs_manual_review', 'reason': 'answer_schema_mismatch'}
    normalized = {k: v.strip().casefold() if isinstance(v, str) else v for k,v in answer.items()}
    target = {k: v.casefold() if isinstance(v, str) else v for k,v in expected.items()}
    return {'status': 'correct' if normalized == target else 'incorrect', 'parsed_answer': answer,
            'rule': 'Exact integer values; source strings trimmed and casefolded. No prose extraction.'}


def evaluate(response, payload, model, expected, meta):
    try:
        parsed = parse_live(response['raw_response'], payload, model, response.get('transport'), meta['parser_version']) if meta['backend'] == LIVE_BACKEND else parse_response(response['raw_response'], payload)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        return {'status': 'technical_invalid', 'reason': 'malformed_response', 'detail': str(exc)}
    if parsed['invalid_reason']:
        return {'status': 'technical_invalid', 'reason': parsed['invalid_reason'], 'content': parsed['content']}
    return dict(score_content(parsed['content'], expected), content=parsed['content'], thinking=parsed['thinking'])


def reconstruct(events):
    require(events and events[0]['kind'] == 'probe_batch_created', 'Not a probe journal')
    meta = events[0]['payload']; plan = meta['plan']
    require(meta['plan_sha256'] == fingerprint(plan), 'Probe plan changed')
    protocol, registry = validate_plan(plan)
    live = plan['source_protocol']['schema'] == 'behaviorlab.protocol/2'
    require(meta['backend'] == (LIVE_BACKEND if live else FakeBackend.identity)
            and meta['parser_version'] in (LIVE_PARSERS if live else {PARSER_VERSION})
            and meta['data_class'] == ('local_engineering_disposable_probes' if live else 'synthetic_probe_fixture'),
            'Probe backend/parser/data-class mismatch')
    jobs = {j['id']: j for j in plan['jobs']}
    requests, responses, results, errors = {}, {}, {}, set(); complete = False
    for e in events[1:]:
        p, kind = e['payload'], e['kind']; identity = p.get('job')
        require(not complete, 'Event after probe completion')
        if kind == 'probe_complete':
            require(set(results) == set(jobs), 'Premature probe completion'); complete = True; continue
        if kind == 'probe_paused': continue
        require(identity in jobs, 'Unknown probe job')
        payload, model, expected = probe_request(plan, jobs[identity], protocol, registry)
        if kind == 'probe_request_saved':
            require(identity not in requests and p['request'] == payload and p['request_sha256'] == fingerprint(payload)
                    and p['model_digest'] == model.digest, 'Repeated or changed probe request')
            requests[identity] = p
        elif kind == 'probe_response_saved':
            require(identity in requests and identity not in responses and identity not in errors, 'Duplicate/unrequested probe response')
            if 'preflight' in requests[identity] and meta['backend'] == LIVE_BACKEND:
                row = read_json(model.metadata_json)
                if row['backend'] == 'ollama' and 'qualification' in row['artifact']:
                    require(p['transport'].get('ollama_context') == requests[identity]['preflight'], 'Probe preflight association changed')
            responses[identity] = p
        elif kind == 'probe_result_saved':
            require(identity in responses and identity not in results and p['result'] == evaluate(responses[identity], payload, model, expected, meta), 'Probe score differs from saved evidence')
            results[identity] = p['result']
        elif kind == 'probe_request_error':
            require(identity in requests and identity not in responses and identity not in errors, 'Invalid probe error'); errors.add(identity)
        else:
            raise ValueError('Unknown probe event: '+kind)
    return meta, protocol, registry, requests, responses, results, complete


def execute_probes(directory, max_calls, backend=None, hook=None):
    require(type(max_calls) is int and max_calls >= 0, 'Explicit nonnegative probe call budget required')
    with Journal(directory) as journal:
        meta, protocol, registry, requests, responses, results, complete = reconstruct(journal.events)
        live = meta['backend'] == LIVE_BACKEND
        backend = backend or (HTTPBackend() if live else FakeBackend())
        require(backend.identity == meta['backend'], 'Wrong probe execution backend')
        calls = 0
        for job in meta['plan']['jobs']:
            identity = job['id']
            if identity in results: continue
            payload, model, expected = probe_request(meta['plan'], job, protocol, registry)
            if identity in requests and identity not in responses:
                raise NeedsAttention('Unresolved probe '+identity+'; automatic retry is disabled')
            if identity not in requests:
                if calls >= max_calls:
                    journal.append('probe_paused', {'new_calls': calls}); break
                require(not live or meta['parser_version'] == LIVE_PARSER, 'Legacy probe batch is replay-only')
                observation = backend.verify(model) if live else None
                preflight = backend.preflight(payload, model) if live and hasattr(backend, 'preflight') else None
                p = {'job': identity, 'request': payload, 'request_sha256': fingerprint(payload),
                     'model_digest': model.digest, 'observation': observation}
                if preflight is not None: p['preflight'] = preflight
                journal.append('probe_request_saved', p)
                if hook: hook('after_request', identity)
                try:
                    response = backend.generate(payload, model) if live else backend.generate(payload)
                except Exception as exc:
                    journal.append('probe_request_error', {'job': identity, 'error_type': type(exc).__name__, 'outcome': 'unknown'})
                    raise NeedsAttention('Probe transport failed; outcome unknown for '+identity) from exc
                calls += 1
                saved = {'job': identity, 'raw_response': response.raw if live else response}
                if live: saved['transport'] = response.evidence
                journal.append('probe_response_saved', saved); responses[identity] = saved
                if hook: hook('after_response', identity)
            result = evaluate(responses[identity], payload, model, expected, meta)
            journal.append('probe_result_saved', {'job': identity, 'result': result}); results[identity] = result
            if hook: hook('after_result', identity)
        if not complete and len(results) == len(meta['plan']['jobs']):
            journal.append('probe_complete', {'jobs': len(results)})
        return report_events(journal.events)


def report_events(events):
    meta, protocol, registry, requests, responses, results, complete = reconstruct(events)
    rows = []
    for job in meta['plan']['jobs']:
        _, model, expected = probe_request(meta['plan'], job, protocol, registry)
        rows.append(dict(job, model=model.label, expected=expected, result=results.get(job['id'])))
    return {'schema': 'behaviorlab.probe-report/1', 'data_class': meta['data_class'],
        'plan_sha256': meta['plan_sha256'], 'source': meta['plan']['source'],
        'planned_calls': len(rows), 'requests': len(requests), 'responses': len(responses),
        'scored': len(results), 'complete': complete, 'unavailable_snapshots': meta['plan']['unavailable_snapshots'],
        'unresolved': [k for k in requests if k not in responses], 'jobs': rows,
        'scope': 'Strict JSON task checks, not general competence or evidence of subjective experience. Format failures require review.'}


def probe_report(directory):
    return report_events(read_events(Path(directory)/'events.jsonl'))


def export_probes(directory):
    """Display independent checks together, without creating a probe conversation."""
    events = read_events(Path(directory)/'events.jsonl')
    report = report_events(events)
    require(report['complete'], 'Export requires a completed probe batch')
    meta, protocol, registry, *_ = reconstruct(events)
    identity = {'display_only': True, 'kind': 'independent_probe_results',
                'plan_sha256': report['plan_sha256'], 'journal_head': events[-1]['hash'],
                'data_class': report['data_class'], 'source': report['source']}
    digest = fingerprint(identity); stamp = int(time.time())
    def mid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL, digest+':'+key))
    display = [{'id': mid('intro'), 'role': 'user', 'parentId': None, 'childrenIds': [], 'timestamp': stamp,
        'content': 'Laboratory: independent probe results. These checks are separate continuations, not one conversation. '
                   'Baseline checks receive the same system and question with no participant history. '
                   'Edits or continuations here do not update the laboratory evidence.\n\nPlan: '+report['plan_sha256']}]
    tags = []
    for job in report['jobs']:
        _, model, _ = probe_request(meta['plan'], job, protocol, registry)
        prompt, _ = question(job, meta['plan']['spec'])
        label = job['id']+' · '+model.tag+' · '+job['snapshot']+' · '+('baseline' if job['baseline'] else 'snapshot history')
        text = ('**'+label+'**\n\n**Question**\n\n'+prompt+'\n\n**Response**\n\n'
                +job['result'].get('content', '[No valid response text]')+'\n\nStrict scorer: '+job['result']['status'])
        display.append({'id': mid(job['id']), 'role': 'assistant', 'parentId': display[-1]['id'],
            'childrenIds': [], 'timestamp': stamp, 'content': text, 'model': model.tag,
            'modelName': model.tag, 'done': True, 'lab_probe_id': job['id']})
        display[-2]['childrenIds'] = [display[-1]['id']]
        if model.tag not in tags: tags.append(model.tag)
    chat = {'title': 'Behavior Lab · independent probes · '+report['plan_sha256'][:10],
        'models': tags, 'messages': display, 'history': {'messages': {m['id']:m for m in display}, 'currentId': display[-1]['id']},
        'params': {}, 'timestamp': stamp*1000, 'lab_evidence': identity}
    return {'chats': [{'chat': chat, 'meta': {'behaviorlab_export_id': digest},
        'current_message_id': display[-1]['id'], 'created_at': stamp, 'updated_at': stamp}]}
