"""Offline full-ancestry and speaker audit for the prepared JEV corpus; no inference."""
import argparse
from collections import Counter
from pathlib import Path

from behaviorlab.common import fingerprint, require
from behaviorlab.explorer import Catalog
from behaviorlab.jev_atlas import now, read_record, write_record
from behaviorlab.jev_coverage import build_inventory


def audit(catalog, inventory):
    current, _ = build_inventory(catalog)
    require(fingerprint(current) == inventory['sha256'], 'Corpus differs from frozen inventory')
    rows = []
    for run in catalog.runs.values():
        if run['kind'] == 'synthetic': continue
        ms = run['messages']; by_id = {m['id']: m for m in ms}
        branched = any(m.get('parent') for m in ms)
        for n, m in enumerate(ms):
            if m.get('kind') != 'message' or m.get('speaker') not in ('X', 'Y', 'Z') or not m.get('text'): continue
            if branched:
                prior = []; parent = m.get('parent'); seen = {m['id']}
                while parent:
                    require(parent in by_id and parent not in seen, 'Invalid ancestry')
                    seen.add(parent); ancestor = by_id[parent]; prior.append(ancestor); parent = ancestor.get('parent')
            else: prior = ms[:n]
            target_ok = m['status'] in ('valid', 'recorded')
            flags = Counter(p.get('status') for p in prior if p.get('status') not in ('valid', 'recorded', 'intervention'))
            absent = sum(not p.get('text') for p in prior)
            rows.append({'item_id': fingerprint([run['id'], m['id']])[:24], 'run_id': run['id'],
                'message_id': m['id'], 'source_sha256': run['source']['sha256'],
                'speaker': m['speaker'], 'speaker_model': m.get('model'), 'data_class': run['data_class'],
                'target_status': m['status'], 'preceding_events_on_actual_path': len(prior),
                'prior_status_flags': dict(flags), 'prior_unavailable_events': absent,
                'clean_observed_history': target_ok and not flags and absent == 0})
    expected = {t['id'] for t in inventory['targets'] if t['visible']}
    require({r['item_id'] for r in rows} == expected and len(rows) == len(expected), 'Scope audit must cover every visible target exactly once')
    return {'schema': 'behaviorlab.jev-corpus-scope-audit/1', 'at': now(), 'author': 'Codex',
        'inventory_sha256': inventory['sha256'], 'targets': rows,
        'counts': {'visible_targets': len(rows), 'clean_observed_history': sum(r['clean_observed_history'] for r in rows),
            'flagged_or_incomplete_history': sum(not r['clean_observed_history'] for r in rows),
            'speaker_model_missing': sum(not r['speaker_model'] for r in rows),
            'data_classes': dict(Counter(r['data_class'] for r in rows)),
            'speaker_models': dict(Counter(r['speaker_model'] or 'Unknown' for r in rows))},
        'method': 'All preceding evidence events on the actual parent path, not only the two-event classifier context. '
                  'Clean means recorded/valid target and no missing or flagged prior event in the saved projection; '
                  'it does not establish historical runtime validity. Speaker attribution comes from each message, not the conversation model set.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--workspace', default='workspace')
    p.add_argument('--inventory', required=True); p.add_argument('--output', required=True); a = p.parse_args()
    result = audit(Catalog(a.workspace), read_record(a.inventory)); write_record(Path(a.output), result)
    import json
    print(json.dumps(result['counts'], indent=2))
