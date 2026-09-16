"""An attributed, versioned notebook for the laboratory's evolving purpose."""
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets

from .common import canonical, require

KINDS = {'reflection':'Reflection','question':'Research question','hypothesis':'Working hypothesis','direction':'Research direction'}
STATUSES = {'exploring':'Exploring','working':'Working direction','reconsidered':'Reconsidered','parked':'Parked'}
AUTHORS = ('Local researcher','Codex')
SEED = Path(__file__).with_name('lab_musings_seed.json')


class LabMusings:
    def __init__(self, notes):
        self.notes=notes
        with notes.lock,notes.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS lab_musings (id TEXT PRIMARY KEY, revision INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS lab_musing_history (id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(id,revision))')
            now=datetime.now(timezone.utc).isoformat()
            for seed in json.loads(SEED.read_text())['entries']:
                if db.execute('SELECT 1 FROM lab_musings WHERE id=?',(seed['id'],)).fetchone():continue
                body=dict(seed,revision=1,created_at=now,updated_at=now,edited_by='Codex',recorded_by='Codex',study_id=None)
                db.execute('INSERT INTO lab_musings VALUES (?,?,?)',(body['id'],1,canonical(body)))
                db.execute('INSERT INTO lab_musing_history VALUES (?,?,?)',(body['id'],1,canonical(body)))

    def all(self):
        with self.notes.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT body FROM lab_musings ORDER BY rowid DESC')]

    def history(self,identity):
        with self.notes.connect() as db:
            rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM lab_musing_history WHERE id=? ORDER BY revision DESC',(identity,))]
        require(bool(rows),'Unknown reflection')
        return rows

    def save(self,data,study_ids=()):
        require(isinstance(data,dict),'Expected a reflection')
        title=data.get('title');body=data.get('body')
        require(isinstance(title,str) and 0<len(title.strip())<=200,'Use a title of up to 200 characters')
        require(isinstance(body,str) and 0<len(body.strip())<=20000,'Write a reflection of up to 20,000 characters')
        kind=data.get('kind','reflection');status=data.get('status','exploring')
        require(kind in KINDS and status in STATUSES,'Choose a reflection kind and status')
        author=data.get('author','Local researcher');editor=data.get('edited_by','Local researcher')
        require(author in AUTHORS and editor in AUTHORS,'Declare authorship')
        tags=data.get('tags',[])
        require(isinstance(tags,list) and len(tags)<=10 and all(isinstance(t,str) and 0<len(t.strip())<=60 for t in tags),'Use up to ten short tags')
        study=data.get('study_id') or None
        require(study is None or isinstance(study,str) and study in study_ids,'Unknown research collection')
        identity=data.get('id') or secrets.token_hex(12)
        require(isinstance(identity,str) and identity.isalnum() and len(identity)<=64,'Invalid reflection identity')
        with self.notes.lock,self.notes.connect() as db:
            row=db.execute('SELECT revision,body FROM lab_musings WHERE id=?',(identity,)).fetchone()
            require(row is not None or not data.get('id'),'Unknown reflection')
            require(not row or type(data.get('revision')) is int and row[0]==data['revision'],'Reflection changed; reload before editing')
            prior=json.loads(row[1]) if row else {}
            require(not row or prior['author']==author,'Original authorship cannot be reassigned')
            now=datetime.now(timezone.utc).isoformat();revision=row[0]+1 if row else 1
            # Source quotations and attribution are immutable provenance. Edits
            # create a new body; they never replace the source's original words.
            saved={'id':identity,'revision':revision,'title':title.strip(),'body':body,'kind':kind,'status':status,
                   'tags':sorted({t.strip().casefold() for t in tags}),'study_id':study,'author':author,'edited_by':editor,
                   'recorded_by':prior.get('recorded_by',editor),'created_at':prior.get('created_at',now),'updated_at':now,
                   'slot':prior.get('slot'),'source':prior.get('source')}
            db.execute('INSERT OR REPLACE INTO lab_musings VALUES (?,?,?)',(identity,revision,canonical(saved)))
            db.execute('INSERT INTO lab_musing_history VALUES (?,?,?)',(identity,revision,canonical(saved)))
        return saved

    def export(self):
        with self.notes.connect() as db:
            history=[json.loads(r[0]) for r in db.execute('SELECT body FROM lab_musing_history ORDER BY id,revision')]
        return {'schema':'behaviorlab.lab-musings/1','entries':self.all(),'history':history,
                'scope':'Evolving research purpose, interpretations and design ideas; not experimental outcomes.'}
