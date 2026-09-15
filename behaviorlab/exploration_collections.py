"""Versioned research collections with exact source links and declared authorship."""
from datetime import datetime, timezone
import json
import secrets

from .common import canonical, require


AUTHORS = ('Local researcher', 'Codex')


class ResearchCollections:
    def __init__(self, notes):
        self.notes = notes
        with notes.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS research_collections (id TEXT PRIMARY KEY, revision INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS collection_history (id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(id, revision))')

    def all(self):
        with self.notes.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT body FROM research_collections ORDER BY rowid DESC')]

    def get(self, identity):
        with self.notes.connect() as db:
            row = db.execute('SELECT body FROM research_collections WHERE id=?', (identity,)).fetchone()
        require(row is not None, 'Unknown research collection')
        return json.loads(row[0])

    def summaries(self):
        return [{k:d[k] for k in ('id','revision','title','question','author','updated_at')} |
                {'run_count':len(d['runs']), 'finding_count':len(d['findings'])} for d in self.all()]

    @staticmethod
    def text(data, key, limit, required=False):
        value = data.get(key, '')
        require(isinstance(value,str) and len(value)<=limit and (not required or value.strip()), 'Invalid collection '+key)
        return value

    def save(self, data, catalog):
        require(isinstance(data,dict), 'Expected research collection')
        editor=data.get('edited_by','Local researcher'); author=data.get('author','Local researcher')
        require(author in AUTHORS and editor in AUTHORS, 'Declare collection authorship')
        body={key:self.text(data,key,limit,required) for key,limit,required in
              [('title',180,True),('question',1200,False),('summary',16000,False),('selection_note',8000,False)]}
        members=data.get('runs',[]); findings=data.get('findings',[])
        require(isinstance(members,list) and len(members)<=200, 'Use up to 200 reading entries')
        require(isinstance(findings,list) and len(findings)<=100, 'Use up to 100 findings')
        run_ids=set(); clean_members=[]
        for member in members:
            require(isinstance(member,dict), 'Invalid reading entry')
            identity=member.get('run_id'); require(identity in catalog.runs and identity not in run_ids, 'Unknown or duplicate reading entry')
            run_ids.add(identity); status=member.get('status','queued')
            require(status in ('queued','passages_reviewed','visible_reviewed'), 'Invalid reading status')
            reviewer=member.get('reviewed_by',author)
            require(reviewer in AUTHORS, 'Declare reading reviewer')
            clean_members.append({'run_id':identity,'reason':self.text(member,'reason',2000),
                'review_note':self.text(member,'review_note',3000),'status':status,'reviewed_by':reviewer})
        clean_findings=[]; finding_ids=set()
        for finding in findings:
            require(isinstance(finding,dict), 'Invalid finding')
            identity=finding.get('id') or secrets.token_hex(8)
            require(isinstance(identity,str) and identity.isalnum() and len(identity)<=64 and identity not in finding_ids, 'Invalid finding identity')
            finding_ids.add(identity)
            kind=finding.get('kind','observation')
            require(kind in ('observation','counterexample','hypothesis','limitation'), 'Invalid finding category')
            evidence=finding.get('evidence',[])
            require(isinstance(evidence,list) and len(evidence)<=20, 'Use up to 20 passages per finding')
            require(evidence or kind in ('hypothesis','limitation'), 'Observations need source evidence')
            clean_evidence=[]
            for item in evidence:
                require(isinstance(item,dict) and item.get('run_id') in run_ids, 'Evidence must belong to this reading set')
                run=catalog.runs[item['run_id']]
                message=next((m for m in run['messages'] if m['id']==item.get('message_id')),None)
                require(message is not None and isinstance(message.get('text'),str), 'Evidence message unavailable')
                start,end=item.get('start'),item.get('end'); quote=item.get('quote')
                require(type(start) is int and type(end) is int and 0<=start<end<=len(message['text']) and message['text'][start:end]==quote, 'Quote differs from exact source span')
                source_hash=run['source']['sha256']
                require(item.get('source_sha256',source_hash)==source_hash, 'Evidence source changed; review before saving')
                clean_evidence.append({'run_id':run['id'],'message_id':message['id'],'start':start,'end':end,
                    'quote':quote,'source_sha256':source_hash,'turn':message['turn'],'speaker':message['speaker'],
                    'status_at_save':message['status'],'label':self.text(item,'label',500)})
            clean_findings.append({'id':identity,'kind':kind,'title':self.text(finding,'title',250,True),
                'text':self.text(finding,'text',7000,True),'evidence':clean_evidence})
        identity=data.get('id') or secrets.token_hex(12)
        require(isinstance(identity,str) and identity.isalnum() and len(identity)<=64, 'Invalid collection identity')
        now=datetime.now(timezone.utc).isoformat()
        with self.notes.lock, self.notes.connect() as db:
            existing=db.execute('SELECT revision,body FROM research_collections WHERE id=?',(identity,)).fetchone()
            require(not existing or existing[0]==data.get('revision'), 'Collection changed; reload before editing')
            if existing:
                prior=json.loads(existing[1]); require(author==prior['author'], 'Original collection authorship cannot be reassigned')
            else:
                require(not data.get('id'), 'Unknown research collection')
                prior={}
            revision=existing[0]+1 if existing else 1
            body.update(id=identity,revision=revision,author=author,edited_by=editor,
                created_at=prior.get('created_at',now),updated_at=now,runs=clean_members,findings=clean_findings,
                method='assistant_exploration_not_independent_rating' if author=='Codex' else 'personal_exploration_not_formal_annotation')
            db.execute('INSERT OR REPLACE INTO research_collections VALUES (?,?,?)',(identity,revision,canonical(body)))
            db.execute('INSERT INTO collection_history VALUES (?,?,?)',(identity,revision,canonical(body)))
        return body

    def detail(self, identity, catalog):
        document=self.get(identity); sources={}
        for member in document['runs']:
            run=catalog.runs.get(member['run_id'])
            if run:
                sources[run['id']]={k:run[k] for k in ('id','title','models','condition','prompt','opening','settings','source','kind','message_count','cap_count','repeat_count')}
        for finding in document['findings']:
            for item in finding['evidence']:
                source=sources.get(item['run_id'])
                item['source_current']=bool(source and item['source_sha256']==source['source']['sha256'])
        return {'collection':document,'sources':sources,
                'notes':[n for n in self.notes.all() if n.get('study_id')==identity]}

    def export(self, identity, catalog):
        bundle=self.detail(identity,catalog)
        # A single portable bundle contains the visible evidence and settings.
        # Large request/transport payloads remain in the original evidence store.
        for run_id,source in bundle['sources'].items():
            run=catalog.runs[run_id]
            source['messages']=[{k:m.get(k) for k in ('id','parent','turn','speaker','segment','text','thinking','thinking_recorded','status','reason')}
                                for m in run['messages']]
            source['segments']=run['segments']
        return dict(schema='behaviorlab.research-collection/1',**bundle)
