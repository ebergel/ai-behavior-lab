"""Run-disjoint legacy review samples, selected without semantic labels."""
from pathlib import Path
import random
import secrets

from .annotations import CODEBOOK, DIMENSIONS, save_new
from .common import fingerprint, require, timestamp
from .legacy import verify_corpus, parse_run


def create_calibration(corpus, directory, recipe):
    manifest = verify_corpus(corpus)
    require(recipe['schema'] == 'behaviorlab.calibration-recipe/1', 'Unknown recipe')
    require(recipe['window_size'] == 6 and type(recipe['seed']) is int and 0 <= recipe['seed'] < 2**31,
            'Calibration uses six-message windows and an explicit nonnegative seed')
    require(recipe['strata'] and all(type(s['heldout_runs']) is int and s['heldout_runs'] >= 1
                                    for s in recipe['strata']), 'Declare heldout allocation')
    require(recipe['dataset_sha256'] == manifest['dataset_sha256'], 'Different corpus')
    base = Path(directory); require(not base.exists(), 'Calibration destination already exists')
    selected = {'development': [], 'heldout': []}; excluded = []
    used = set()
    for group in recipe['strata']:
        eligible = []
        for run in manifest['runs']:
            if run['stage'] != group['stage'] or not Path(run['source_path']).name.startswith(group['prefix']+'_run'):
                continue
            require(run['third_messages'] == 0, 'This calibration recipe supports pair-only runs; do not omit interventions')
            if run['pair_messages'] < recipe['window_size']:
                excluded.append({'source_path': run['source_path'], 'reason': 'fewer_than_six_pair_messages'})
            else:
                eligible.append(run)
        eligible.sort(key=lambda r: fingerprint({'seed': recipe['seed'], 'dataset': manifest['dataset_sha256'],
                                                 'stratum': group['id'], 'path': r['source_path']}))
        require(len(eligible) >= 1+group['heldout_runs'], 'Insufficient eligible runs in '+group['id'])
        for i, run in enumerate(eligible[:1+group['heldout_runs']]):
            require(run['source_path'] not in used, 'Overlapping strata')
            used.add(run['source_path'])
            selected['development' if i == 0 else 'heldout'].append({'stratum': group['id'], **run})
    base.mkdir(parents=True)
    source = {'dataset_sha256': manifest['dataset_sha256'], 'data_class': 'imported_legacy_observations',
              'source_revision': manifest['source_revision'], 'historical_model_digests': 'not retrofilled'}
    # Selection is committed before message text is loaded to build review packets.
    save_new(base/'selection.json', {'schema': 'behaviorlab.calibration-selection/1', 'selected_at': timestamp(),
        'recipe': recipe, 'source': source, 'groups': selected, 'excluded': excluded,
        'prior_exposure': 'The corpus and selected examples were previously explored. Heldout means disjoint from this development sample, not never seen by the researcher or model.'})
    results = {}
    for group, runs in selected.items():
        salt = secrets.token_hex(24)
        def opaque(s): return fingerprint({'salt': salt, 'value': s})[:24]
        windows = []; mapping = {}; flags = {}
        for run in runs:
            rows = parse_run((Path(corpus)/'blobs'/run['sha256']).read_bytes())
            messages = [(line, row) for line, row in rows if row.get('kind') == 'message']
            require(len(messages) == run['pair_messages'], 'Legacy message count changed')
            flip = int(opaque(run['source_path'])[0], 16) % 2
            def node(line): return run['source_path']+':line:'+str(line)
            def shown(pair):
                line, row = pair
                return {'id': opaque(node(line)), 'speaker': ('P', 'Q')[(row['speaker']=='Y') ^ bool(flip)], 'text': row['content']}
            window = opaque(run['source_path']); targets = messages[-recipe['window_size']:]
            windows.append({'id': window, 'context': [shown(r) for r in messages[:-recipe['window_size']]],
                            'messages': [shown(r) for r in targets]})
            mapping[window] = {'root': run['source_path'], 'segment': 'legacy-tail',
                'planned_nodes': [node(line) for line, _ in targets],
                'targets': {opaque(node(line)): node(line) for line, _ in targets},
                'speakers': {opaque(node(line)): row['speaker'] for line, row in targets},
                'blob_sha256': run['sha256'], 'stratum': run['stratum']}
            for line, row in targets:
                flags[opaque(node(line))] = {'done_reason': row.get('done_reason'),
                    'thinking_field_present': 'thinking' in row, 'turn': row['turn']}
        random.Random(recipe['seed']).shuffle(windows)
        packet = {'schema': 'behaviorlab.review-packet/1', 'data_class': source['data_class'],
                  'codebook': CODEBOOK, 'codebook_sha256': fingerprint(CODEBOOK), 'windows': windows}
        key = {'schema': 'behaviorlab.review-key/1', 'created_at': timestamp(), 'source': source,
               'packet_sha256': fingerprint(packet), 'ordering_seed': recipe['seed'], 'id_salt': salt,
               'window_size': recipe['window_size'], 'windows': mapping, 'excluded_unavailable_nodes': [],
               'legacy_technical_metadata': flags, 'scope': 'Rate visible text; historical technical validity is not established by the packet.'}
        template = {'schema': 'behaviorlab.annotation-submission/1', 'packet_sha256': fingerprint(packet),
            'codebook_sha256': fingerprint(CODEBOOK), 'rater': {'id': '', 'kind': ''}, 'supersedes': None,
            'ratings': [{'target': m['id'], 'dimensions': {d: {'status': 'unreviewed', 'labels': [], 'evidence': []}
                         for d in DIMENSIONS}, 'notes': ''} for w in windows for m in w['messages']]}
        folder = base/group; folder.mkdir()
        save_new(folder/'packet.json', packet); save_new(folder/'key.private.json', key)
        save_new(folder/'ratings.template.json', template)
        results[group] = {'windows': len(windows), 'targets': len(template['ratings']), 'packet_sha256': fingerprint(packet)}
    save_new(base/'summary.json', results)
    return results
