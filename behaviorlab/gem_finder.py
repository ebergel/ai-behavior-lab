"""Gem discovery and personal readings, separate from topic classifications."""
import json
from pathlib import Path

from .common import canonical, fingerprint, require
from .gem_plan import PILOT
from .gem_runner import receipts, summary
from .jev_atlas import now, read_record
from .topic_trajectories import path_messages
from .finder import model_info

RATINGS={'':'No verdict yet','gem':'Keep as a gem','promising':'Promising','ordinary':'Ordinary',
         'misleading':'Sounds profound, little substance','unsure':'Unsure'}
AUTHORS=('Local researcher','Codex')


class GemFinder:
    def __init__(self,workspace,notes,catalog):
        self.root=Path(workspace)/PILOT;self.notes=notes;self.catalog=catalog
        self.cached_plan=None
        with notes.lock,notes.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS gem_readings (id TEXT PRIMARY KEY, revision INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS gem_reading_history (id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(id,revision))')

    def plan(self):
        if self.cached_plan is None and (self.root/'plan.json').exists():self.cached_plan=read_record(self.root/'plan.json')
        return self.cached_plan

    def batches(self):
        base=self.plan()
        if not base:return []
        batches=[{'id':'pilot','title':'Original pilot','root':self.root,'plan':base}]
        seen={i['id'] for i in base['items']}
        seen_sources={(i['run_id'],i['message_id']) for i in base['items']}
        for path in sorted(self.root.parent.glob('expansion-*/plan.json')):
            plan=read_record(path)
            require(plan.get('schema')=='behaviorlab.gem-expansion/1' and plan['parent_plan_sha256']==base['sha256'], 'Gem expansion parent differs')
            require(plan['rubric']==base['rubric'] and plan['questions']==base['questions'], 'Gem expansion rubric differs')
            require(plan['reference_sha256']==fingerprint(base.get('reference',[])), 'Gem expansion reference differs')
            ids={i['id'] for i in plan['items']}
            require(len(ids)==len(plan['items']) and not seen & ids, 'Duplicate Gem assessment target across batches')
            sources={(i['run_id'],i['message_id']) for i in plan['items']}
            require(len(sources)==len(plan['items']) and not seen_sources & sources, 'Duplicate Gem source passage across batches')
            seen.update(ids)
            seen_sources.update(sources)
            batches.append({'id':path.parent.name,'title':'Model × length expansion','root':path.parent,'plan':plan})
        return batches

    def source_plan(self,run_id,message_id):
        return next((b['plan'] for b in self.batches() if any(i['run_id']==run_id and i['message_id']==message_id for i in b['plan']['items'])),self.plan())

    def all_readings(self):
        with self.notes.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT body FROM gem_readings ORDER BY rowid')]

    def history(self,identity):
        with self.notes.connect() as db:
            rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM gem_reading_history WHERE id=? ORDER BY revision DESC',(identity,))]
        require(bool(rows),'Unknown gem reading');return rows

    def current_source(self,run_id,message_id):
        plan=self.plan();require(plan is not None,'Prepare a discovery pilot first')
        require(isinstance(run_id,str) and isinstance(message_id,str),'Invalid passage identity')
        require(run_id in plan['discovery_runs'],'This conversation is outside Gem Finder discovery scope or reserved for independent validation')
        run=self.catalog.runs.get(run_id)
        require(run and run['source']['sha256']==plan['discovery_runs'][run_id],'Source changed since discovery freeze')
        m=next((m for m in run['messages'] if m['id']==message_id),None)
        require(m and m.get('kind')=='message' and isinstance(m.get('text'),str) and m['text'].strip(),'Choose a visible participant passage')
        return run,m

    def save(self,data):
        require(isinstance(data,dict),'Expected a gem reading')
        run,m=self.current_source(data.get('run_id'),data.get('message_id'))
        author=data.get('author','Local researcher');require(author in AUTHORS,'Declare reading authorship')
        require(data.get('source_sha256')==run['source']['sha256'],'Reading source is stale; reopen it')
        identity=fingerprint(['gem-reading/1',run['id'],m['id'],author])[:24]
        require(not data.get('id') or data['id']==identity,'Reading identity or author differs')
        rating=data.get('rating','');note=data.get('note','');quote=data.get('quote','');axes=data.get('axes',{})
        require(isinstance(rating,str) and rating in RATINGS,'Choose a reading verdict')
        require(isinstance(note,str) and len(note)<=8000,'Use a note of up to 8,000 characters')
        require(isinstance(quote,str) and (not quote or quote in m['text']),'The quoted phrase must appear exactly in this passage')
        rubric=self.plan()['rubric'];allowed={a['id'] for a in rubric['axes']}
        require(isinstance(axes,dict) and set(axes)<=allowed and all(type(v) is int and 0<=v<=4 for v in axes.values()),'Choose rubric levels 0–4, or leave unrated')
        exposure=data.get('exposure');require(exposure in ('visible','hidden_in_this_view'),'Record score visibility')
        archived=data.get('archived',False);require(type(archived) is bool,'Invalid archive state')
        with self.notes.lock,self.notes.connect() as db:
            row=db.execute('SELECT revision,body FROM gem_readings WHERE id=?',(identity,)).fetchone()
            require(not row or type(data.get('revision')) is int and row[0]==data['revision'],'Reading changed; reload before editing')
            require(row or not data.get('id'),'Unknown reading')
            prior=json.loads(row[1]) if row else {};at=now()
            saved={'id':identity,'revision':row[0]+1 if row else 1,'run_id':run['id'],'message_id':m['id'],
                   'source_sha256':run['source']['sha256'],'target_text':m['text'],'author':author,'rating':rating,'note':note.strip(),
                   'quote':quote,'axes':axes,'exposure':exposure,'archived':archived,'created_at':prior.get('created_at',at),'updated_at':at,
                   'rubric_version':rubric['version'],'rubric_sha256':fingerprint(rubric),'plan_sha256':self.source_plan(run['id'],m['id'])['sha256'],
                   'interpretation':'Personal development reading; hidden in this view does not establish independent blinding.'}
            args=(identity,saved['revision'],canonical(saved));db.execute('INSERT OR REPLACE INTO gem_readings VALUES (?,?,?)',args)
            db.execute('INSERT INTO gem_reading_history VALUES (?,?,?)',args)
        return saved

    def item_for_source(self,run_id,message_id):
        run,m=self.current_source(run_id,message_id)
        item=next((i for b in self.batches() for i in b['plan']['items'] if i['run_id']==run_id and i['message_id']==message_id),None)
        if item:return dict(item)
        path=next(path_messages(run,leaf) for leaf in run['leaves'] if any(x['id']==message_id for x in path_messages(run,leaf)))
        index=next(i for i,x in enumerate(path) if x['id']==message_id)
        context=[{'speaker':x.get('speaker',''),'text':x['text']} for x in path[max(0,index-2):index] if x.get('text')]
        model=m.get('model','Unknown')
        return {'id':fingerprint(['gem-example',run_id,message_id])[:24],'run_id':run_id,'message_id':message_id,
                'source_sha256':run['source']['sha256'],'title':run['title'],'text':m['text'],'context':context,
                'speaker':m.get('speaker',''),'turn':m.get('turn'),'model':model,'model_label':model_info(model)['label'],
                'quality':m.get('status','Unknown'),'condition':run.get('condition',''),'identity':run.get('experiment',{}).get('identity','Unknown'),
                'words':len(m['text'].split()),'sample_role':'reader_example','broad_topic':'','topic_scores':{},
                'profile_distance':{'value':None,'neighbors':[]}}

    def detail(self,run_id=None,message_id=None,batch='all'):
        plan=self.plan()
        if not plan:return {'available':False,'ratings':RATINGS,'message':'A Gem Finder pilot has not been prepared in this workspace.'}
        batches=self.batches();require(batch=='all' or any(b['id']==batch for b in batches),'Unknown Gem batch')
        selected=[b for b in batches if batch=='all' or b['id']==batch]
        index=[];rows={};items=[];totals=[];sampled=set()
        for b in batches:
            br,attempts=receipts(b['root'],b['plan']);stats=summary(b['root'],b['plan'])
            index.append({'id':b['id'],'title':b['title'],'planned':len(b['plan']['items']),'complete':stats['complete'],'known_cost_usd':stats['known_cost_usd']})
            sampled.update((i['run_id'],i['message_id']) for i in b['plan']['items'])
            if b in selected:
                rows.update(br);totals.append(stats)
                items.extend(dict(i,cohort=b['id'],cohort_label=b['title']) for i in b['plan']['items'])
        readings=self.all_readings();represented={(i['run_id'],i['message_id']) for i in items};issues=[]
        pairs={(r['run_id'],r['message_id']) for r in readings if not r['archived']}
        if run_id:pairs.add((run_id,message_id))
        for pair in sorted(pairs-represented-sampled):
            try:items.append(self.item_for_source(*pair))
            except ValueError as e:issues.append({'run_id':pair[0],'message_id':pair[1],'reason':str(e)})
        for item in items:
            history=rows.get(item['id'],[]);last=history[-1] if history else {}
            run=self.catalog.runs.get(item['run_id']);m=next((m for m in (run or {}).get('messages',[]) if m['id']==item['message_id']),None)
            current=bool(run and m and run['source']['sha256']==item['source_sha256'] and m.get('text')==item['text'])
            item['source_current']=current;item['assessment']=('Source changed' if not current else last.get('status','pending'))
            item['answers']=last.get('answers',{}) if current else {}
            item['readings']=[r for r in readings if (r['run_id'],r['message_id'])==(item['run_id'],item['message_id']) and not r['archived']]
        combined={k:sum(t[k] for t in totals) for k in ('planned','complete','attempts','known_cost_usd','unknown_reserved_usd','pending')}
        combined['stopped']=[s for t in totals for s in t['stopped']]
        lineages=len({i.get('lineage',i['run_id']) for b in selected for i in b['plan']['items']})
        hashes=[b['plan']['sha256'] for b in selected]
        note=(f"{combined['planned']} planned targets from {lineages} conversation lineages. "
              + ('The original pilot selected one target per lineage. ' if batch=='pilot' or len(batches)==1 else
                 'The expansion samples model × length cells where available, with at most three targets per lineage including the original pilot. These are distinct passages, not independent conversation replicates. ')
              + f"All {len(plan['selection']['reserved_lineages'])} reserved validation lineages remain excluded. Sampling is for development, not a corpus prevalence estimate. Your readings remain separate from model assessments.")
        return {'available':True,'batch':batch,'batches':index,'plan_sha256':hashes[0] if len(hashes)==1 else fingerprint(hashes),
                'plan_hashes':hashes,'created_at':selected[-1]['plan']['created_at'],'rubric':plan['rubric'],
                'budget':{'unique_requests':combined['planned'], 'max_attempts':sum(b['plan']['budget']['max_attempts'] for b in selected)},
                'batch_budgets':{b['id']:b['plan']['budget'] for b in selected},'summary':combined,'sample_note':note,'lineages':lineages,
                'selection':{k:v for k,v in plan['selection'].items() if k!='reserved_lineages'},
                'reserved_lineages':len(plan['selection']['reserved_lineages']),'topics':plan['broad_topics'],
                'items':items,'ratings':RATINGS,'issues':issues,'policy':' '.join(b['plan']['policy'] for b in selected)}

    def export(self):
        with self.notes.lock,self.notes.connect() as db:
            history=[json.loads(r[0]) for r in db.execute('SELECT body FROM gem_reading_history ORDER BY id,revision')]
            readings=[json.loads(r[0]) for r in db.execute('SELECT body FROM gem_readings')]
        plan=self.plan()
        return {'schema':'behaviorlab.gem-export/2','batches':[{'id':b['id'],'plan':b['plan'],
                'receipts':{p.relative_to(b['root']).as_posix():read_record(p) for p in sorted((b['root']/'attempts').glob('*/*.json'))}} for b in self.batches()], 'plan':plan,'readings':readings,'history':history,
                'receipts':{p.relative_to(self.root).as_posix():read_record(p) for p in sorted((self.root/'attempts').glob('*/*.json'))} if plan else {}}
