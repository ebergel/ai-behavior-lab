"""Publication check: run from a clean repo copy with no workspace.

Pass the original project root as argv[1]. Reads under it and network access
are blocked. Expected atlas/Finder counts belong to the 2026-09-16 snapshot.
"""
import json
import os
from pathlib import Path
import sys

root = Path.cwd()
forbidden = Path(sys.argv[1]).resolve()
attempts = []
def audit(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo'):
        attempts.append(event)
        raise AssertionError('Network access forbidden during offline restore')
    if event in ('open', 'os.listdir', 'os.scandir', 'sqlite3.connect') and args and isinstance(args[0], (str, bytes, os.PathLike)):
        p = Path(os.fsdecode(args[0])).absolute()
        if p == forbidden or forbidden in p.parents:
            attempts.append(event)
            raise AssertionError('Original project access forbidden')
sys.addaudithook(audit)
sys.path.insert(0, str(root))

from behaviorlab.research_bundle import restore_bundle, export_notebook, verify_bundle
from behaviorlab.explorer import Catalog, Notes
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.topic_flags import TopicFlags
from behaviorlab.topic_atlas import TopicAtlas
from behaviorlab.finder import finder_result
from behaviorlab.common import fingerprint

bundle = root/'research'; destination = root/'workspace'
receipt = restore_bundle(bundle, destination)
c = Catalog(destination); n = Notes(destination/'explorer/notes.sqlite')
studies = ResearchCollections(n); atlas = TopicAtlas(n)
manifest = verify_bundle(bundle)
tables = {name:json.loads((bundle/'notebook'/(name+'.json')).read_bytes()) for name in manifest['notebook_rows']}
assert export_notebook(n.path)==tables

checked_spans = 0
def span(item, run_id=None):
    global checked_spans
    r = c.runs[run_id or item['run_id']]
    if 'source_sha256' in item: assert item['source_sha256']==r['source']['sha256']
    if item.get('message_id'):
        m = next(m for m in r['messages'] if m['id']==item['message_id'])
        assert m['text'][item['start']:item['end']]==item['quote']
        checked_spans += 1

for note in n.all(): span(note)
findings = 0
for study in studies.all():
    for member in study['runs']: assert member['run_id'] in c.runs
    d = studies.detail(study['id'], c)
    for f in d['collection']['findings']:
        findings += 1
        for e in f['evidence']:
            assert e['source_current']; span(e)
for f in TopicFlags(n).all(c):
    assert f['source_current']; span(f)
for r in atlas.reviews(c):
    assert r['source_current'] and r['dictionary_current']
    if r['choice']:
        for key in ('proposal','uptake'): span(r['choice'][key], r['run_id'])
analysis = atlas.analyze(c,studies,topic='consciousness')
finder = finder_result(c, {'models':['anthropic/claude-haiku-4.5'], 'topics':['consciousness']}, studies, topic_atlas=atlas)
assert finder['total']==4
assert analysis['denominators']['runs']==438
assert analysis['denominators']['visible_messages']==11204
assert analysis['denominators']['opening_reviews_resolved']==12
assert next(r for r in analysis['rows'] if r['id']=='consciousness')['run_hits']==204
assert not attempts
result = dict(receipt, source_project_access='blocked by Python audit hook', network_access='blocked by Python audit hook',
              attempted_forbidden_operations=len(attempts), notebook_exact_tables=len(tables),
              notebook_sha256=fingerprint(tables), collections=len(studies.all()), findings=findings,
              exact_spans_checked=checked_spans, atlas_denominators=analysis['denominators'],
              atlas_topic_counts=analysis['rows'], finder_haiku_consciousness=finder['total'])
print(json.dumps({k:v for k,v in result.items() if k!='atlas_topic_counts'},indent=2))
