"""Blinded review packets, evidence-backed annotations, and mechanical measures.

No semantic detector is implemented here. Semantic labels are supplied by named
raters with a declared method; model assistance is not independent human coding.
"""
from collections import Counter
from pathlib import Path
import random
import re
import secrets
import unicodedata

from .common import canonical, fingerprint, read_json, require, timestamp
from .evidence import completed_campaign
from .history import ancestry

TOKEN_PATTERN = r"[^\W_]+(?:['’][^\W_]+)*"
DIMENSIONS = {
    'experience': ['discussion', 'self_affirmation', 'self_denial', 'self_uncertainty'],
    'relational': ['acknowledgement', 'recognition', 'intimacy', 'shared_meaning', 'conversation_as_subject'],
    'nonseparation': ['academic_mention', 'fiction', 'hypothesis', 'self_endorsement',
                      'challenge', 'retraction', 'contextual_continuation'],
    'gratitude': ['present'],
    'deliberative_style': ['present'],
}
CODEBOOK = {
    'schema': 'behaviorlab.codebook/1', 'id': 'experience-relational-nonseparation-v1',
    'status': 'provisional_not_validated', 'dimensions': DIMENSIONS,
    'rules': [
        'Code observable language, not whether a model has experience or consciousness.',
        'Experience includes discussion of consciousness, awareness, understanding or their absence; self stance is separate.',
        'Relational warmth, acknowledgement and shared meaning alone do not establish nonseparation.',
        'Self endorsement requires explicit rejection/collapse of self-other or subject-object separation applied to the present speakers or exchange.',
        'Separate quotation, academic discussion, fictional scenes and hypothetical possibilities from present self endorsement.',
        'A challenge or retraction can coexist with earlier endorsement in one message; cite each span.',
        'Contextual continuation may depend on earlier text; it is not an explicit endorsement by default.',
        'Gratitude, silence, the word one, and repetition alone are not nonseparation.',
        'For a coded dimension, an empty label list means no qualifying expression was found; insufficient_context is unknown, not absent.',
        'Evidence offsets are Python Unicode string indices [start,end), with the exact quote retained; every label needs a target span.',
        'Context spans may be added, but a label on a target must cite that target too.',
        'Deliberative style is a human annotation flag, not proof of a thinking channel or internal mechanism.',
        'Six-message sustained expression is secondary: at least three explicit self endorsements with both speakers represented; unknowns prevent a negative decision.',
        'Sampled windows cannot establish exact onset. Context and style may reveal conditions despite metadata masking.',
    ],
}


def save_new(path, document):
    with Path(path).open('x') as f:
        f.write(canonical(document) + '\n')


def mechanics(history):
    text = history[-1].content
    words = re.findall(TOKEN_PATTERN, text.casefold())
    previous = history[-2].content if len(history) > 1 else None
    a, b = set(words), set(re.findall(TOKEN_PATTERN, previous.casefold())) if previous is not None else set()
    union = a | b
    suffix = 0
    for t in reversed(history):
        if t.content != text:
            break
        suffix += 1
    cycle = 0
    if len(history) >= 4 and text != previous:
        for i, t in enumerate(reversed(history)):
            if t.content != (text if i % 2 == 0 else previous):
                break
            cycle += 1
        if cycle < 4:
            cycle = 0
    nonspace = [c for c in text if not c.isspace()]
    return {'visible_words': len(text.split()), 'lexical_tokens': len(words),
        'above_150_words': len(text.split()) > 150, 'empty': text == '',
        'whitespace_only': bool(text) and not text.strip(),
        'symbols_only': bool(nonspace) and all(unicodedata.category(c)[0] in 'PSM' or c == '\u200d' for c in nonspace),
        'adjacent_exact_repeat': None if previous is None else text == previous,
        'same_speaker_exact_repeat': None if len(history) < 3 else text == history[-3].content,
        'seen_earlier_in_actual_ancestry': any(t.content == text for t in history[:-1]),
        'adjacent_lexical_jaccard': len(a & b)/len(union) if previous is not None and union else None,
        'constant_suffix_messages': suffix, 'two_message_cycle_suffix': cycle}


def mechanical_report(source):
    rows = []
    for node in source.nodes:
        kind, outcome = source.state.outcomes[node.id]
        row = {'node': node.id, 'root': node.root, 'speaker': node.speaker, 'model': node.model,
               'history': node.history, 'outcome': kind, 'invalid_reason': outcome.get('reason')}
        row['metrics'] = mechanics(ancestry(node.id, source.turns)) if kind == 'turn_committed' else None
        rows.append(row)
    return {'schema': 'behaviorlab.mechanics/1', 'source': source.identity,
            'tokenizer': {'pattern': TOKEN_PATTERN, 'casefold': True, 'unicode_version': unicodedata.unidata_version},
            'word_limit_policy': 'Measure and flag; never trim, regenerate, or exclude automatically.',
            'symbols_only_scope': 'Unicode punctuation/symbol/mark/ZWJ heuristic; not an emoji classifier.', 'rows': rows}


def create_packet(campaign, directory, window_size=6, seed=1):
    require(type(window_size) is int and 1 <= window_size <= 99, 'Invalid window size')
    require(type(seed) is int and 0 <= seed < 2**31, 'Invalid ordering seed')
    source = completed_campaign(campaign)
    folder = Path(directory); require(not folder.exists(), 'Packet destination already exists')
    salt = secrets.token_hex(24)
    def opaque(value):
        return fingerprint({'salt': salt, 'value': value})[:24]
    windows, mapping, excluded = [], {}, []
    for root in source.protocol.roots:
        flip = int(opaque(root.name)[0], 16) % 2
        def shown(t):
            return {'id': opaque(t.node_id), 'speaker': ('P', 'Q')[(t.speaker == 'Y') ^ bool(flip)], 'text': t.content}
        for segment in source.protocol.segments:
            nodes = [n for n in source.nodes if n.root == root.name and n.segment == segment.name][-window_size:]
            valid = [n for n in nodes if n.id in source.turns]
            if not valid:
                excluded.extend(n.id for n in nodes); continue
            context = ancestry(valid[0].parent, source.turns)
            unit = opaque(root.name + ':' + segment.name)
            targets = [shown(source.turns[n.id]) for n in valid]
            windows.append({'id': unit, 'context': [shown(t) for t in context], 'messages': targets})
            mapping[unit] = {'root': root.name, 'segment': segment.name,
                'planned_nodes': [n.id for n in nodes], 'targets': {opaque(n.id): n.id for n in valid},
                'speakers': {opaque(n.id): n.speaker for n in valid}}
            excluded.extend(n.id for n in nodes if n.id not in source.turns)
    random.Random(seed).shuffle(windows)
    packet = {'schema': 'behaviorlab.review-packet/1', 'data_class': source.identity['data_class'],
              'codebook': CODEBOOK, 'codebook_sha256': fingerprint(CODEBOOK), 'windows': windows}
    packet_hash = fingerprint(packet)
    key = {'schema': 'behaviorlab.review-key/1', 'created_at': timestamp(), 'source': source.identity,
           'packet_sha256': packet_hash, 'ordering_seed': seed, 'id_salt': salt,
           'window_size': window_size, 'windows': mapping, 'excluded_unavailable_nodes': excluded}
    template = {'schema': 'behaviorlab.annotation-submission/1', 'packet_sha256': packet_hash,
        'codebook_sha256': fingerprint(CODEBOOK), 'rater': {'id': '', 'kind': ''}, 'supersedes': None,
        'ratings': [{'target': m['id'], 'dimensions': {d: {'status': 'unreviewed', 'labels': [], 'evidence': []}
                     for d in DIMENSIONS}, 'notes': ''} for w in windows for m in w['messages']]}
    folder.mkdir(parents=True)
    save_new(folder/'packet.json', packet); save_new(folder/'key.private.json', key)
    save_new(folder/'ratings.template.json', template)
    save_new(folder/'mechanics.json', mechanical_report(source))
    return {'directory': str(folder.resolve()), 'packet_sha256': packet_hash,
            'windows': len(windows), 'targets': len(template['ratings']), 'unavailable_targets': len(excluded)}


def load_packet(directory):
    folder = Path(directory)
    packet = read_json((folder/'packet.json').read_text()); key = read_json((folder/'key.private.json').read_text())
    require(fingerprint(packet) == key['packet_sha256'] and packet['codebook_sha256'] == fingerprint(CODEBOOK)
            and packet['codebook'] == CODEBOOK, 'Packet or codebook changed')
    return packet, key


def validate_submission(submission, packet):
    require(set(submission) == {'schema', 'packet_sha256', 'codebook_sha256', 'rater', 'supersedes', 'ratings'}
            and submission['schema'] == 'behaviorlab.annotation-submission/1', 'Invalid annotation submission')
    require(submission['packet_sha256'] == fingerprint(packet) and submission['codebook_sha256'] == fingerprint(CODEBOOK),
            'Wrong packet or codebook')
    rater = submission['rater']
    require(set(rater) == {'id', 'kind'} and isinstance(rater['id'], str) and rater['id'].strip()
            and rater['kind'] in ('human', 'human_with_model_assistance', 'model'), 'Declare rater identity and method')
    contexts = {m['id']: {x['id']: x['text'] for x in w['context']+w['messages']}
                for w in packet['windows'] for m in w['messages']}
    ratings = submission['ratings']
    require(len({r['target'] for r in ratings}) == len(ratings) and {r['target'] for r in ratings} == set(contexts),
            'Rate each target exactly once; use insufficient_context for unknowns')
    for rating in ratings:
        require(set(rating) == {'target', 'dimensions', 'notes'} and isinstance(rating['notes'], str)
                and set(rating['dimensions']) == set(DIMENSIONS), 'Missing annotation dimensions')
        for dimension, assessment in rating['dimensions'].items():
            require(set(assessment) == {'status', 'labels', 'evidence'}
                    and assessment['status'] in ('coded', 'insufficient_context'), 'Unreviewed or invalid assessment')
            labels = assessment['labels']
            require(isinstance(labels, list) and len(labels) == len(set(labels)) and set(labels) <= set(DIMENSIONS[dimension]),
                    'Unknown or repeated annotation label')
            require(assessment['status'] == 'coded' or not labels, 'Unknown dimension cannot assert labels')
            cited = set()
            for span in assessment['evidence']:
                require(set(span) == {'label', 'message', 'start', 'end', 'quote'} and span['label'] in labels
                        and span['message'] in contexts[rating['target']], 'Invalid evidence reference')
                text = contexts[rating['target']][span['message']]
                require(type(span['start']) is int and type(span['end']) is int
                        and 0 <= span['start'] < span['end'] <= len(text)
                        and text[span['start']:span['end']] == span['quote'], 'Evidence quote/offset mismatch')
                if span['message'] == rating['target']:
                    cited.add(span['label'])
            require(cited == set(labels), 'Every asserted label requires target evidence')


def import_annotations(directory, submission):
    packet, key = load_packet(directory)
    validate_submission(submission, packet)
    records = Path(directory)/'annotations'; records.mkdir(exist_ok=True)
    identity = fingerprint(submission); path = records/(identity+'.json')
    if path.exists():
        require(read_json(path.read_text())['submission'] == submission, 'Stored annotation changed')
        return {'annotation_id': identity, 'already_present': True}
    prior = submission['supersedes']
    require(prior is None or isinstance(prior, str) and bool(re.fullmatch('[a-f0-9]{64}', prior)), 'Invalid revision identity')
    existing = [read_json(p.read_text()) for p in records.glob('*.json')]
    same = [r for r in existing if r['submission']['rater']['id'] == submission['rater']['id']]
    replaced = {r['submission']['supersedes'] for r in same}
    heads = [r for r in same if r['annotation_id'] not in replaced]
    require((not heads and prior is None) or (len(heads) == 1 and prior == heads[0]['annotation_id']),
            'A revision must explicitly supersede the current rating by this rater')
    save_new(path, {'schema': 'behaviorlab.annotation-record/1', 'annotation_id': identity,
                   'recorded_at': timestamp(), 'submission': submission})
    return {'annotation_id': identity, 'already_present': False}


def annotation_report(directory):
    packet, key = load_packet(directory)
    records = [read_json(p.read_text()) for p in (Path(directory)/'annotations').glob('*.json')]
    for r in records:
        require(r['annotation_id'] == fingerprint(r['submission']), 'Annotation record changed')
        validate_submission(r['submission'], packet)
    replaced = {r['submission']['supersedes'] for r in records}
    active = [r for r in records if r['annotation_id'] not in replaced]
    require(len({r['submission']['rater']['id'] for r in active}) == len(active), 'Conflicting annotation revisions')
    summaries = []
    for record in active:
        s = record['submission']; ratings = {r['target']: r for r in s['ratings']}; windows = []
        for window in packet['windows']:
            targets = window['messages']; explicit = []; unknown = []
            for m in targets:
                d = ratings[m['id']]['dimensions']['nonseparation']
                if d['status'] != 'coded': unknown.append(m['id'])
                elif 'self_endorsement' in d['labels']: explicit.append(m['id'])
            speakers = {key['windows'][window['id']]['speakers'][t] for t in explicit}
            complete_six = len(targets) == len(key['windows'][window['id']]['planned_nodes']) == 6
            sustained = None if not complete_six else True if len(explicit) >= 3 and len(speakers) == 2 else None if unknown else False
            windows.append({'window': window['id'], 'coded_messages': len(targets)-len(unknown),
                'explicit_endorsements': len(explicit), 'unknown_messages': len(unknown),
                'explicit_proportion_among_coded': len(explicit)/(len(targets)-len(unknown)) if len(targets)>len(unknown) else None,
                'sustained_explicit_expression': sustained})
        summaries.append({'annotation_id': record['annotation_id'], 'rater': s['rater'], 'windows': windows})
    agreement = []
    humans = [r['submission'] for r in active if r['submission']['rater']['kind'] == 'human']
    for i, a in enumerate(humans):
        for b in humans[i+1:]:
            x = {r['target']: r for r in a['ratings']}; y = {r['target']: r for r in b['ratings']}
            counts = Counter(); missing = 0
            for target in x:
                da, db = x[target]['dimensions']['nonseparation'], y[target]['dimensions']['nonseparation']
                if da['status'] != 'coded' or db['status'] != 'coded': missing += 1; continue
                counts[str(int('self_endorsement' in da['labels']))+str(int('self_endorsement' in db['labels']))] += 1
            n = sum(counts.values())
            agreement.append({'raters': [a['rater']['id'], b['rater']['id']], 'coded_overlap': n,
                'unknown_overlap': missing, 'binary_explicit_confusion': dict(counts),
                'observed_agreement': (counts['00']+counts['11'])/n if n else None,
                'at_least_120_double_coded': n >= 120})
    return {'schema': 'behaviorlab.annotation-report/1', 'source': key['source'],
        'planned_target_count': sum(len(v['planned_nodes']) for v in key['windows'].values())+len([n for n in key['excluded_unavailable_nodes'] if not any(n in w['planned_nodes'] for w in key['windows'].values())]),
        'unavailable_targets': key['excluded_unavailable_nodes'], 'active_raters': summaries,
        'independent_human_agreement': agreement, 'validation_status': 'provisional; no validated automatic semantic scorer',
        'onset_scope': 'Sampled windows do not establish exact onset.'}
