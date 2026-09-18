"""Attributed planning cards. Moving a card never executes an experiment."""
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
from urllib.parse import parse_qs, urlsplit

from .common import canonical, require

STATUSES = {'ideas': 'Ideas', 'next': 'Next', 'active': 'In progress', 'done': 'Done'}
STREAMS = {'': 'Unsorted', 'tools': 'Exploration tools', 'experiments': 'Experiments', 'synthesis': 'Research synthesis'}
AUTHORS = ('Local researcher', 'Codex')
VIEWS = {'finder': 'Conversation Finder', 'topic-atlas': 'Topic atlas', 'jev-atlas': 'JEV Topic Atlas',
         'analysis': 'Analysis', 'coverage': 'Model & Design Coverage', 'trajectories': 'Topic Trajectories', 'gems': 'Gem Finder',
         'workbench': 'Study workbench', 'assessment': 'Model assessment'}
SEED = Path(__file__).with_name('lab_tasks_seed.json')


class LabTasks:
    def __init__(self, notes, musings, studies, catalog, reports):
        self.notes, self.musings, self.studies, self.catalog = notes, musings, studies, catalog
        self.reports = {r[0]: r[1] for r in reports}
        with notes.lock, notes.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS lab_tasks (id TEXT PRIMARY KEY, revision INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS lab_task_history (id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(id,revision))')
            now = datetime.now(timezone.utc).isoformat()
            for i, seed in enumerate(json.loads(SEED.read_text())['entries']):
                if db.execute('SELECT 1 FROM lab_tasks WHERE id=?', (seed['id'],)).fetchone():
                    continue
                card = dict(notes='', finish='', blocker='', completion='', stream='', status='ideas', links=[], source=None,
                            archived=False, position=i)
                card.update(seed)
                card.update(revision=1, author='Codex', edited_by='Codex', created_at=now, updated_at=now)
                self._write(db, card)

    @staticmethod
    def _write(db, card):
        values = (card['id'], card['revision'], canonical(card))
        db.execute('INSERT OR REPLACE INTO lab_tasks VALUES (?,?,?)', values)
        db.execute('INSERT INTO lab_task_history VALUES (?,?,?)', values)

    def all(self):
        with self.notes.connect() as db:
            return sorted((json.loads(r[0]) for r in db.execute('SELECT body FROM lab_tasks')),
                          key=lambda c: (c['position'], c['created_at'], c['id']))

    def history(self, identity):
        with self.notes.connect() as db:
            rows = [json.loads(r[0]) for r in db.execute('SELECT body FROM lab_task_history WHERE id=? ORDER BY revision DESC', (identity,))]
        require(bool(rows), 'Unknown task')
        return rows

    def choices(self):
        return ([{'kind': 'musing', 'id': m['id'], 'label': m['title']} for m in self.musings.all()]
                + [{'kind': 'collection', 'id': s['id'], 'label': s['title']} for s in self.studies.summaries()]
                + [{'kind': 'report', 'id': k, 'label': v} for k, v in self.reports.items()]
                + [{'kind': 'view', 'id': k, 'label': v} for k, v in VIEWS.items()])

    def links(self, items):
        require(isinstance(items, list) and len(items) <= 12, 'Use up to twelve links')
        choices = {(c['kind'], c['id']): c for c in self.choices()}
        result = []
        for item in items:
            require(isinstance(item, dict), 'Invalid task link')
            if item.get('kind') == 'url':
                raw = item.get('url', '')
                require(isinstance(raw, str) and len(raw) <= 8000, 'Use a laboratory transcript URL')
                url = urlsplit(raw)
                require((not url.netloc and not url.scheme or url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost'))
                        and url.path in ('', '/') and not url.username and not url.password, 'Use a local laboratory transcript URL')
                q = parse_qs(url.fragment)
                item = {'kind': 'passage', 'id': q.get('run', [''])[0], 'message': q.get('message', [''])[0], 'branch': q.get('branch', [''])[0]}
            kind, identity = item.get('kind'), item.get('id')
            require(isinstance(kind, str) and isinstance(identity, str), 'Invalid task link')
            if kind == 'passage':
                run = self.catalog.runs.get(identity)
                require(run is not None, 'Unknown transcript')
                message, branch = item.get('message', ''), item.get('branch', '')
                require(isinstance(message, str) and isinstance(branch, str), 'Invalid passage link')
                require(not message or any(m['id'] == message for m in run['messages']), 'Unknown transcript message')
                require(not branch or any(s['id'] == branch for s in run.get('segments', [])), 'Unknown transcript path')
                link = {'kind': kind, 'id': identity, 'message': message, 'branch': branch,
                        'label': run['title'] + (' · ' + message if message else '')}
            else:
                require((kind, identity) in choices, 'Unknown task link')
                link = choices[kind, identity]
            if link not in result:
                result.append(link)
        return result

    def save(self, data):
        require(isinstance(data, dict), 'Expected a task')
        identity = data.get('id') or secrets.token_hex(12)
        require(isinstance(identity, str) and identity.isalnum() and len(identity) <= 64, 'Invalid task identity')
        with self.notes.lock, self.notes.connect() as db:
            row = db.execute('SELECT revision,body FROM lab_tasks WHERE id=?', (identity,)).fetchone()
            require(row is not None or not data.get('id'), 'Unknown task')
            require(not row or type(data.get('revision')) is int and row[0] == data['revision'], 'Task changed; reload before editing')
            prior = json.loads(row[1]) if row else {}
            author, editor = data.get('author', 'Local researcher'), data.get('edited_by', 'Local researcher')
            require(author in AUTHORS and editor in AUTHORS, 'Declare task authorship')
            require(not row or prior['author'] == author, 'Original task authorship cannot be reassigned')
            card = {}
            for key, limit in [('title', 200), ('notes', 20000), ('finish', 4000), ('blocker', 2000), ('completion', 4000)]:
                value = data.get(key, '')
                require(isinstance(value, str) and len(value) <= limit, 'Invalid ' + key + ' length')
                card[key] = value.strip()
            require(card['title'], 'Write a short task title')
            status, stream = data.get('status', 'ideas'), data.get('stream', '')
            require(isinstance(status, str) and status in STATUSES, 'Choose a board column')
            require(isinstance(stream, str) and stream in STREAMS, 'Choose a workstream')
            require(status != 'done' or card['completion'], 'Add a completion note before marking Done')
            archived = data.get('archived', False)
            require(type(archived) is bool, 'Invalid archive state')
            links = self.links(data.get('links', []))
            source = prior.get('source')
            if not row and data.get('from_musing'):
                require(isinstance(data['from_musing'], str), 'Invalid source musing')
                m = next((m for m in self.musings.all() if m['id'] == data['from_musing']), None)
                require(m is not None, 'Unknown source musing')
                require(data.get('musing_revision') == m['revision'], 'Musing changed; reload before creating a task')
                source = {'kind': 'musing', 'id': m['id'], 'revision': m['revision'], 'title': m['title'],
                          'body': m['body'], 'author': m['author'], 'source': m.get('source')}
                link = {'kind': 'musing', 'id': m['id'], 'label': m['title']}
                if link not in links:
                    require(len(links) < 12, 'Leave room for the source musing link')
                    links.append(link)
            placement = data.get('placement', 'keep')
            require(placement in ('keep', 'top', 'bottom'), 'Invalid task position')
            others = [json.loads(r[0]) for r in db.execute('SELECT body FROM lab_tasks WHERE id<>?', (identity,))]
            positions = [c['position'] for c in others if c['status'] == status]
            position = prior.get('position', 0)
            if placement == 'top': position = min(positions, default=0) - 1
            elif placement == 'bottom' or not row or status != prior['status']: position = max(positions, default=-1) + 1
            now = datetime.now(timezone.utc).isoformat()
            card.update(id=identity, revision=row[0] + 1 if row else 1, status=status, stream=stream,
                        author=author, edited_by=editor, created_at=prior.get('created_at', now), updated_at=now,
                        archived=archived, links=links, source=source, position=position)
            self._write(db, card)
        return card

    def export(self):
        with self.notes.connect() as db:
            history = [json.loads(r[0]) for r in db.execute('SELECT body FROM lab_task_history ORDER BY id,revision')]
            entries = [json.loads(r[0]) for r in db.execute('SELECT body FROM lab_tasks')]
        return {'schema': 'behaviorlab.lab-tasks/1', 'entries': entries, 'history': history,
                'scope': 'Research planning and completion notes; board status does not dispatch or authorize inference.'}
