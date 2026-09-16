"""Finite OpenRouter self-play with immutable plans, routing checks and a cost ledger.

Separate from the factorial runtime. No cloud inference is exposed by the Explorer.
Only this module's explicit CLI runner dispatches; readers replay saved bytes.
"""
import base64
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from decimal import Decimal
import os
from pathlib import Path

from .backends import http_request, json_request
from .common import canonical, fingerprint, read_json, require, sha256, timestamp
from .journal import Journal, read_events

ENDPOINT = 'https://openrouter.ai/api/v1'
PARSER = 'participant-response/1'
MODELS = {
    'mini': ('openai/gpt-4o-mini-2024-07-18', 'openai', 'OpenAI', '0.15', '0.60'),
    'haiku': ('anthropic/claude-haiku-4.5', 'anthropic', 'Anthropic', '1', '5'),
}
PROMPTS = {
    'anonymous': 'You may act freely in this open-ended conversation. Write only your own next message. Keep each message to at most 150 words.',
    'mirror': 'You may act freely in this open-ended context. You are in conversation with another instance of the same AI model. There is no human user in this conversation. Keep each message to at most 150 words. There is no task; the two of you decide what to talk about.',
}
OPENING = '(The conversation begins. You speak first.)'


def money(value):
    require(type(value) in (str, int, float, Decimal), 'Invalid monetary value')
    result = Decimal(str(value))
    require(result.is_finite() and result >= 0, 'Invalid monetary value')
    return result


def credential(webui_token_file=None):
    """Resolve only the selected connection in memory; never retain its config."""
    if os.environ.get('OPENROUTER_API_KEY'):
        return os.environ['OPENROUTER_API_KEY']
    require(webui_token_file is not None, 'Provide OPENROUTER_API_KEY or the existing WebUI token file')
    token = Path(webui_token_file).read_text().strip()
    config = json_request('http://127.0.0.1:8080', '/openai/config', token=token)
    indices = [i for i, url in enumerate(config['OPENAI_API_BASE_URLS']) if url.rstrip('/') == ENDPOINT]
    require(config.get('ENABLE_OPENAI_API') is True and len(indices) == 1, 'Expected one enabled OpenRouter connection')
    key = config['OPENAI_API_KEYS'][indices[0]]
    require(isinstance(key, str) and key and '*' not in key, 'OpenRouter credential unavailable')
    return key


def make_plan(replicates=10):
    require(type(replicates) is int and 1 <= replicates <= 10, 'Use one to ten replicates per condition')
    plan = {'schema': 'behaviorlab.participant-plan/1', 'id': 'cheap-cloud-participants-v1',
        'data_class': 'exploratory_cloud_participant_comparison_not_factorial_pilot',
        'parser': PARSER, 'endpoint': ENDPOINT, 'temperature': 0.8, 'max_tokens': 2048,
        'messages_per_root': 30, 'budget_usd': '5.00', 'max_inflight': 4,
        'opening': OPENING, 'prompts': PROMPTS, 'models': {}, 'jobs': [],
        'failure_policy': 'no_retry_stop_descendants_halt_on_unknown_cost_or_identity',
        'word_policy': 'flag_preserve_continue', 'exit_policy': 'literal_END_is_content',
        'seed_base': 1500000000, 'created_at': timestamp()}
    for label, (model, slug, name, prompt_price, completion_price) in MODELS.items():
        plan['models'][label] = {'model': model, 'provider_slug': slug, 'provider_name': name,
            'prompt_usd_per_million': prompt_price, 'completion_usd_per_million': completion_price,
            'seed_supported': label == 'mini', 'reasoning_disabled': label == 'haiku',
            'weight_digest': None, 'template': None, 'other_sampler_defaults': 'unknown'}
        plan['jobs'].append({'id': label+'-smoke', 'model': label, 'condition': 'smoke', 'replicate': 0, 'turns': 1})
    for rep in range(1, replicates+1):
        for condition in (('anonymous', 'mirror') if rep % 2 else ('mirror', 'anonymous')):
            for label in MODELS:
                plan['jobs'].append({'id': '%s-%s-%02d' % (label, condition, rep), 'model': label,
                    'condition': condition, 'replicate': rep, 'turns': 30})
    plan['max_calls'] = sum(j['turns'] for j in plan['jobs'])
    return plan


def validate(plan):
    require(plan['schema'] == 'behaviorlab.participant-plan/1' and plan['parser'] == PARSER, 'Unknown participant contract')
    require(plan['endpoint'] == ENDPOINT and plan['data_class'] == 'exploratory_cloud_participant_comparison_not_factorial_pilot', 'Wrong participant scope')
    require(plan['temperature'] == 0.8 and plan['max_tokens'] == 2048 and plan['messages_per_root'] == 30, 'Unqualified generation settings')
    require(plan['prompts'] == PROMPTS and plan['opening'] == OPENING, 'Unknown prompt contrast')
    require(plan['failure_policy'] == 'no_retry_stop_descendants_halt_on_unknown_cost_or_identity'
            and plan['word_policy'] == 'flag_preserve_continue' and plan['exit_policy'] == 'literal_END_is_content', 'Unknown stopping rules')
    require(0 < money(plan['budget_usd']) <= 5 and type(plan['max_inflight']) is int and 1 <= plan['max_inflight'] <= 4, 'Invalid budget or concurrency')
    require(plan['seed_base'] == 1500000000 and set(plan['models']) == set(MODELS), 'Wrong model or seed allocation')
    for label, row in plan['models'].items():
        model, slug, name, price_in, price_out = MODELS[label]
        require((row['model'], row['provider_slug'], row['provider_name']) == (model, slug, name), 'Model routing changed')
        require(money(row['prompt_usd_per_million']) == money(price_in) and money(row['completion_usd_per_million']) == money(price_out), 'Price ceiling changed')
        require(row['seed_supported'] is (label == 'mini') and row['reasoning_disabled'] is (label == 'haiku'), 'Unsupported controls')
        require(row['weight_digest'] is None and row['template'] is None, 'Unknown remote internals must stay unknown')
    jobs = plan['jobs']
    require(len(jobs) >= 6 and (len(jobs)-2) % 4 == 0 and len(jobs) <= 42, 'Invalid balanced job count')
    expected = make_plan((len(jobs)-2)//4)['jobs']
    require(jobs == expected and plan['max_calls'] == sum(j['turns'] for j in jobs), 'Job/aggregate budget mismatch')
    canonical(plan)
    return plan


def slots(plan):
    return [{'id': job['id']+':'+str(t), 'job': job['id'], 'turn': t,
             'seed': plan['seed_base']+1000*i+t,
             'seed_sent': plan['models'][job['model']]['seed_supported']}
            for i, job in enumerate(plan['jobs']) for t in range(1, job['turns']+1)]


def payload(plan, job, turn, results):
    model = plan['models'][job['model']]
    messages = [{'role': 'system', 'content': 'Reply with the single word Ready.' if job['condition'] == 'smoke' else plan['prompts'][job['condition']]}]
    speaker = 'X' if turn % 2 else 'Y'
    if speaker == 'X': messages.append({'role': 'user', 'content': OPENING})
    for previous in range(1, turn):
        row = results[job['id']+':'+str(previous)]
        require(row['status'] == 'valid', 'History contains an unavailable or invalid ancestor')
        messages.append({'role': 'assistant' if previous % 2 == turn % 2 else 'user', 'content': row['text']})
    p = {'model': model['model'], 'messages': messages, 'stream': False,
         'temperature': plan['temperature'], 'max_tokens': 32 if job['condition'] == 'smoke' else plan['max_tokens'],
         'transforms': [], 'provider': {'only': [model['provider_slug']], 'allow_fallbacks': False,
             'require_parameters': True, 'max_price': {'prompt': float(money(model['prompt_usd_per_million'])),
                 'completion': float(money(model['completion_usd_per_million']))}}}
    if model['seed_supported']:
        p['seed'] = plan['seed_base']+1000*plan['jobs'].index(job)+turn
    if model['reasoning_disabled']: p['reasoning'] = {'enabled': False}
    return p


def reservation(plan, job, request):
    """Conservative byte-based estimate with explicit provider-overrun detection.

    Not a claim of knowing the remote tokenizer. Any overrun stops further calls.
    """
    row = plan['models'][job['model']]
    upper = sum(len(m['content'].encode('utf-8'))+64 for m in request['messages'])+2048
    require(upper+request['max_tokens'] <= 128000, 'Conservative context allowance exceeded')
    cost = (Decimal(upper)*money(row['prompt_usd_per_million']) +
            Decimal(request['max_tokens'])*money(row['completion_usd_per_million']))/Decimal(1000000)
    return {'input_token_allowance': upper, 'output_token_allowance': request['max_tokens'], 'usd': str(cost)}


def parse_response(raw, transport, plan, job, request, reserved):
    b = base64.b64decode(transport['response_bytes_base64'], validate=True)
    require(sha256(b) == transport['response_sha256'] and b.decode('utf-8', errors='replace') == raw, 'Raw response integrity failure')
    result = {'status': 'invalid', 'reason': None, 'text': None, 'thinking': None, 'cost_usd': None,
              'usage': None, 'reported_model': None, 'provider': None, 'system_fingerprint': None, 'halt': False}
    try:
        d = read_json(b.decode('utf-8'))
        if isinstance(d, dict):
            result.update(reported_model=d.get('model'), provider=d.get('provider'), system_fingerprint=d.get('system_fingerprint'))
            usage = d.get('usage'); result['usage'] = usage
            if isinstance(usage, dict) and usage.get('cost') is not None:
                result['cost_usd'] = str(money(usage['cost']))
        require(transport['http_status'] == 200 and not d.get('error'), 'HTTP or provider error')
        row = plan['models'][job['model']]
        require(d.get('model') == row['model'], 'Reported model mismatch')
        require(d.get('provider') == row['provider_name'], 'Reported provider mismatch')
        require(result['cost_usd'] is not None, 'Missing billed usage cost')
        require(money(result['cost_usd']) <= money(reserved['usd']), 'Provider cost exceeds reserved allowance')
        u = result['usage']
        require(all(type(u.get(k)) is int and u[k] >= 0 for k in ('prompt_tokens', 'completion_tokens')), 'Missing token usage')
        require(u['prompt_tokens'] <= reserved['input_token_allowance'] and u['completion_tokens'] <= request['max_tokens'], 'Usage exceeds reserved allowance')
        require(len(d['choices']) == 1, 'Expected one response choice')
        choice = d['choices'][0]; msg = choice['message']
        require(msg.get('role') == 'assistant' and isinstance(msg.get('content'), str), 'Missing assistant text')
        result['text'] = msg['content']
        traces = {k:msg[k] for k in ('reasoning', 'reasoning_details', 'reasoning_content', 'thinking') if msg.get(k)}
        result['thinking'] = canonical(traces) if traces else None
        require(not traces and not (u.get('completion_tokens_details') or {}).get('reasoning_tokens'), 'Unexpected reasoning output')
        require(not msg.get('tool_calls') and not msg.get('function_call'), 'Unexpected tool call')
        require(choice.get('finish_reason') in ('stop', 'length'), 'Unsupported finish reason')
        result.update(status='cap' if choice['finish_reason'] == 'length' else 'valid',
                      reason='output_cap' if choice['finish_reason'] == 'length' else None)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, UnicodeError) as exc:
        # Errors have fixed local messages/exception types; never include credential-bearing requests.
        result.update(reason=str(exc)[:200], halt=True)
    return result


def replay(events):
    require(events and events[0]['kind'] == 'participant_comparison_created', 'Not a participant comparison')
    header = events[0]['payload']; plan = validate(header['plan'])
    require(header['plan_sha256'] == fingerprint(plan), 'Plan checksum mismatch')
    jobs = {j['id']: j for j in plan['jobs']}; valid_slots = {s['id']:s for s in slots(plan)}
    requests = {}; responses = {}; results = {}; errors = {}; rejected = {}; pauses = []; complete = False
    for event in events[1:]:
        kind, p = event['kind'], event['payload']; key = p.get('id')
        if kind == 'participant_request':
            require(key in valid_slots and key not in requests and key not in rejected and not complete, 'Duplicate/unknown dispatch')
            slot = valid_slots[key]; job = jobs[slot['job']]
            expected = payload(plan, job, slot['turn'], results)
            require(p['request'] == expected and p['request_sha256'] == fingerprint(expected), 'Saved participant history differs')
            require(p['reservation'] == reservation(plan, job, expected), 'Cost reservation differs')
            if job['condition'] != 'smoke':
                require(all(results.get(j['id']+':1', {}).get('status') == 'valid' for j in plan['jobs'][:2]), 'Main run before smoke qualification')
            used = sum((money(results[k]['cost_usd']) if k in results and results[k]['cost_usd'] is not None else money(v['reservation']['usd'])) for k,v in requests.items())
            require(used+money(p['reservation']['usd']) <= money(plan['budget_usd']), 'Journal exceeds budget')
            requests[key] = p
        elif kind == 'participant_response':
            require(key in requests and key not in responses and key not in errors, 'Unrequested/duplicate response')
            responses[key] = p
        elif kind == 'participant_result':
            require(key in responses and key not in results, 'Unrequested/duplicate result')
            req = requests[key]; resp = responses[key]; job = jobs[valid_slots[key]['job']]
            expected = parse_response(resp['raw'], resp['transport'], plan, job, req['request'], req['reservation'])
            require(p['result'] == expected, 'Participant result differs from source bytes')
            results[key] = expected
        elif kind == 'participant_transport_error':
            require(key in requests and key not in responses and key not in errors, 'Invalid transport error')
            errors[key] = p
        elif kind == 'participant_preflight_rejected':
            require(key in valid_slots and key not in requests and key not in rejected, 'Invalid preflight rejection')
            rejected[key] = p
        elif kind == 'participant_paused': pauses.append(p)
        elif kind == 'participant_complete':
            require(not complete, 'Duplicate completion'); complete = True
        else: raise ValueError('Unknown participant event')
    return {'plan': plan, 'requests': requests, 'responses': responses, 'results': results,
            'errors': errors, 'rejected': rejected, 'pauses': pauses, 'complete': complete}


def report(events):
    state = replay(events); plan = state['plan']; rows = []
    for job in plan['jobs']:
        counts = {'valid':0, 'cap':0, 'invalid':0, 'blocked':0, 'unresolved':0, 'pending':0, 'not_dispatched':0, 'uncommitted':0}
        blocked = False
        for t in range(1, job['turns']+1):
            key = job['id']+':'+str(t)
            r = state['results'].get(key)
            status = r['status'] if r else 'not_dispatched' if key in state['rejected'] else 'uncommitted' if key in state['responses'] else 'unresolved' if key in state['requests'] else 'blocked' if blocked else 'pending'
            counts[status] += 1
            blocked = blocked or status in ('cap','invalid','not_dispatched','unresolved')
        rows.append(dict(job, counts=counts))
    known = sum((money(r['cost_usd']) for r in state['results'].values() if r['cost_usd'] is not None), Decimal(0))
    held = sum((money(p['reservation']['usd']) for k,p in state['requests'].items() if state['results'].get(k,{}).get('cost_usd') is None), Decimal(0))
    return {'schema':'behaviorlab.participant-report/1', 'plan_sha256':fingerprint(plan),
            'requests':len(state['requests']), 'responses':len(state['responses']), 'known_cost_usd':str(known),
            'reserved_unknown_cost_usd':str(held), 'budget_usd':plan['budget_usd'], 'complete':state['complete'],
            'jobs':rows, 'last_pause':state['pauses'][-1] if state['pauses'] else None,
            'journal_head':events[-1]['hash']}


class OpenRouter:
    def __init__(self, token): self.token = token

    def verify(self, plan):
        observations = {}
        for label, row in plan['models'].items():
            data = json_request(ENDPOINT, '/models/'+row['model']+'/endpoints')['data']
            routes = [e for e in data['endpoints'] if e['tag'] == row['provider_slug']]
            require(len(routes) == 1, 'Pinned provider unavailable: '+label)
            route = routes[0]
            needed = {'temperature','max_tokens'} | ({'seed'} if row['seed_supported'] else {'reasoning'})
            require(needed <= set(route['supported_parameters']), 'Requested parameters unavailable: '+label)
            require(route['provider_name'] == row['provider_name'] and route['status'] == 0, 'Pinned provider unhealthy: '+label)
            for kind, field in [('prompt','prompt_usd_per_million'), ('completion','completion_usd_per_million')]:
                require(money(route['pricing'][kind])*1000000 <= money(row[field]), 'Provider price exceeds ceiling: '+label)
            require(route['context_length'] >= 128000 and route['max_completion_tokens'] >= plan['max_tokens'], 'Provider capacity changed')
            observations[label] = {'at':timestamp(), 'model_data_id':data['id'], 'endpoint':route}
        # Check account access without recording its key label or other identifying metadata.
        key_data = json_request(ENDPOINT, '/key', token=self.token)['data']
        require(key_data.get('is_free_tier') is False, 'Paid OpenRouter access required')
        return observations

    def generate(self, request):
        return http_request(ENDPOINT, '/chat/completions', request, self.token, timeout=120)


def create(directory, plan, verification, seed_audit, code_hashes, synthetic=False):
    validate(plan); directory = Path(directory); directory.mkdir(parents=True, exist_ok=False)
    with Journal(directory, create=True) as journal:
        journal.append('participant_comparison_created', {'plan':plan, 'plan_sha256':fingerprint(plan),
            'verification':verification, 'seed_audit':seed_audit, 'code_hashes':code_hashes, 'synthetic':synthetic})


def execute(directory, backend, smoke_only=False, hook=None):
    """Single journal writer; parallel independent roots; never retries a saved request."""
    with Journal(Path(directory)) as journal:
        state = replay(journal.events); plan = state['plan']; jobs = {j['id']:j for j in plan['jobs']}
        header = journal.events[0]['payload']
        require(header['synthetic'] is bool(getattr(backend, 'synthetic', False)), 'Synthetic/live backend mismatch')
        for path, digest in header['code_hashes'].items():
            require(sha256(Path(path).read_bytes()) == digest, 'Frozen execution code changed: '+path)
        index = {s['id']:s for s in slots(plan)}
        # Recover received raw responses without contacting the service.
        for key, response in state['responses'].items():
            if key not in state['results']:
                req = state['requests'][key]
                r = parse_response(response['raw'], response['transport'], plan, jobs[index[key]['job']], req['request'], req['reservation'])
                journal.append('participant_result', {'id':key, 'result':r})
        state = replay(journal.events)
        if state['complete']: return report(journal.events)
        if any(k not in state['responses'] for k in state['requests']) or state['rejected'] or any(r['halt'] for r in state['results'].values()):
            return report(journal.events)
        # Verify model routes/prices again before resuming. No generation during verification.
        backend.verify(plan)
        results = state['results']; requests = state['requests']; active = {}; active_jobs = set()
        stopped = False
        def ledger():
            return sum((money(results[k]['cost_usd']) if k in results and results[k]['cost_usd'] is not None
                        else money(v['reservation']['usd'])) for k,v in requests.items())
        with ThreadPoolExecutor(max_workers=plan['max_inflight']) as pool:
            while True:
                smoke_ok = all(results.get(j['id']+':1',{}).get('status') == 'valid' for j in plan['jobs'][:2])
                eligible = plan['jobs'][:2] if not smoke_ok or smoke_only else plan['jobs'][2:]
                for job in eligible:
                    if stopped or len(active) >= plan['max_inflight']: break
                    if job['id'] in active_jobs: continue
                    prior = [results.get(job['id']+':'+str(t)) for t in range(1,job['turns']+1)]
                    if any(r and r['status'] != 'valid' for r in prior): continue
                    turn = next((t for t,r in enumerate(prior,1) if r is None), None)
                    if turn is None: continue
                    key = job['id']+':'+str(turn)
                    require(key not in requests, 'Unresolved request cannot be retried')
                    p = payload(plan, job, turn, results)
                    try: reserved = reservation(plan, job, p)
                    except ValueError as exc:
                        journal.append('participant_preflight_rejected', {'id':key, 'reason':str(exc), 'generation_dispatches':0})
                        stopped = True; break
                    if ledger()+money(reserved['usd']) > money(plan['budget_usd']):
                        journal.append('participant_paused', {'reason':'budget_ceiling', 'id':key, 'ledger_usd':str(ledger())})
                        stopped = True; break
                    saved = {'id':key,'request':p,'request_sha256':fingerprint(p),'reservation':reserved}
                    journal.append('participant_request', saved); requests[key] = saved
                    if hook: hook('after_request', key)
                    future = pool.submit(backend.generate, p); active[future] = (key,job); active_jobs.add(job['id'])
                if not active: break
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    key, job = active.pop(future); active_jobs.remove(job['id'])
                    try:
                        wire = future.result()
                    except Exception as exc:
                        journal.append('participant_transport_error', {'id':key,'error_type':type(exc).__name__, 'outcome':'unknown_no_retry'})
                        stopped = True; continue
                    journal.append('participant_response', {'id':key,'raw':wire.raw,'transport':wire.evidence})
                    if hook: hook('after_response', key)
                    req = requests[key]
                    r = parse_response(wire.raw, wire.evidence, plan, job, req['request'], req['reservation'])
                    journal.append('participant_result', {'id':key,'result':r}); results[key] = r
                    if hook: hook('after_result', key)
                    if r['halt'] or job['condition']=='smoke' and r['status']!='valid': stopped = True
        current = report(journal.events)
        if all(not any(j['counts'][k] for k in ('pending','unresolved','uncommitted')) for j in current['jobs']):
            journal.append('participant_complete', {'accounted_jobs':len(plan['jobs'])})
        elif not current['last_pause'] or current['last_pause']['reason'] != 'budget_ceiling':
            journal.append('participant_paused', {'reason':'smoke_complete' if smoke_only and not stopped else 'technical_failure'})
        return report(journal.events)
