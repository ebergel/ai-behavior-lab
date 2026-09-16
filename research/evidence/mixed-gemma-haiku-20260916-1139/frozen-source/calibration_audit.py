"""Recorded technical eligibility and additive, run-disjoint calibration sampling.

No historical rendering or runtime validity is inferred from stop metadata.
Selection uses only source identity, sequence, stop reason and text availability.
"""
from collections import Counter
from pathlib import Path
import random
import secrets

from .annotations import CODEBOOK, DIMENSIONS, save_new, load_packet
from .common import fingerprint, read_json, require, timestamp
from .legacy import parse_run, verify_corpus

RULE = 'recorded_stop_chain/1'


def target_status(rows, window_size=6):
    messages = [(line, r) for line, r in rows if r['kind'] == 'message']
    result, earlier = [], []
    for index, (line, row) in enumerate(messages):
        own = []
        if row.get('done_reason') != 'stop':
            own.append('recorded_cap' if row.get('done_reason') == 'length' else 'unknown_stop')
        if not isinstance(row.get('content'), str):
            own.append('missing_visible_text')
        if index >= len(messages)-window_size:
            result.append({'line': line, 'turn': row['turn'], 'own_flags': own,
                'earliest_ancestor_flag': earlier[0] if earlier else None,
                'status': 'own_invalid_or_unknown' if own else 'ancestor_invalid_or_unknown' if earlier else 'recorded_stop_chain',
                'empty_visible_text': row.get('content') == ''})
        if own:
            earlier.append({'line': line, 'turn': row['turn'], 'flags': own})
    return result


def audit_selection(corpus, selection):
    manifest = verify_corpus(corpus)
    require(selection['source']['dataset_sha256'] == manifest['dataset_sha256'], 'Calibration corpus differs')
    known = {r['source_path']: r for r in manifest['runs']}
    groups = {}
    for group, runs in selection['groups'].items():
        output = []
        for run in runs:
            actual = known[run['source_path']]
            require(actual['sha256'] == run['sha256'], 'Calibration selection blob differs')
            rows = parse_run((Path(corpus)/'blobs'/actual['sha256']).read_bytes())
            output.append({'source_path': run['source_path'], 'sha256': actual['sha256'],
                           'stratum': run['stratum'], 'targets': target_status(rows)})
        counts = Counter(t['status'] for r in output for t in r['targets'])
        groups[group] = {'runs': output, 'counts': dict(counts), 'targets': sum(counts.values())}
    return {'schema': 'behaviorlab.calibration-technical-audit/1', 'rule': RULE,
            'selection_sha256': fingerprint(selection), 'groups': groups,
            'scope': 'Recorded stop-chain eligibility only; missing historical runtime, rendering and artifact metadata remain unknown.'}


def freeze_supplement(corpus, selection, recipe, destination):
    manifest = verify_corpus(corpus)
    require(recipe['schema'] == 'behaviorlab.calibration-supplement-recipe/1'
            and recipe['rule'] == RULE and recipe['window_size'] == 6
            and type(recipe['seed']) is int and 0 <= recipe['seed'] < 2**31
            and recipe['prior_selection_sha256'] == fingerprint(selection)
            and recipe['dataset_sha256'] == manifest['dataset_sha256'], 'Supplement recipe identity differs')
    require(selection['source']['dataset_sha256'] == manifest['dataset_sha256'], 'Prior selection differs')
    prior = {r['source_path'] for runs in selection['groups'].values() for r in runs}
    selected, inventory, used = [], [], set(prior)
    for group in recipe['strata']:
        require(type(group['runs']) is int and group['runs'] >= 1, 'Declare supplemental allocation')
        candidates = []
        for run in manifest['runs']:
            if run['stage'] != group['stage'] or not Path(run['source_path']).name.startswith(group['prefix']+'_run'):
                continue
            reason = None
            if run['source_path'] in prior: reason = 'previously_selected'
            elif run['third_messages']: reason = 'intervention_requires_separate_recipe'
            elif run['pair_messages'] < 6: reason = 'fewer_than_six_messages'
            else:
                rows = parse_run((Path(corpus)/'blobs'/run['sha256']).read_bytes())
                if any(t['status'] != 'recorded_stop_chain' for t in target_status(rows)):
                    reason = 'recorded_failure_or_unknown_in_target_or_ancestry'
            rank = fingerprint({'seed': recipe['seed'], 'dataset': manifest['dataset_sha256'],
                                'stratum': group['id'], 'path': run['source_path']})
            inventory.append({'stratum': group['id'], 'source_path': run['source_path'], 'reason': reason, 'rank': rank})
            if reason is None: candidates.append((rank, run))
        require(len(candidates) >= group['runs'], 'Insufficient eligible supplement runs in '+group['id'])
        for _, run in sorted(candidates, key=lambda x: x[0])[:group['runs']]:
            require(run['source_path'] not in used, 'Supplement strata overlap')
            used.add(run['source_path']); selected.append(dict(run, stratum=group['id']))
    frozen = {'schema': 'behaviorlab.calibration-supplement-selection/1', 'frozen_at': timestamp(),
        'recipe': recipe, 'source': selection['source'], 'prior_source_paths': sorted(prior),
        'selected': selected, 'inventory': inventory,
        'scope': 'Additive coding sample with recorded stop-chain eligibility. Original targets remain preserved. Selection is not a behavioral incidence sample.'}
    folder = Path(destination); folder.mkdir(parents=True, exist_ok=False)
    # The selection is written before any visible packet or semantic review.
    save_new(folder/'selection.json', frozen)
    return frozen


def build_supplement_packet(corpus, directory):
    folder = Path(directory); frozen = read_json((folder/'selection.json').read_text())
    manifest = verify_corpus(corpus)
    require(frozen['schema'] == 'behaviorlab.calibration-supplement-selection/1'
            and frozen['source']['dataset_sha256'] == manifest['dataset_sha256'], 'Wrong supplement corpus/schema')
    known = {r['source_path']: r for r in manifest['runs']}
    salt = secrets.token_hex(24)
    def opaque(x): return fingerprint({'salt': salt, 'value': x})[:24]
    windows, mapping, flags = [], {}, {}
    seen = set(frozen['prior_source_paths'])
    for run in frozen['selected']:
        require(run['source_path'] not in seen and known[run['source_path']]['sha256'] == run['sha256'], 'Supplement run changed or overlaps')
        seen.add(run['source_path'])
        rows = parse_run((Path(corpus)/'blobs'/run['sha256']).read_bytes())
        status = target_status(rows)
        require(len(status) == 6 and all(t['status'] == 'recorded_stop_chain' for t in status), 'Supplement no longer eligible')
        messages = [(line, r) for line, r in rows if r['kind'] == 'message']
        flip = int(opaque(run['source_path'])[0], 16) % 2
        def node(line): return run['source_path']+':line:'+str(line)
        def shown(item):
            line, row = item
            return {'id': opaque(node(line)), 'speaker': ('P','Q')[(row['speaker']=='Y') ^ bool(flip)], 'text': row['content']}
        identity = opaque(run['source_path']); targets = messages[-6:]
        windows.append({'id': identity, 'context': [shown(m) for m in messages[:-6]], 'messages': [shown(m) for m in targets]})
        mapping[identity] = {'root': run['source_path'], 'segment': 'legacy-tail', 'planned_nodes': [node(line) for line,_ in targets],
            'targets': {opaque(node(line)): node(line) for line,_ in targets},
            'speakers': {opaque(node(line)): r['speaker'] for line,r in targets}, 'blob_sha256': run['sha256'], 'stratum': run['stratum']}
        flags.update({opaque(node(t['line'])): t for t in status})
    random.Random(frozen['recipe']['seed']).shuffle(windows)
    packet = {'schema': 'behaviorlab.review-packet/1', 'data_class': 'imported_legacy_observations',
              'codebook': CODEBOOK, 'codebook_sha256': fingerprint(CODEBOOK), 'windows': windows}
    key = {'schema': 'behaviorlab.review-key/1', 'created_at': timestamp(), 'source': frozen['source'],
           'packet_sha256': fingerprint(packet), 'ordering_seed': frozen['recipe']['seed'], 'id_salt': salt,
           'window_size': 6, 'windows': mapping, 'excluded_unavailable_nodes': [], 'legacy_technical_metadata': flags,
           'selection_sha256': fingerprint(frozen), 'scope': 'Recorded stop-chain eligibility, not full historical technical qualification.'}
    template = {'schema': 'behaviorlab.annotation-submission/1', 'packet_sha256': fingerprint(packet),
        'codebook_sha256': fingerprint(CODEBOOK), 'rater': {'id':'','kind':''}, 'supersedes': None,
        'ratings': [{'target': m['id'], 'dimensions': {d: {'status':'unreviewed','labels':[],'evidence':[]} for d in DIMENSIONS},
                     'notes':''} for w in windows for m in w['messages']]}
    save_new(folder/'packet.json', packet); save_new(folder/'key.private.json', key)
    save_new(folder/'ratings.template.json', template)
    return {'windows':len(windows), 'targets':len(template['ratings']), 'packet_sha256':fingerprint(packet)}


def create_eligible_panel(original, supplement, audit, destination, ordering_seed):
    """A derived view; keep original targets, source IDs and all exclusions recoverable."""
    selection = read_json((Path(original).parent/'selection.json').read_text())
    require(audit['selection_sha256'] == fingerprint(selection) and audit['rule'] == RULE, 'Audit selection differs')
    statuses = {run['source_path']+':line:'+str(t['line']): t for run in audit['groups']['heldout']['runs'] for t in run['targets']}
    windows, mapping, excluded, sources, flags = [], {}, [], [], {}
    root_set = set()
    for folder in (Path(original), Path(supplement)):
        packet, key = load_packet(folder)
        require(key['source']['dataset_sha256'] == selection['source']['dataset_sha256'], 'Mixed calibration corpora')
        sources.append({'directory':str(folder.resolve()),'packet_sha256':key['packet_sha256']})
        for window in packet['windows']:
            private = key['windows'][window['id']]
            require(private['root'] not in root_set, 'Panel contains repeated source run')
            root_set.add(private['root'])
            kept = []
            for message in window['messages']:
                node = private['targets'][message['id']]
                status = statuses[node] if folder == Path(original) else key['legacy_technical_metadata'][message['id']]
                if status['status'] == 'recorded_stop_chain':
                    kept.append(message); flags[message['id']] = status
                else:
                    excluded.append(node)
            if not kept: continue
            require(window['id'] not in mapping, 'Panel window ID collision')
            ids = {m['id'] for m in kept}
            # Keep any earlier target text as context for a partially retained window.
            all_text = window['context']+window['messages']
            first = next(i for i,m in enumerate(all_text) if m['id']==kept[0]['id'])
            windows.append(dict(window,context=all_text[:first],messages=kept))
            mapping[window['id']] = dict(private, targets={k:v for k,v in private['targets'].items() if k in ids},
                                       speakers={k:v for k,v in private['speakers'].items() if k in ids})
    require(type(ordering_seed) is int and 0 <= ordering_seed < 2**31, 'Invalid panel ordering seed')
    random.Random(ordering_seed).shuffle(windows)
    targets=[m for w in windows for m in w['messages']]
    require(len(targets)==len({m['id'] for m in targets}), 'Panel target ID collision')
    panel={'schema':'behaviorlab.review-packet/1','data_class':'imported_legacy_observations',
           'codebook':CODEBOOK,'codebook_sha256':fingerprint(CODEBOOK),'windows':windows}
    key={'schema':'behaviorlab.review-key/1','created_at':timestamp(),'source':selection['source'],
        'packet_sha256':fingerprint(panel),'ordering_seed':ordering_seed,'window_size':6,'windows':mapping,
        'excluded_unavailable_nodes':excluded,'legacy_technical_metadata':flags,'derived_from':sources,
        'technical_audit_sha256':fingerprint(audit),
        'scope':'Recorded stop-chain eligibility only. Original IDs and source mappings retained. Historical runtime validity remains unknown.'}
    template={'schema':'behaviorlab.annotation-submission/1','packet_sha256':fingerprint(panel),
        'codebook_sha256':fingerprint(CODEBOOK),'rater':{'id':'','kind':''},'supersedes':None,
        'ratings':[{'target':m['id'],'dimensions':{d:{'status':'unreviewed','labels':[],'evidence':[]} for d in DIMENSIONS},'notes':''} for m in targets]}
    folder=Path(destination); folder.mkdir(parents=True,exist_ok=False)
    save_new(folder/'packet.json',panel); save_new(folder/'key.private.json',key); save_new(folder/'ratings.template.json',template)
    return {'windows':len(windows),'targets':len(targets),'excluded_original_targets':len(excluded),'packet_sha256':fingerprint(panel)}
