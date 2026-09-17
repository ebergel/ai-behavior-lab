"""Finite TypeSafe assessment runner, deliberately separate from the web explorer.

Run: python3 -m behaviorlab.jev_runner --workspace workspace --batch ID
Credentials: TYPESAFE_API_KEY or workspace/private/typesafe-api-key.
"""
import argparse
import json
import os
from pathlib import Path
import stat
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .common import canonical, require
from .jev_atlas import ENDPOINT, MAX_INPUT, MODEL, PRICE, JevAtlas, locked, now, read_record, write_record, software_identity


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def credential(workspace):
    key = os.environ.get('TYPESAFE_API_KEY', '').strip()
    if not key:
        path = Path(workspace) / 'private' / 'typesafe-api-key'
        require(path.is_file() and not path.is_symlink(), 'TypeSafe API key is missing; configure the environment or private key file')
        require(stat.S_IMODE(path.stat().st_mode) & 0o077 == 0, 'Set private/typesafe-api-key permissions to 600')
        key = path.read_text().strip()
    require(key and not any(c.isspace() for c in key), 'Invalid credential format')
    return key


def transport(payload, key):
    request = Request(ENDPOINT, data=canonical(payload).encode(), headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
    try:
        with build_opener(NoRedirect()).open(request, timeout=60) as response:
            return response.status, response.read(4_000_000).decode('utf-8')
    except HTTPError as error:
        return error.code, error.read(1_000_000).decode('utf-8', errors='replace')


def execute(workspace, identity, send=None, key=None, max_calls=None):
    store = JevAtlas(workspace); path = store.batch_path(identity)
    with locked(path / '.runner.lock', blocking=False):
        plan = store.plan(identity)
        revision = store.integration_revision(plan)
        frozen_software = revision['software_sha256'] if revision else plan['software_sha256']
        require(frozen_software == software_identity(), 'Runner software changed since freeze; prepare a new batch')
        require(plan['endpoint'] == ENDPOINT and plan['model'] == MODEL and
                plan['budget']['usd_per_million_input'] == PRICE and
                plan['budget']['reserved_input_tokens_per_call'] == MAX_INPUT and
                len(plan['items']) == plan['budget']['max_calls'] <= 200 and
                0 < plan['budget']['usd_ceiling'] <= 0.60, 'Unsupported model, route or budget freeze')
        rows = store.results(plan)
        require(not any(r['status'] in ('error', 'unresolved') for r in rows),
                'Batch stopped on failed or unresolved response. Inspect saved evidence; no automatic retry.')
        pending = [r for r in rows if r['status'] == 'pending']
        if revision:
            require(all(r['id'] in revision['allowed_new_items'] for r in pending),
                    'Pending request is outside the integration allocation')
        if not pending: return store.summary(plan, rows)
        if send is None:
            key = credential(workspace); send = transport
        require(max_calls is None or type(max_calls) is int and max_calls > 0, 'max-calls must be positive')
        spent = sum(r['cost_usd'] or 0 for r in rows)
        reserve = MAX_INPUT * PRICE / 1_000_000
        for index, item in enumerate(pending):
            if max_calls is not None and index >= max_calls: break
            require(spent + reserve <= plan['budget']['usd_ceiling'], 'Insufficient remaining reserved budget')
            payload = store.payload(plan, item)
            require(len(canonical(payload).encode()) < 60000, 'Input exceeds conservative byte screen; no request dispatched')
            # This durable marker precedes network I/O; interruptions never imply zero calls.
            request_path = path / 'requests' / (item['id'] + '.json')
            write_record(request_path, {'item_id': item['id'], 'plan_sha256': plan['sha256'],
                                       'at': now(), 'payload': payload, 'reserved_usd': reserve})
            request = read_record(request_path); start = time.monotonic()
            record = {'request_sha256': request['sha256'], 'at': now(), 'http_status': None,
                      'raw_text': '', 'error': None}
            try:
                record['http_status'], record['raw_text'] = send(payload, key)
                if key and key in record['raw_text']:
                    record['raw_text'] = record['raw_text'].replace(key, '[credential removed]')
                    record['http_status'] = None; record['error'] = 'Credential echoed by service; response excluded'
                elif record['http_status'] != 200: record['error'] = 'Service returned HTTP ' + str(record['http_status'])
            except Exception:
                # Exception strings can contain credential-bearing URLs; never persist them.
                record['error'] = 'Transport failed after dispatch; provider cost unknown'
            record['elapsed_seconds'] = round(time.monotonic() - start, 4)
            write_record(path / 'responses' / (item['id'] + '.json'), record)
            rows = store.results(plan)
            current = next(r for r in rows if r['id'] == item['id'])
            print(canonical({'completed': sum(r['status'] == 'complete' for r in rows),
                             'planned': len(rows), 'latest_status': current['status']}), flush=True)
            if current['status'] != 'complete': break
            spent += current['cost_usd']
        return store.summary(plan, store.results(plan))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='workspace'); parser.add_argument('--batch', required=True)
    parser.add_argument('--max-calls', type=int)
    args = parser.parse_args()
    try:
        result = execute(args.workspace, args.batch, max_calls=args.max_calls)
        print(json.dumps(result, indent=2))
        if result['failed']: raise SystemExit(2)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__': main()
