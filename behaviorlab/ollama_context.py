"""Version-pinned native Ollama rendering and recipient token preflight.

These are render/tokenize observations, not captures of a generation request at
the runner. Native response counts cross-check the subsequent generation.
"""
import base64
import hashlib
from pathlib import Path
import re
import shlex
import subprocess

from .common import canonical, fingerprint, read_json, require, sha256

SCHEMA = 'ollama-local-render/1'
MODE_SCHEMA = 'ollama-local-render/2'


def thinking_mode(q):
    return False if q['schema'] == SCHEMA else q['thinking']


class ContextLimitError(ValueError):
    def __init__(self, evidence):
        self.evidence = evidence
        super().__init__('Rendered recipient input plus output reserve exceeds context: '
                         + str(evidence['input_tokens']) + ' + ' + str(evidence['reserved_output_tokens'])
                         + ' > ' + str(evidence['context_window']))


def profile(model):
    return read_json(model.metadata_json)['artifact']['qualification']


def parameter_values(text):
    """Ollama prints a Go map in variable key order; preserve per-key lists."""
    result = {}
    for line in text.splitlines():
        parts = line.split(None, 1)
        require(len(parts) == 2 and re.fullmatch(r'[a-z][a-z0-9_]*', parts[0]), 'Malformed default option')
        result.setdefault(parts[0], []).append(read_json(parts[1]))
    return result


def validate_artifact(row):
    q = row['artifact']['qualification']
    fields = {'schema', 'manifest_path', 'model_blob', 'runner_path', 'runner_arguments', 'runner_build_info', 'parameters', 'files'}
    if isinstance(q, dict) and q.get('schema') == MODE_SCHEMA:
        fields.add('thinking')
    require(isinstance(q, dict) and set(q) == fields and q['schema'] in (SCHEMA, MODE_SCHEMA)
            and type(thinking_mode(q)) is bool,
            'Invalid Ollama rendering qualification')
    for key in ('manifest_path', 'model_blob', 'runner_path'):
        require(isinstance(q[key], str) and Path(q[key]).is_absolute() and not re.search(r'\s', q[key]),
                'This runner discovery profile requires absolute paths without whitespace')
    require(isinstance(q['runner_arguments'], list) and q['runner_arguments'].count('{port}') == 1
            and q['runner_arguments'][0] == q['runner_path'], 'Pin normalized runner arguments')
    require(isinstance(q['runner_build_info'], str) and q['runner_build_info'], 'Pin runner build identity')
    require(isinstance(q['parameters'], dict), 'Pin structured model defaults')
    require(isinstance(q['files'], list) and q['files'], 'Pin local artifact and runtime files')
    names = []
    for f in q['files']:
        require(set(f) == {'path', 'sha256', 'bytes'} and Path(f['path']).is_absolute()
                and re.fullmatch('[a-f0-9]{64}', f['sha256']) and type(f['bytes']) is int and f['bytes'] > 0,
                'Invalid pinned file')
        names.append(f['path'])
    require(len(set(names)) == len(names) and {q[k] for k in ('manifest_path', 'model_blob', 'runner_path')} <= set(names),
            'Missing or duplicate pinned artifact/runtime file')
    require(next(f['sha256'] for f in q['files'] if f['path'] == q['manifest_path']) == row['digest'],
            'Manifest identity differs from registry')


def verify_files(model, cache):
    q = profile(model)
    def signatures():
        result = []
        for f in q['files']:
            p = Path(f['path']); s = p.stat()
            require(s.st_size == f['bytes'], 'Pinned file size changed: ' + p.name)
            result.append((str(p), s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns))
        return result
    before = signatures()
    key = fingerprint({'files': q['files'], 'signatures': before})
    # Keep distinct entries for the two recipients: switching models must not
    # force a fresh full-weight read when neither artifact changed.
    cache_name = 'ollama-files:' + model.digest
    if cache.get(cache_name) != key:
        for f in q['files']:
            h = hashlib.sha256()
            with Path(f['path']).open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    h.update(block)
            require(h.hexdigest() == f['sha256'], 'Pinned file content changed: ' + Path(f['path']).name)
        require(signatures() == before, 'Artifact changed during verification')
        cache[cache_name] = key
    return {'content_hash_verified': True, 'files_fingerprint': fingerprint(q['files']),
            'verification_cache_key': key, 'file_count': len(q['files'])}


def discover_runner(q, context):
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,command='], capture_output=True, text=True, check=True)
    matches = []
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3 or not parts[2].startswith(q['runner_path'] + ' '):
            continue
        argv = shlex.split(parts[2])
        def option(name):
            require(argv.count(name) == 1 and argv.index(name)+1 < len(argv), 'Missing runner option ' + name)
            return argv[argv.index(name)+1]
        if option('--model') != q['model_blob']:
            continue
        port = int(option('--port'))
        require(1 <= port <= 65535 and option('--host') == '127.0.0.1'
                and int(option('-c')) == context and option('-np') == '1', 'Runner route/context mismatch')
        normalized = list(argv); normalized[argv.index('--port')+1] = '{port}'
        require(normalized == q['runner_arguments'], 'Runner launch arguments changed')
        matches.append({'pid': int(parts[0]), 'parent_pid': int(parts[1]), 'arguments': argv,
                        'endpoint': 'http://127.0.0.1:' + str(port)})
    require(len(matches) == 1, 'Expected exactly one matching local runner')
    return matches[0]


def document(request, response):
    return {'request': request, 'raw_response': response.raw, 'transport': response.evidence}


def decoded(record):
    wire = record['transport']; raw = record['raw_response']
    data = base64.b64decode(wire['response_bytes_base64'], validate=True)
    require(wire['http_status'] == 200 and sha256(data) == wire['response_sha256']
            and data.decode('utf-8') == raw, 'Invalid render/tokenize HTTP evidence')
    return read_json(raw)


def preflight(payload, model):
    from .backends import http_request
    q = profile(model); row = read_json(model.metadata_json)
    require(payload.get('truncate') is False and payload.get('shift') is False and payload.get('think') is thinking_mode(q),
            'Qualified Ollama requires pinned thinking mode and truncation/shift disabled')
    render_payload = read_json(canonical(payload)); render_payload['_debug_render_only'] = True
    render = document(render_payload, http_request(row['endpoint'], '/api/chat', render_payload))
    d = decoded(render)
    require(d.get('model') == model.tag and d.get('done') is False and not d.get('eval_count'),
            'Render-only call unexpectedly generated or reported another model')
    prompt = d['_debug_info']['rendered_template']
    require(isinstance(prompt, str) and prompt and d['_debug_info'].get('image_count', 0) == 0,
            'Missing text-only rendered input')
    context = payload['options']['num_ctx']
    runner = discover_runner(q, context)
    props = document(None, http_request(runner['endpoint'], '/props'))
    config = decoded(props)
    require(config['model_path'] == q['model_blob'] and config['build_info'] == q['runner_build_info']
            and config['total_slots'] == 1 and config['default_generation_settings']['n_ctx'] == context,
            'Runner model/build/context differs from pinned configuration')
    token_payload = {'content': prompt, 'add_special': False, 'parse_special': True}
    tokenization = document(token_payload, http_request(runner['endpoint'], '/tokenize', token_payload))
    tokens = decoded(tokenization)['tokens']
    require(isinstance(tokens, list) and tokens and all(type(t) is int and t >= 0 for t in tokens),
            'Missing recipient token IDs')
    reserve = payload['options']['num_predict']
    evidence = {'schema': q['schema'], 'request_sha256': fingerprint(payload), 'render': render, 'runner': runner,
            'runner_configuration_defaults': props, 'tokenization': tokenization,
            'rendered_utf8_sha256': sha256(prompt.encode()), 'prompt_token_ids_sha256': fingerprint(tokens),
            'input_tokens': len(tokens), 'context_window': context, 'reserved_output_tokens': reserve,
            'context_headroom': context-len(tokens)-reserve,
            'scope': 'Runtime render-only and tokenizer observations; generation input token IDs and final sampler parameters are not captured.'}
    if evidence['context_headroom'] < 0:
        raise ContextLimitError(evidence)
    return evidence


def validate_response_evidence(data, payload, evidence, model):
    require(isinstance(evidence, dict) and evidence.get('schema') == profile(model)['schema'], 'Missing Ollama context evidence')
    require(evidence['request_sha256'] == fingerprint(payload), 'Preflight belongs to another request')
    expected = read_json(canonical(payload)); expected['_debug_render_only'] = True
    require(evidence['render']['request'] == expected, 'Render-only request differs from generation request')
    render = decoded(evidence['render'])
    prompt = render['_debug_info']['rendered_template']
    require(render['model'] == payload['model'] and render['done'] is False and not render.get('eval_count'),
            'Invalid render-only response')
    require(evidence['tokenization']['request'] == {'content': prompt, 'add_special': False, 'parse_special': True},
            'Recipient tokenization input changed')
    tokens = decoded(evidence['tokenization'])['tokens']
    require(isinstance(tokens, list) and tokens and all(type(t) is int and t >= 0 for t in tokens)
            and len(tokens) == evidence['input_tokens'] and fingerprint(tokens) == evidence['prompt_token_ids_sha256']
            and sha256(prompt.encode()) == evidence['rendered_utf8_sha256'], 'Token/render evidence changed')
    context, reserve = payload['options']['num_ctx'], payload['options']['num_predict']
    q = profile(model)
    runner = evidence['runner']; argv = list(runner['arguments'])
    require(argv.count('--port') == 1, 'Ambiguous runner port')
    port = int(argv[argv.index('--port')+1]); argv[argv.index('--port')+1] = '{port}'
    require(1 <= port <= 65535 and runner['endpoint'] == 'http://127.0.0.1:' + str(port)
            and argv == q['runner_arguments'], 'Recorded runner route/arguments changed')
    config = decoded(evidence['runner_configuration_defaults'])
    require(config['model_path'] == q['model_blob'] and config['build_info'] == q['runner_build_info']
            and config['total_slots'] == 1 and config['default_generation_settings']['n_ctx'] == context,
            'Recorded runner configuration changed')
    require(payload.get('truncate') is False and payload.get('shift') is False and payload.get('think') is thinking_mode(q),
            'Context or thinking controls changed')
    require(evidence['context_window'] == context and evidence['reserved_output_tokens'] == reserve
            and evidence['context_headroom'] == context-len(tokens)-reserve >= 0, 'Insufficient context headroom')
    require(type(data.get('prompt_eval_count')) is int and data['prompt_eval_count'] == len(tokens),
            'Generation prompt count differs from recipient preflight')
    cached = data.get('prompt_eval_cached_count')
    require(type(cached) is int and 0 <= cached <= len(tokens), 'Missing or invalid cached-token accounting')
    require(type(data.get('eval_count')) is int and 0 <= data['eval_count'] <= reserve,
            'Generation exceeded output allowance or omitted token count')
