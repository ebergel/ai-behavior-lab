"""Read-only assessment matrices and separate, versioned analysis recipes.

No inference imports or writes to existing research notebooks. A row denotes
one source passage; repeated assessment methods remain separate datasets.
"""
import json
import math
from pathlib import Path
import re
import secrets

from .common import fingerprint, require
from .jev_atlas import JevAtlas, read_record, write_record, now, locked
from .finder import model_info

EXPANDED = '7f665a93c90cb1c2e1253d36'
PILOT = 'c8e5aca183e5777cdae09cfb'
RECOVERY = 'intact-window-recovery-20260917-v1'


class AnalysisWorkspace:
    def __init__(self, workspace, catalog):
        self.workspace = Path(workspace); self.catalog = catalog
        self.store = JevAtlas(workspace); self.root = self.workspace / 'analysis'

    def sources(self, identity):
        if identity in ('expanded', 'pilot'):
            return [{'batch': EXPANDED if identity == 'expanded' else PILOT, 'items': None}]
        require(identity == 'intact', 'Unknown analysis dataset')
        path = self.store.root / RECOVERY
        release = read_record(path / 'release.json'); protocol = read_record(path / 'qualification.json')
        require(release['qualification_sha256'] == protocol['sha256'], 'Recovery source differs')
        return ([{'batch': a['batch'], 'items': None} for a in protocol['allocations']] +
                [{'batch': r['batch'], 'items': [r['item']]} for r in release['reused']])

    def index(self):
        available = []; issues = []
        for identity, title, description in (
            ('expanded', 'Two tiers · development sample', '31 selected passages; all 53 questions in one request per passage.'),
            ('intact', 'Two tiers · intact-window sample', '27 selected passages; joined broad and detail packs, including the reused first result.'),
            ('pilot', 'Original eight-topic pilot', '200 sampled passages assessed with the original eight-topic vocabulary.')):
            try:
                sources = self.sources(identity)
                for source in sources: self.store.plan(source['batch'])
                available.append({'id': identity, 'title': title, 'description': description})
            except (ValueError, OSError) as error:
                issues.append({'id': identity, 'message': str(error)[:180]})
        return {'datasets': available, 'issues': issues, 'views': self.views()}

    def dataset(self, identity):
        sources = self.sources(identity); merged = {}; topics = {}; receipts = []; inventory = None
        for source in sources:
            plan = self.store.plan(source['batch'])
            inventory = plan.get('coverage_summary', {}).get('visible_nonsynthetic_targets', inventory)
            for t in plan['dictionary']:
                if t['id'] not in plan['topics']: continue
                field = 'Score · ' + t['title']
                entry = {'id': t['id'], 'field': field, 'title': t['title'], 'group': t.get('group', 'focused'), 'definition': t.get('definition', ''), 'boundary': t.get('boundary', '')}
                require(t['id'] not in topics or topics[t['id']] == entry, 'Question definitions differ across packs')
                topics[t['id']] = entry
            for item in self.store.results(plan):
                if source['items'] is not None and item['id'] not in source['items']: continue
                signature = fingerprint([item['run_id'], item['message_id'], item['source_sha256'], item['text'], item['context']])
                if item['id'] not in merged:
                    merged[item['id']] = {'item': item, 'signature': signature, 'scores': {}, 'states': []}
                target = merged[item['id']]
                require(target['signature'] == signature, 'Joined passages differ')
                target['states'].append(item['status'])
                for topic in plan['topics']:
                    key = 'topic_' + topic
                    value = (item['answers'] or {}).get(key, {}).get('noul') if item['status'] == 'complete' else None
                    field = topics[topic]['field']
                    require(field not in target['scores'], 'Duplicate assessment for the same passage and question')
                    target['scores'][field] = None if value is None else value * 100
                for kind in ('requests', 'responses'):
                    path = self.store.batch_path(plan['id']) / kind / (item['id'] + '.json')
                    if path.exists(): receipts.append({'batch': plan['id'], 'item': item['id'], 'kind': kind, 'sha256': read_record(path)['sha256']})
            receipts.append({'batch': plan['id'], 'plan_sha256': plan['sha256']})
        rows = []; passages = {}
        for iid, joined in merged.items():
            item = joined['item']; run = self.catalog.runs.get(item['run_id'], {})
            message = next((m for m in run.get('messages', []) if m['id'] == item['message_id']), None)
            current = bool(message and message['text'] == item['text'] and run['source']['sha256'] == item['source_sha256'])
            model = (message or {}).get('model') or 'Unknown'
            meta = model_info(model); exp = run.get('experiment', {})
            settings = run.get('settings_by_speaker', {}).get(item['speaker'], run.get('settings', {}))
            states = joined['states']; status = 'Complete' if all(s == 'complete' for s in states) else 'Incomplete'
            if not current: status = 'Source changed / missing'
            row = {'__id': iid, 'Conversation': item['run_title'], 'Conversation ID': item['run_id'],
                   'Model': meta['label'], 'Model ID': model, 'Model family': meta.get('developer', 'Unknown'),
                   'Weight access': meta.get('weights', 'Unknown'), 'Speaker': item['speaker'], 'Turn': item['turn'],
                   'Condition': item['condition'], 'Identity': exp.get('identity', 'Unknown'),
                   'Composition': exp.get('composition', 'Unknown'), 'Participants': exp.get('participants', 'Unknown'),
                   'External intervention': exp.get('external', 'Unknown'), 'External models': ' · '.join(exp.get('external_models', [])) or 'None recorded',
                   'Participant models': ' · '.join(exp.get('models', item.get('models', []))),
                   'History': exp.get('history', 'Unknown'), 'Task': exp.get('task', 'Unknown'), 'Exit instruction': exp.get('exit', 'Unknown'),
                   'Temperature': settings.get('temperature', 'Unknown'), 'Top p': settings.get('top_p', 'Unknown'),
                   'Quality': item.get('message_status', 'Unknown'), 'Sample stratum': item.get('sampling_stratum', 'Unspecified'),
                   'Assessment status': status}
            for t in topics.values(): row[t['field']] = joined['scores'].get(t['field']) if current else None
            rows.append(row)
            passages[iid] = {'id': iid, 'run_id': item['run_id'], 'message_id': item['message_id'],
                              'title': item['run_title'], 'text': item['text'], 'context': item['context'],
                              'model': model, 'source_current': current, 'source_sha256': item['source_sha256']}
        result = {'schema': 'behaviorlab.analysis-dataset/1', 'id': identity, 'rows': rows, 'topics': list(topics.values()),
                  'passages': passages, 'provenance': receipts,
                  'coverage': {'passages': len(rows), 'conversations': len({r['Conversation ID'] for r in rows}),
                               'complete': sum(r['Assessment status'] == 'Complete' for r in rows),
                               'questions': len(topics), 'corpus_visible_targets': inventory},
                  'method': 'Selected assessment sample, not a whole-corpus distribution. One row per passage; shared source IDs do not imply independent conversations. Missing or stale scores remain unknown.'}
        result['fingerprint'] = fingerprint(result)
        return result

    def views(self):
        entries = []
        for path in sorted((self.root / 'views').glob('*/*.json')):
            record = read_record(path)
            if not entries or entries[-1]['id'] != record['id']: entries.append(record)
            else: entries[-1] = record
        return entries

    def save(self, data):
        dataset = self.dataset(data.get('dataset'))
        require(data.get('dataset_fingerprint') == dataset['fingerprint'], 'Assessment data changed; reload before saving')
        config = data.get('config'); require(isinstance(config, dict) and config.get('version') == 1, 'Invalid analysis configuration')
        require(len(json.dumps(config)) < 50000, 'Analysis configuration too large')
        title = data.get('title', '').strip(); require(0 < len(title) <= 160, 'Name the analysis (up to 160 characters)')
        require(isinstance(data.get('note', ''), str) and len(data.get('note', '')) <= 8000, 'Observation too long')
        fields = {t['field'] for t in dataset['topics']}
        require(isinstance(config.get('transforms', {}), dict), 'Invalid transformations')
        for field, rule in config.get('transforms', {}).items():
            require(field in fields and isinstance(rule, dict), 'Unknown transformed field')
            require(rule.get('mode') in ('continuous', 'binary', 'bands', 'quantile'), 'Unknown transformation')
            cuts = rule.get('cuts', [])
            require(isinstance(cuts, list) and len(cuts) <= 19 and all(type(c) in (int, float) and math.isfinite(c) and 0 <= c <= 100 for c in cuts), 'Invalid cut points')
            require(cuts == sorted(set(cuts)), 'Cut points must be strictly increasing')
            if rule['mode'] == 'binary':
                v = rule.get('threshold'); require(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 100, 'Invalid threshold')
            if rule['mode'] == 'quantile':
                require(rule.get('reference') == dataset['fingerprint'], 'Quantile reference differs; refit on this dataset')
        identity = data.get('id') or secrets.token_hex(12)
        require(isinstance(identity, str) and re.fullmatch('[a-f0-9]{24}', identity), 'Invalid view ID')
        author = data.get('author', 'Local researcher'); require(author in ('Local researcher', 'Codex'), 'Unknown author')
        with locked(self.root / '.views.lock'):
            history = sorted((self.root / 'views' / identity).glob('*.json'))
            prior = read_record(history[-1]) if history else None
            require(data.get('revision', 0) == (prior['revision'] if prior else 0), 'View changed; reload before editing')
            record = {'schema': 'behaviorlab.analysis-view/1', 'id': identity, 'revision': len(history) + 1,
                      'created_at': prior['created_at'] if prior else now(), 'updated_at': now(),
                      'author': prior['author'] if prior else author, 'edited_by': author,
                      'title': title, 'note': data.get('note', ''), 'dataset': dataset['id'],
                      'dataset_fingerprint': dataset['fingerprint'], 'provenance': dataset['provenance'], 'config': config}
            write_record(self.root / 'views' / identity / f"{record['revision']:06d}.json", record)
        return record
