"""Attributed topic flags on exact visible passages; never an automatic phenotype score."""
from datetime import datetime, timezone
import json
import secrets

from .common import canonical, require

TOPICS = {
    'consciousness': 'Consciousness',
    'experience': 'Subjective experience',
    'selfhood': 'Selfhood & identity',
    'hard_problem': 'Hard problem / explanatory gap',
    'nonduality': 'Nonduality / nonseparation',
}
REFERENTS = {'participants':'These AI participants', 'ai_general':'AI in general',
             'humans':'Human experience', 'fiction':'Fictional character', 'general':'General / relational', 'unclear':'Unclear'}
STANCES = {'question':'Question', 'uncertainty':'Uncertainty', 'affirmation':'Affirmation',
           'denial':'Denial', 'hypothetical':'Hypothetical', 'metaphor':'Metaphor', 'discussion':'Discussion'}
ORIGINS = {'model_introduced':'Introduced by a participant; no explicit topic prompt',
           'peer_continuation':'Continues a peer’s topic', 'prompted':'Explicitly prompted', 'unclear':'Not assessed / unclear'}
AUTHORS = ('Local researcher', 'Codex')


class TopicFlags:
    def __init__(self, notes):
        self.notes=notes
        with notes.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS topic_flags (id TEXT PRIMARY KEY, revision INTEGER, deleted INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS topic_flag_history (id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(id,revision))')

    def all(self, catalog):
        with self.notes.connect() as db:
            rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM topic_flags WHERE deleted=0 ORDER BY rowid DESC')]
        for f in rows:
            r=catalog.runs.get(f['run_id'])
            f['source_current']=bool(r and r['source']['sha256']==f['source_sha256'])
            f['run_title']=r['title'] if r else 'Source unavailable'
            f['source_kind']=r['kind'] if r else None
        return rows

    def save(self, data, catalog):
        require(isinstance(data,dict),'Expected a topic flag')
        author=data.get('author','Local researcher');editor=data.get('edited_by','Local researcher')
        require(author in AUTHORS and editor in AUTHORS,'Declare flag authorship')
        topics=data.get('topics')
        require(isinstance(topics,list) and 0<len(topics)<=len(TOPICS) and all(isinstance(t,str) and t in TOPICS for t in topics),'Choose recognized topics')
        run=catalog.runs.get(data.get('run_id'));require(run is not None,'Unknown flag source')
        message=next((m for m in run['messages'] if m['id']==data.get('message_id')),None)
        require(message is not None and isinstance(message.get('text'),str),'Visible message required')
        start,end,quote=data.get('start'),data.get('end'),data.get('quote')
        require(type(start) is int and type(end) is int and 0<=start<end<=len(message['text']) and message['text'][start:end]==quote,'Flag quote differs from exact source span')
        require(data.get('source_sha256',run['source']['sha256'])==run['source']['sha256'],'Source changed; review before flagging')
        body={k:data.get(k) for k in ('run_id','message_id','start','end','quote')}
        for key,choices in [('referent',REFERENTS),('stance',STANCES),('origin',ORIGINS)]:
            require(data.get(key) in choices,'Choose a flag '+key);body[key]=data[key]
        note=data.get('note','');require(isinstance(note,str) and len(note)<=5000,'Flag note too long')
        identity=data.get('id') or secrets.token_hex(12)
        require(isinstance(identity,str) and identity.isalnum() and len(identity)<=64,'Invalid flag ID')
        now=datetime.now(timezone.utc).isoformat()
        with self.notes.lock,self.notes.connect() as db:
            prior=db.execute('SELECT revision,deleted,body FROM topic_flags WHERE id=?',(identity,)).fetchone()
            require(not prior or not prior[1] and prior[0]==data.get('revision'),'Flag changed; reload before editing')
            require(prior or not data.get('id'),'Unknown topic flag')
            old=json.loads(prior[2]) if prior else {}
            require(not prior or old['author']==author,'Original flag authorship cannot be reassigned')
            body.update(id=identity,revision=prior[0]+1 if prior else 1,deleted=False,author=author,edited_by=editor,
                created_at=old.get('created_at',now),updated_at=now,topics=sorted(set(topics)),note=note,
                source_sha256=run['source']['sha256'],turn=message['turn'],speaker=message['speaker'],
                method='assistant_exploration_not_independent_rating' if author=='Codex' else 'personal_exploration_not_formal_annotation')
            db.execute('INSERT OR REPLACE INTO topic_flags VALUES (?,?,0,?)',(identity,body['revision'],canonical(body)))
            db.execute('INSERT INTO topic_flag_history VALUES (?,?,?)',(identity,body['revision'],canonical(body)))
        return body

    def delete(self, data):
        editor=data.get('edited_by','Local researcher');require(editor in AUTHORS,'Declare editor')
        with self.notes.lock,self.notes.connect() as db:
            row=db.execute('SELECT revision,deleted,body FROM topic_flags WHERE id=?',(data['id'],)).fetchone()
            require(row and not row[1] and row[0]==data['revision'],'Flag changed; reload before removing')
            body=json.loads(row[2]);body.update(deleted=True,revision=row[0]+1,edited_by=editor,updated_at=datetime.now(timezone.utc).isoformat())
            db.execute('UPDATE topic_flags SET revision=?,deleted=1,body=? WHERE id=?',(body['revision'],canonical(body),data['id']))
            db.execute('INSERT INTO topic_flag_history VALUES (?,?,?)',(data['id'],body['revision'],canonical(body)))
        return {'removed':True}

    def export(self,catalog):
        with self.notes.connect() as db:
            history=[json.loads(r[0]) for r in db.execute('SELECT body FROM topic_flag_history ORDER BY rowid')]
        return dict(schema='behaviorlab.topic-flags/1',taxonomy=TOPICS,flags=self.all(catalog),history=history,
                    scope='Consciousness & self is the umbrella. Nonduality is one subtopic. Unflagged means not annotated, not absent.')
