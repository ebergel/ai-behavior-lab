"""Publishable research snapshots and non-destructive, offline restoration.

Original evidence bytes and notebook rows are authoritative. Readable transcript
projections supplement those sources; no inference client is dispatched here.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import tempfile

from .common import fingerprint, require, sha256

SCHEMA = 'behaviorlab.research-bundle/1'
EXCLUDED_PARTS = {'private', 'explorer', 'source', 'plotting-deps', '__pycache__',
                  '.git', '.venv', 'fixture-evidence', 'fixture-evidence-2'}
PATTERNS = {
    'provider token': rb'\b(?:sk-(?:or-v1-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|AKIA[A-Z0-9]{16})\b',
    'private key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'bearer credential': rb'(?i)\bBearer\s+[A-Za-z0-9_.-]{24,}',
    'JWT credential': rb'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\b',
}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def safe_relative(value):
    require(isinstance(value, str) and value and '\\' not in value, 'Invalid bundle path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(p not in ('.', '..', '') for p in value.split('/')),
            'Unsafe bundle path')
    return Path(*path.parts)


def no_symlink(path, root):
    require(not any(p.is_symlink() for p in (path, *path.parents) if p != root and root in p.parents),
            'Symlink in research bundle or evidence')


def publishable(raw, name, secrets=()):
    # Report the rule and filename only, never candidate credential values.
    for pattern_name, pattern in PATTERNS.items():
        require(not re.search(pattern, raw), f'Credential candidate ({pattern_name}) in {name}; nothing published')
    require(not any(secret in raw for secret in secrets), f'Local credential found in {name}; nothing published')


def private_secrets(workspace):
    """Use local credentials only as exclusion sentinels; never export them."""
    values = set()
    def visit(value, key=''):
        if isinstance(value, dict):
            for k, v in value.items(): visit(v, k)
        elif isinstance(value, str) and any(k in key.lower() for k in ('token', 'password', 'secret', 'api_key')):
            if len(value) >= 16: values.add(value.encode())
    private = workspace / 'private'
    if private.exists():
        for p in private.rglob('*'):
            if p.is_file() and not p.is_symlink() and p.stat().st_size < 100_000:
                raw = p.read_bytes().strip()
                try: visit(json.loads(raw))
                except (ValueError, UnicodeDecodeError):
                    if 16 <= len(raw) <= 4096: values.add(raw)
    return values


def evidence_files(workspace):
    """Select journals, research sidecars and frozen local code, not vendor trees."""
    selected = set()
    for p in workspace.rglob('*'):
        rel = p.relative_to(workspace)
        if EXCLUDED_PARTS.intersection(rel.parts) or any(s.startswith('.') for s in rel.parts): continue
        if p.suffix in ('.json', '.jsonl', '.md') or (p.suffix == '.py' and
                {'frozen-source', 'software-audit-snapshot'}.intersection(rel.parts)):
            no_symlink(p, workspace)
            if p.is_file(): selected.add(p)
    # Extensionless content-addressed legacy transcripts and supplements.
    for p in workspace.glob('*/manifest.json'):
        if p.parent.name in EXCLUDED_PARTS: continue
        doc = json.loads(p.read_bytes())
        if doc.get('schema') == 'behaviorlab.legacy/1':
            from .legacy import verify_corpus
            verify_corpus(p.parent)
            for row in doc['runs'] + doc['supplements']:
                blob = p.parent / 'blobs' / row['sha256']
                no_symlink(blob, workspace)
                selected.add(blob)
    return sorted(selected)


def export_notebook(path):
    require(path.is_file(), 'Research notebook is missing')
    # A SQLite backup includes a consistent transaction snapshot, including WAL.
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as source, sqlite3.connect(':memory:') as snapshot:
        source.backup(snapshot)
        require(snapshot.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Notebook integrity check failed')
        tables = {}
        for name, sql in snapshot.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            require(re.fullmatch(r'[a-z_]+', name), 'Unsupported notebook table name')
            columns = [r[1] for r in snapshot.execute(f'PRAGMA table_info("{name}")')]
            rows = [list(row) for row in snapshot.execute(f'SELECT * FROM "{name}" ORDER BY rowid')]
            tables[name] = {'name': name, 'sql': sql, 'columns': columns, 'rows': rows}
        return tables


def restore_notebook(tables, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists() and not path.is_symlink(), 'Refusing to replace a notebook')
    with sqlite3.connect(path) as db:
        for name, table in tables.items():
            require(re.fullmatch(r'[a-z_]+', name) and table['name'] == name, 'Invalid notebook table')
            require(re.match(r'^CREATE TABLE\s+' + re.escape(name) + r'\s*\(', table['sql'], re.I), 'Unsupported notebook schema')
            db.execute(table['sql'])
            columns = [r[1] for r in db.execute(f'PRAGMA table_info("{name}")')]
            require(columns == table['columns'], 'Notebook columns differ')
            placeholders = ','.join('?' for _ in columns)
            db.executemany(f'INSERT INTO "{name}" VALUES ({placeholders})', table['rows'])
        require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Restored notebook is invalid')
    path.chmod(0o600)


def portable_run(run, workspace):
    """A readable projection, retaining all visible and recorded reasoning text."""
    result = {k: v for k, v in run.items() if k not in ('_search', '_metadata_search', 'messages', 'source', 'probes')}
    source = dict(run['source'])
    relative = Path(source.pop('path')).resolve().relative_to(workspace.resolve()).as_posix()
    source['workspace_path'] = relative
    result['source'] = source
    # Display grouping in older loaders depends on the workspace folder's name.
    if result.get('collection_id') == 'lab':
        parts = PurePosixPath(relative).parts
        result['collection'] = parts[-2] if len(parts) > 1 else parts[-1]
    result['messages'] = [{k: v for k, v in m.items() if k not in ('request', 'raw_response', 'raw_record')}
                          for m in run['messages']]
    result['probes'] = [dict(p, path=Path(p['path']).resolve().relative_to(workspace.resolve()).as_posix())
                        for p in run.get('probes', [])]
    return result


def inventory(catalog):
    counts = Counter(r['kind'] for r in catalog.runs.values())
    return {'records': len(catalog.runs), 'by_kind': dict(counts),
            'default_records': sum(r['kind'] != 'synthetic' and not r.get('unstarted_assessment') for r in catalog.runs.values()),
            'assessment_screens': len(catalog.assessments), 'probe_batches': len(catalog.probes)}


def verify_bundle(bundle):
    bundle = Path(bundle).resolve()
    no_symlink(bundle / 'manifest.json', bundle)
    manifest = json.loads((bundle / 'manifest.json').read_bytes())
    require(manifest.get('schema') == SCHEMA, 'Unsupported research bundle')
    require(manifest['bundle_sha256'] == fingerprint({k: v for k, v in manifest.items() if k != 'bundle_sha256'}), 'Bundle manifest changed')
    listed = set()
    for item in manifest['files']:
        relative = safe_relative(item['path']); path = bundle / relative
        require(item['path'] not in listed, 'Duplicate bundle path')
        listed.add(item['path'])
        no_symlink(path, bundle)
        raw = path.read_bytes()
        require(len(raw) == item['bytes'] and sha256(raw) == item['sha256'], 'Changed bundle file: ' + item['path'])
    actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    require(actual == listed | {'manifest.json'}, 'Unlisted or missing bundle files')
    for name in manifest['notebook_rows']:
        require(re.fullmatch(r'[a-z_]+', name) and 'notebook/' + name + '.json' in listed,
                'Invalid notebook table reference')
    for run in json.loads((bundle / 'catalog.json').read_bytes())['runs']:
        require(run['evidence'] in listed and run['transcript'] in listed, 'Missing catalog source reference')
    return manifest


def compare_catalog(catalog, bundle, manifest):
    require(inventory(catalog) == manifest['inventory'], 'Restored catalog inventory differs')
    expected = {r['id']: r for r in json.loads((bundle / 'catalog.json').read_bytes())['runs']}
    require(set(catalog.runs) == set(expected), 'Restored conversation IDs differ')
    for identity, run in catalog.runs.items():
        require(fingerprint(portable_run(run, catalog.workspace)) == expected[identity]['projection_sha256'],
                'Restored transcript differs: ' + identity)
    issues = [{'workspace_path': Path(i['source']).resolve().relative_to(catalog.workspace).as_posix(), 'reason': i['reason']}
              for i in catalog.issues]
    require(issues == manifest['catalog_issues'], 'Restored source diagnostics differ')


def restore_bundle(bundle, destination):
    bundle = Path(bundle).resolve(); destination = Path(destination).absolute()
    require(not destination.exists() and not destination.is_symlink(), 'Restore destination already exists; choose a new directory')
    manifest = verify_bundle(bundle)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.restore-research-', dir=destination.parent))
    try:
        for item in manifest['files']:
            if item['category'] != 'original_evidence': continue
            target = staging / safe_relative(item['workspace_path'])
            require(not {'private', 'explorer'}.intersection(target.relative_to(staging).parts), 'Forbidden evidence destination')
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = (bundle / safe_relative(item['path'])).read_bytes()
            require(sha256(raw) == item['sha256'], 'Bundle changed during restore')
            with target.open('xb') as out: out.write(raw)
        tables = {name: json.loads((bundle / 'notebook' / (name + '.json')).read_bytes())
                  for name in manifest['notebook_rows']}
        restore_notebook(tables, staging / 'explorer' / 'notes.sqlite')
        require(export_notebook(staging / 'explorer' / 'notes.sqlite') == tables, 'Restored notebook rows differ')
        from .explorer import Catalog
        compare_catalog(Catalog(staging), bundle, manifest)
        # Do not merge with or overwrite a live workspace, even if it appeared meanwhile.
        require(not destination.exists() and not destination.is_symlink(), 'Restore destination appeared during verification')
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return {'destination': str(destination), 'bundle_sha256': manifest['bundle_sha256'],
            'inventory': manifest['inventory'], 'notebook_rows': manifest['notebook_rows']}


def export_bundle(workspace, output):
    workspace = Path(workspace).resolve(); output = Path(output).absolute()
    require(workspace.is_dir() and not output.exists() and not output.is_symlink(), 'Use an existing workspace and a new bundle directory')
    require(workspace not in output.resolve().parents and output.resolve() not in workspace.parents, 'Bundle must be outside the workspace')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.export-research-', dir=output.parent))
    files = []; sentinels = private_secrets(workspace)
    def write(relative, raw, category, **extra):
        publishable(raw, relative, sentinels)
        target = staging / safe_relative(relative); target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as out: out.write(raw)
        files.append(dict(path=relative, bytes=len(raw), sha256=sha256(raw), category=category, **extra))
    try:
        from .explorer import Catalog
        catalog = Catalog(workspace)
        for path in evidence_files(workspace):
            relative = path.relative_to(workspace).as_posix(); raw = path.read_bytes()
            write('evidence/' + relative, raw, 'original_evidence', workspace_path=relative)
        tables = export_notebook(workspace / 'explorer' / 'notes.sqlite')
        readable = {}
        for name, table in tables.items():
            write('notebook/' + name + '.json', json_bytes(table), 'notebook_table')
            if 'body' in table['columns']:
                index = table['columns'].index('body')
                readable[name] = [json.loads(row[index]) for row in table['rows']]
        write('notebook/readable.json', json_bytes(readable), 'notebook_readable')
        runs = []
        for identity, run in sorted(catalog.runs.items()):
            require(re.fullmatch(r'[a-zA-Z0-9_-]+', identity), 'Unsafe conversation ID')
            doc = portable_run(run, workspace); relative = 'transcripts/' + identity + '.json'
            write(relative, json_bytes(doc), 'transcript_projection')
            source = doc['source']['workspace_path']
            raw_source = source + ('/blobs/' + run['source']['sha256'] if run['kind'] == 'reference' else '/events.jsonl')
            runs.append(dict(id=identity, title=run['title'], kind=run['kind'], data_class=run['data_class'],
                             transcript=relative, evidence='evidence/' + raw_source,
                             source_sha256=run['source']['sha256'], projection_sha256=fingerprint(doc)))
        write('catalog.json', json_bytes({'schema': SCHEMA, 'runs': runs}), 'catalog')
        write('README.md', ("# Research snapshot\n\nOriginal transcripts are core research entities.\n\n"
            "- `transcripts/`: readable conversations, prompts, settings, all recorded visible/thinking text and message IDs.\n"
            "- `evidence/`: unchanged original journals, raw requests/responses, imported source bytes and research sidecars.\n"
            "- `catalog.json`: maps conversation IDs to readable files and authoritative sources.\n"
            "- `notebook/readable.json`: notes, collections, findings, topic definitions/reviews, musings and all histories.\n"
            "- Other `notebook/*.json`: exact table schemas and row values for restoration, including deleted entries.\n\n"
            "Readable transcripts omit duplicated raw request/response/record fields; these remain in original evidence. "
            "Synthetic and unstarted records retain their labels. Historical host paths and local WebUI links are provenance, "
            "not portable execution credentials or a promise that a closed experiment can be rerun.\n\n"
            "Restore offline into a NEW directory: `python3 -m behaviorlab.research_bundle restore --bundle research --destination workspace`. "
            "Then run `python3 -m behaviorlab explore --workspace workspace`. No model calls are made. "
            "Restore refuses to overwrite an existing workspace. See `docs/RESEARCH-DATA.md` for scope and updates.\n").encode(), 'guide')
        # Catch source changes during export instead of silently publishing a mixed snapshot.
        for item in files:
            if item['category'] == 'original_evidence':
                require(sha256((workspace / item['workspace_path']).read_bytes()) == item['sha256'], 'Evidence changed during export')
        manifest = {'schema': SCHEMA, 'created_at': datetime.now(timezone.utc).isoformat(),
                    'inventory': inventory(catalog), 'files': files,
                    'notebook_rows': {name: len(table['rows']) for name, table in tables.items()},
                    'catalog_issues': [{'workspace_path': Path(i['source']).resolve().relative_to(workspace).as_posix(), 'reason': i['reason']} for i in catalog.issues],
                    'excluded': ['credentials/private files', 'SQLite indexes, live database and prior backups (current notebook exported separately)',
                                 'vendor source/dependencies', 'locks, caches, logs and disposable test fixtures'],
                    'secret_review': 'Known local credential sentinels plus token/private-key patterns; export fails on candidates; no source redaction.'}
        manifest['bundle_sha256'] = fingerprint(manifest)
        publishable(json_bytes(manifest), 'manifest.json', sentinels)
        (staging / 'manifest.json').write_bytes(json_bytes(manifest))
        verify_bundle(staging)
        # A full reindex proves the selected originals suffice before publication.
        with tempfile.TemporaryDirectory(prefix='lab-snapshot-check-') as temp:
            restore_bundle(staging, Path(temp) / 'workspace')
        require(not output.exists() and not output.is_symlink(), 'Bundle destination appeared during verification')
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return {'bundle': str(output), 'bundle_sha256': manifest['bundle_sha256'],
            'inventory': manifest['inventory'], 'files': len(files), 'bytes': sum(f['bytes'] for f in files),
            'notebook_rows': manifest['notebook_rows']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    export = sub.add_parser('export'); export.add_argument('--workspace', default='workspace'); export.add_argument('--output', required=True)
    restore = sub.add_parser('restore'); restore.add_argument('--bundle', default='research'); restore.add_argument('--destination', default='workspace')
    verify = sub.add_parser('verify'); verify.add_argument('--bundle', default='research')
    args = parser.parse_args(argv)
    if args.command == 'export': result = export_bundle(args.workspace, args.output)
    elif args.command == 'restore': result = restore_bundle(args.bundle, args.destination)
    else:
        m = verify_bundle(args.bundle)
        result = {'bundle_sha256': m['bundle_sha256'], 'files': len(m['files']), 'inventory': m['inventory']}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
