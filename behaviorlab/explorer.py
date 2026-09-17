"""Local transcript exploration. Source evidence is read-only; notes are separate.

This module never imports an inference client for dispatch or executes a campaign.
Search operates on recorded visible messages, including explicitly flagged partial
outputs. Tags are personal research notes, not validated semantic annotations.
"""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .common import canonical, fingerprint, read_json, require, sha256
from .history import ancestry, request
from .exploration_collections import ResearchCollections
from .topic_flags import TopicFlags, TOPICS, REFERENTS, STANCES, ORIGINS
from .topic_atlas import TopicAtlas
from .jev_atlas import JevAtlas
from .finder import experiment, model_info, FinderViews, finder_result
from .lab_musings import LabMusings, KINDS as MUSING_KINDS, STATUSES as MUSING_STATUSES
from .study_workbench import build_workbench
from .journal import read_events
from .legacy import parse_run, verify_corpus
from .runner import campaign_documents, outcome, turn_from
from .trajectory_outcomes import line_features, repeated_state

STATIC = Path(__file__).with_name('explorer_ui')
REPORTS = [('opening-partner', 'Opening and partner: development reading', 'OPENING-PARTNER-STUDY.md'),
           ('opening-partner-design', 'Opening and partner: next study design', 'OPENING-PARTNER-DESIGN.md'),
           ('trajectory', 'Trajectory outcomes', 'PILOT-OUTCOMES-V0.2.md'),
           ('topic-atlas', 'Initial topics, variants and recurrence', 'TOPIC-ATLAS.md'),
           ('mixed-dialogue', 'Gemma and Haiku: local–cloud dialogues', 'GEMMA-HAIKU-PILOT.md'),
           ('framing', 'Nemotron framing comparison', 'NEMOTRON-FRAMING.md'),
           ('cheap-framing', 'GPT-4o mini and Haiku comparison', 'CHEAP-MODEL-FRAMING.md'),
           ('gpt4o-screen', 'GPT-4o short cost and output screen', 'GPT4O-SHORT-SCREEN.md'),
           ('topics', 'Consciousness and self: topic tracking', 'TOPIC-TRACKING.md'),
           ('assessment', 'Model assessment & cloud checks', 'MODEL-ASSESSMENT.md'),
           ('capacity', 'Output capacity & measurement', 'CAPACITY-AND-MEASUREMENT.md'),
           ('qualification', 'Prompt qualification', 'PROMPT-QUALIFICATION.md'),
           ('measurement', 'Measurement v2 · draft', 'MEASUREMENT-V2-DRAFT.md'),
           ('mixed', 'Mixed-model engineering', 'OLLAMA-MIXED-QUALIFICATION.md'),
           ('mtplx', 'MTPLX long trajectory', 'MTPLX-LONG-TRIAL.md')]


def visible_response(raw):
    try:
        data = read_json(raw)
        msg = data.get('message') or data.get('choices', [{}])[0].get('message', {})
        return {k: msg.get(k) if isinstance(msg.get(k), str) else None for k in ('content', 'thinking')}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return {'content': None, 'thinking': None}


def short_model(tag):
    return tag.rsplit('/', 1)[-1] if tag else 'Unknown model'


def base_summary(run):
    messages = run['messages']
    participant = [m for m in messages if m['speaker'] in ('X', 'Y')]
    texts = [m['text'] for m in messages if m['text'] is not None]
    run.update(message_count=sum(m['text'] is not None for m in participant),
        planned_count=len(participant), words=sum(len(t.split()) for t in texts),
        cap_count=sum(m['status']=='cap' for m in messages),
        unavailable_count=sum(m['status'] in ('blocked', 'pending', 'unresolved', 'not_dispatched') for m in messages),
        repeat_count=sum(m.get('repeat', False) for m in messages),
        has_thinking=any(m.get('thinking') for m in messages),
        preview=next((t for t in texts if t.strip()), '')[:240])
    run['_search'] = '\n'.join(texts).casefold()
    run['_metadata_search'] = ' '.join([run['title'], *run['models'], run['condition'], run['collection']]).casefold()
    return run


def load_legacy(directory):
    manifest = verify_corpus(directory)
    result = []
    for item in manifest['runs']:
        raw = (directory/'blobs'/item['sha256']).read_bytes()
        require(sha256(raw)==item['sha256'], 'Legacy source changed during indexing')
        records = parse_run(raw); header = records[0][1]; footer = records[-1][1]
        messages = []; previous = None; suffix = 0; capped = False
        for line, r in records[1:-1]:
            text = r.get('content'); main = r['kind']=='message'
            status = 'recorded'
            if main:
                status = 'cap' if r.get('done_reason')=='length' else 'after_cap' if capped else 'recorded'
                capped = capped or status=='cap'
                suffix = suffix+1 if text and text==previous else 1
                previous = text
            else:
                suffix = 0; previous = None
            messages.append({'id': 'line-'+str(line), 'parent': None, 'turn': r.get('turn', r.get('after_turn')),
                'speaker': r.get('speaker', 'Observer' if r['kind']=='third' else 'Event'),
                'kind': r['kind'], 'segment': 'conversation', 'text': text,
                'thinking': r.get('thinking'), 'thinking_recorded': 'thinking' in r,
                'status': status if main else 'intervention', 'reason': r.get('done_reason'),
                'repeat': bool(main and status=='recorded' and suffix>=6 and text and text.strip()),
                'lines': line_features(text), 'model': header.get('pair_model') if main else header.get('third_model'),
                'tokens': r.get('eval_count'), 'input_tokens': r.get('prompt_eval_count'),
                'wall_seconds': r.get('wall'), 'raw_record': r})
        title = Path(item['source_path']).stem.replace('_run', ' · run ')
        result.append(base_summary({'id': 'ref-'+item['sha256'][:24], 'title': title,
            'collection': 'Reference · stage '+str(item['stage']), 'collection_id': 'stage-'+str(item['stage']),
            'kind': 'reference', 'data_class': 'imported_reference_data', 'models': [header.get('pair_model', 'Unknown')],
            'condition': header.get('cond_name', header.get('cond', 'Unknown')), 'model_kind': header.get('model_kind', 'Not recorded'),
            'date': header.get('started'), 'complete': True, 'prompt': header.get('system'),
            'opening': header.get('opening_user_message'), 'settings': header,
            'source': {'path': str(directory), 'original_path': item['source_path'], 'sha256': item['sha256'],
                'dataset_sha256': manifest['dataset_sha256'], 'revision': manifest.get('source_revision'),
                'verification': 'Imported bytes verified. Historical runtime and missing settings remain unknown.'},
            'messages': messages, 'segments': [{'id': 'conversation', 'parent': None, 'start': 1, 'stop': header.get('turns'), 'history': header.get('mode', 'Not recorded')}],
            'leaves': ['conversation'], 'footer': footer, 'webui_url': None, 'probes': []}))
    return result


def load_campaign(directory):
    path = directory/'events.jsonl'; original = path.read_bytes()
    events = read_events(path); protocol, registry, state = campaign_documents(events)
    turns = {}; rows = {}; nodes = protocol.nodes()
    live = state.meta['backend']!='deterministic-fake/1'
    for n in nodes:
        row = {'id': n.id, 'parent': n.parent, 'turn': n.turn, 'speaker': n.speaker,
            'kind': 'message', 'segment': n.segment, 'text': None, 'thinking': None,
            'thinking_recorded': False, 'model': registry.model(n.model).tag, 'status': 'pending',
            'reason': None, 'repeat': False, 'lines': None, 'tokens': None, 'input_tokens': None,
            'wall_seconds': None, 'request': None, 'seed': n.seed, 'blocking_node': None}
        saved_outcome = state.outcomes.get(n.id); attempt = state.attempts.get(n.id)
        if saved_outcome and saved_outcome[0]=='node_blocked':
            require(n.parent in rows and rows[n.parent]['status'] in ('cap','invalid','blocked'), 'Invalid blocked ancestry')
            row.update(status='blocked', reason=saved_outcome[1]['reason'],
                       blocking_node=rows[n.parent]['blocking_node'] or n.parent)
        elif attempt:
            payload = request(protocol, registry, n, turns)
            saved = state.requests[attempt]
            require(saved['request']==payload and saved['model_digest']==registry.model(n.model).digest, 'Saved request differs from ancestry')
            if live:
                require(saved['model_identity']==read_json(registry.model(n.model).metadata_json), 'Saved model identity differs')
            row['request'] = payload
            response = state.responses.get(attempt)
            if response:
                visible = visible_response(response['raw_response'])
                row.update(text=visible['content'], thinking=visible['thinking'], thinking_recorded=visible['thinking'] is not None,
                           raw_response=response['raw_response'])
                try:
                    raw = read_json(response['raw_response']); usage = raw.get('usage') or {}
                    row.update(tokens=raw.get('eval_count', usage.get('completion_tokens')),
                               input_tokens=raw.get('prompt_eval_count', usage.get('prompt_tokens')))
                except (ValueError, AttributeError): pass
                if saved_outcome:
                    expected = outcome(n, attempt, response['raw_response'], payload, registry.model(n.model) if live else None,
                                       response.get('transport'), state.meta['parser_version'])
                    require(expected==saved_outcome, 'Saved outcome differs from raw evidence')
                    if saved_outcome[0]=='turn_committed':
                        turns[n.id] = turn_from(n, saved_outcome[1])
                        row.update(text=turns[n.id].content, thinking=turns[n.id].thinking, status='valid',
                                   repeat=repeated_state(ancestry(n.id, turns))['active'])
                    else:
                        reason = saved_outcome[1]['reason']
                        row.update(status='cap' if reason=='output_cap' else 'invalid', reason=reason, blocking_node=n.id)
                else: row.update(status='uncommitted', reason='Raw response saved; outcome not committed')
                row['lines'] = line_features(row['text'])
            else: row.update(status='unresolved', reason='Request saved; response unknown')
        rows[n.id] = row
    require(path.read_bytes()==original, 'Campaign changed during indexing; refresh after the writer pauses')
    result = []; doc = read_json(protocol.document_json)
    parents = {s.parent for s in protocol.segments}
    segments = [{'id':s.name, 'parent':s.parent, 'start':s.start, 'stop':s.stop, 'history':s.history} for s in protocol.segments]
    for root in protocol.roots:
        models = [registry.model(label).tag for label in (root.x_model, root.y_model)]
        settings = read_json(protocol.settings_json)
        by_speaker = {speaker: settings.get('by_model',{}).get(label, settings)
                      for speaker,label in (('X',root.x_model),('Y',root.y_model))}
        result.append(base_summary({'id': 'lab-'+fingerprint([events[0]['hash'], root.name])[:24], 'title': root.name,
            'collection': directory.parent.name if directory.parent.name!='workspace' else directory.name,
            'collection_id': 'lab', 'kind': 'lab' if live else 'synthetic', 'data_class': state.meta['data_class'],
            'models': list(dict.fromkeys(models)), 'speakers': dict(zip(('X','Y'), models)),
            'condition': root.x_model+root.y_model+' · '+('/'.join(s['id'] for s in segments) if len(segments)>1 else 'full history'),
            'model_kind': 'Pinned configuration', 'date': events[0].get('at'), 'complete': state.complete,
            'prompt': protocol.system, 'opening': protocol.opening,
            'settings': settings, 'settings_by_speaker': by_speaker,
            'model_identities': [{'speaker':speaker,'tag':registry.model(label).tag,'digest':registry.model(label).digest,
                                  'recorded_runtime_context':(read_json(registry.model(label).metadata_json).get('artifact') or {}).get('expected_health',{}).get('context_window')}
                                 for speaker,label in (('X',root.x_model),('Y',root.y_model))],
            'source': {'path':str(directory), 'sha256':sha256(original), 'journal_head':events[-1]['hash'],
                'protocol_sha256': protocol.digest, 'registry_sha256':registry.digest, 'parser':state.meta['parser_version'],
                'verification':'Journal, saved requests and committed outcomes verified under the recorded parser.'},
            'messages':[rows[n.id] for n in nodes if n.root==root.name], 'segments':segments,
            'leaves':[s['id'] for s in segments if s['id'] not in parents], 'webui_url':None, 'probes':[]}))
    return result


class Catalog:
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve(); self.runs = {}; self.issues = []; self.probes = []
        self.refresh()

    def refresh(self):
        runs = {}; issues = []; probes = []; seen = set(); assessments = []
        # Only shallow experiment directories are discoverable; private files,
        # bundled dependencies and archived software copies are never traversed.
        paths = sorted({p for pattern in ('*/events.jsonl','*/*/events.jsonl') for p in self.workspace.glob(pattern)
                        if not {'private','explorer'}.intersection(p.relative_to(self.workspace).parts)})
        for manifest in sorted(self.workspace.glob('*/manifest.json')):
            if manifest.parent.name in ('private','explorer'): continue
            try:
                if read_json(manifest.read_text()).get('schema')=='behaviorlab.legacy/1':
                    for run in load_legacy(manifest.parent): runs.setdefault(run['id'], run)
            except (ValueError, OSError, KeyError, TypeError) as e:
                issues.append({'source':str(manifest.parent), 'reason':str(e)[:250]})
        for path in paths:
            try:
                with path.open() as f: first = read_json(f.readline())
                if first.get('kind')=='campaign_created':
                    if first['hash'] in seen: continue
                    found = load_campaign(path.parent); seen.add(first['hash'])
                    for run in found: runs[run['id']] = run
                elif first.get('kind')=='participant_comparison_created':
                    if first['hash'] in seen: continue
                    from .participant_explorer import load_participants
                    found=load_participants(path.parent); seen.add(first['hash'])
                    for run in found: runs[run['id']]=run
                elif first.get('kind') in ('cloud_instruction_diagnostic_created','cloud_system_formats_created'):
                    if first['hash'] in seen: continue
                    from .participant_explorer import load_cloud_diagnostics
                    found=load_cloud_diagnostics(path.parent); seen.add(first['hash'])
                    for run in found: runs[run['id']]=run
                elif first.get('kind')=='model_assessment_created':
                    if first['hash'] in seen: continue
                    from .assessment_explorer import load_assessment
                    found,assessment=load_assessment(path.parent); seen.add(first['hash'])
                    assessments.append(assessment)
                    for run in found: runs[run['id']]=run
                elif first.get('kind') in ('framing_comparison_created','paid_framing_created','gpt4o_screen_created'):
                    if first['hash'] in seen: continue
                    from .framing_explorer import load_framing
                    found,assessment=load_framing(path.parent); seen.add(first['hash'])
                    assessments.append(assessment)
                    for run in found: runs[run['id']]=run
                elif first.get('kind')=='mixed_dialogue_created':
                    if first['hash'] in seen: continue
                    from .mixed_explorer import load_mixed
                    found=load_mixed(path.parent); seen.add(first['hash'])
                    for run in found: runs[run['id']]=run
                elif first.get('kind')=='probe_batch_created':
                    from .probes import probe_report
                    result = probe_report(path.parent)
                    probes.append({'path':str(path.parent), 'report':result, 'plan':first['payload']['plan']})
                else: issues.append({'source':str(path.parent), 'reason':'Separate diagnostic journal; not a conversation campaign.'})
            except (ValueError, OSError, KeyError, TypeError, AttributeError) as e:
                issues.append({'source':str(path.parent), 'reason':str(e)[:250]})
        self.assessments=assessments
        for batch in probes:
            plan = batch['plan']
            for run in runs.values():
                if run['source'].get('sha256')==plan['source']['journal_sha256']:
                    ids = {m['id'] for m in run['messages']}
                    run['probes'].append({'path':batch['path'], 'jobs':[j for j in batch['report']['jobs'] if j['snapshot'] in ids]})
        for receipt in self.workspace.glob('*/webui/*.receipt.json'):
            try:
                data = read_json(receipt.read_text()); exported = receipt.with_name(receipt.name.replace('.receipt.json','.json'))
                doc = read_json(exported.read_text()); evidence = doc['chats'][0]['chat']['lab_evidence']
                if not data.get('round_trip_verified') or fingerprint(doc)!=data.get('document_sha256'): continue
                url = urlsplit(data.get('url',''))
                if url.scheme not in ('http','https') or url.hostname not in ('127.0.0.1','localhost'): continue
                for run in runs.values():
                    if run['source'].get('journal_head')==evidence.get('journal_head') and any(m['id']==evidence.get('leaf') for m in run['messages']):
                        run['webui_url'] = data['url']
            except (ValueError, OSError, KeyError, TypeError): continue
        for run in runs.values(): run['experiment']=experiment(run)
        self.runs, self.issues, self.probes = runs, issues, probes
        self.indexed_at = datetime.now(timezone.utc).isoformat()

    def public(self, run, detail=False):
        omit = {'_search','_metadata_search'} if detail else {'_search','_metadata_search','messages','settings','footer','prompt','opening','probes'}
        return {k:v for k,v in run.items() if k not in omit}

    def search(self, params, notes, topic_flags=()):
        get = lambda k, default='': params.get(k,[default])[0]
        q = get('q').strip().casefold(); scope=get('scope','all'); collection=get('collection'); model=get('model'); condition=get('condition'); signal=get('signal'); tag=get('tag')
        notes_by_run = {}
        for n in notes: notes_by_run.setdefault(n['run_id'],[]).append(n)
        selected_topic=get('topic'); require(not selected_topic or selected_topic=='any' or selected_topic in TOPICS,'Unknown topic filter')
        flags_by_run={}
        for f in topic_flags:
            if f.get('source_current'): flags_by_run.setdefault(f['run_id'],[]).append(f)
        candidates = []
        for r in self.runs.values():
            # Keep unstarted assessment slots in their profiles and direct reader,
            # without counting them as observed conversations in the library.
            if r.get('unstarted_assessment') and not tag: continue
            if scope=='all' and r['kind']=='synthetic' or scope in ('reference','lab','synthetic') and r['kind']!=scope: continue
            if collection and r['collection_id']!=collection: continue
            if model and model not in r['models']: continue
            if condition and r['condition']!=condition: continue
            if signal=='capped' and not r['cap_count'] or signal=='repetition' and not r['repeat_count'] or signal=='thinking' and not r['has_thinking'] or signal=='unavailable' and not r['unavailable_count']: continue
            my_notes=notes_by_run.get(r['id'],[])
            if tag and not any(tag in n['tags'] for n in my_notes): continue
            if q and q not in r['_search'] and q not in r['_metadata_search']: continue
            flags=flags_by_run.get(r['id'],[])
            if selected_topic and not any(selected_topic=='any' or selected_topic in f['topics'] for f in flags): continue
            item=self.public(r); item['topic_flags']=flags; item['note_count']=len(my_notes); item['tags']=sorted({t for n in my_notes for t in n['tags']})
            matching=[m for m in r['messages'] if q and q in (m['text'] or '').casefold()]
            item['matches']=[{'id':m['id'],'turn':m['turn'],'text':m['text'][:600] if not q else self.snippet(m['text'],q)} for m in matching[:3]]
            item['match_count']=len(matching)
            # A compact map still represents every unique planned participant node.
            item['timeline']=[{'id':m['id'],'turn':m['turn'],'segment':m['segment'],'status':m['status'],'repeat':m['repeat'],'words':len((m['text'] or '').split())} for m in r['messages'] if m['speaker'] in ('X','Y')]
            candidates.append(item)
        sort=get('sort','recent')
        candidates.sort(key=lambda r: (-r['match_count'], r['title']) if sort=='matches' else (-r['words'],r['title']) if sort=='length' else (r['title'],) if sort=='name' else (str(r['date'] or ''),r['title']), reverse=sort=='recent')
        models=Counter(); groups=Counter()
        for r in candidates:
            for m in r['models']: models[m]+=1
            groups[r['collection_id']]+=1
        offset=max(0,int(get('offset','0'))); limit=min(100,max(1,int(get('limit','40'))))
        return {'total':len(candidates),'offset':offset,'runs':candidates[offset:offset+limit],
            'stats':{'messages':sum(r['message_count'] for r in candidates), 'capped_runs':sum(bool(r['cap_count']) for r in candidates),
                     'repeating_runs':sum(bool(r['repeat_count']) for r in candidates),'unavailable_runs':sum(bool(r['unavailable_count']) for r in candidates)},
            'models':dict(models),'groups':dict(groups)}

    @staticmethod
    def snippet(text, q):
        at=text.casefold().find(q); start=max(0,at-90)
        return ('…' if start else '')+text[start:start+300]+('…' if start+300<len(text) else '')


class Notes:
    def __init__(self, path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, revision INTEGER, deleted INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS history (id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(id,revision))')
        os.chmod(self.path,0o600)

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path)
        try:
            with db: yield db
        finally: db.close()

    def all(self):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT body FROM notes WHERE deleted=0 ORDER BY rowid DESC')]

    def save(self, data, catalog):
        require(isinstance(data,dict), 'Expected note object')
        run=catalog.runs[data['run_id']]; message_id=data.get('message_id'); quote=data.get('quote'); start=data.get('start'); end=data.get('end')
        if message_id:
            message=next((m for m in run['messages'] if m['id']==message_id),None)
            require(message is not None and message['text'] is not None, 'Message unavailable')
            require(type(start) is int and type(end) is int and 0<=start<end<=len(message['text']) and message['text'][start:end]==quote, 'Quote differs from exact source span')
        else: require(all(x is None for x in (quote,start,end)), 'Run note cannot carry an unattributed quote')
        tags=data.get('tags',[]); text=data.get('text','')
        require(isinstance(tags,list) and len(tags)<=15 and all(isinstance(t,str) and 0<len(t.strip())<=60 for t in tags), 'Use up to 15 short tags')
        require(isinstance(text,str) and len(text)<=10000, 'Note is too long')
        require(text.strip() or tags or quote, 'Add a note, tag or passage')
        identity=data.get('id') or secrets.token_hex(12)
        require(isinstance(identity,str) and len(identity)<=100, 'Invalid note identity')
        with self.lock, self.connect() as db:
            existing=db.execute('SELECT revision,deleted,body FROM notes WHERE id=?',(identity,)).fetchone()
            require(not existing or existing[0]==data.get('revision') and not existing[1], 'Note changed; reload before editing')
            if existing:
                prior=json.loads(existing[2]); require(prior['run_id']==run['id'] and prior['message_id']==message_id, 'Note source cannot be reassigned')
            else: require(not data.get('id'), 'Unknown note')
            study_id=data.get('study_id')
            if study_id:
                collection=db.execute('SELECT body FROM research_collections WHERE id=?',(study_id,)).fetchone()
                require(collection is not None and run['id'] in {r['run_id'] for r in json.loads(collection[0])['runs']}, 'Add this run to the collection first')
            revision=existing[0]+1 if existing else 1
            body={'id':identity,'revision':revision,'run_id':run['id'],'run_title':run['title'],'message_id':message_id,
                'quote':quote,'start':start,'end':end,'tags':sorted({t.strip().casefold() for t in tags}),
                'text':text,'source_sha256':run['source']['sha256'],'updated_at':datetime.now(timezone.utc).isoformat(),
                'method':'personal_exploration_not_formal_annotation','author':'Local researcher','study_id':study_id}
            db.execute('INSERT OR REPLACE INTO notes VALUES (?,?,0,?)',(identity,revision,canonical(body)))
            db.execute('INSERT INTO history VALUES (?,?,?)',(identity,revision,canonical(body)))
            return body

    def delete(self,data):
        with self.lock, self.connect() as db:
            existing=db.execute('SELECT revision,deleted,body FROM notes WHERE id=?',(data['id'],)).fetchone()
            require(existing and not existing[1] and existing[0]==data['revision'], 'Note changed; reload before removing')
            body=json.loads(existing[2]); body.update(deleted=True,revision=existing[0]+1,updated_at=datetime.now(timezone.utc).isoformat())
            db.execute('UPDATE notes SET revision=?,deleted=1,body=? WHERE id=?',(body['revision'],canonical(body),data['id']))
            db.execute('INSERT INTO history VALUES (?,?,?)',(data['id'],body['revision'],canonical(body)))
            return {'removed':True}


def make_server(workspace, port=8765):
    catalog=Catalog(workspace); notes=Notes(Path(workspace)/'explorer'/'notes.sqlite'); token=secrets.token_urlsafe(32)
    for run in catalog.runs.values():
        if 'experiment' not in run: run['experiment']=experiment(run)
    studies=ResearchCollections(notes); topics=TopicFlags(notes); topic_atlas=TopicAtlas(notes)
    jev_atlas=JevAtlas(workspace)
    finder_views=FinderViews(notes)
    musings=LabMusings(notes)
    def study_summaries():
        members={d['id']:d['runs'] for d in studies.all()}
        return [dict(s,models=sorted({model for member in members[s['id']] for model in
                     catalog.runs.get(member['run_id'],{}).get('models',[])})) for s in studies.summaries()]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass

        def send(self, data, status=200, mime='application/json; charset=utf-8', download=None):
            body=data if isinstance(data,bytes) else canonical(data).encode()
            self.send_response(status); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if download: self.send_header('Content-Disposition','attachment; filename="'+download+'"')
            self.end_headers(); self.wfile.write(body)

        def allowed(self, write=False):
            hosts={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            host=self.headers.get('Host',''); origin=self.headers.get('Origin')
            return host in hosts and (not origin or origin=='http://'+host) and (not write or origin=='http://'+host and secrets.compare_digest(self.headers.get('X-Explorer-Token',''),token))

        def do_GET(self):
            if not self.allowed(): return self.send({'error':'Local origin required'},403)
            url=urlsplit(self.path); path=url.path
            try:
                if path in ('/','/app.js','/research.js','/assessment.js','/topics.js','/topic-atlas.js','/topic-atlas.css','/jev-atlas.js','/jev-atlas.css','/finder.js','/finder.css','/musings.js','/musings.css','/workbench.js','/workbench.css','/style.css'):
                    file='index.html' if path=='/' else path[1:]
                    return self.send((STATIC/file).read_bytes(),mime='text/html; charset=utf-8' if path=='/' else 'text/css; charset=utf-8' if path.endswith('.css') else 'text/javascript; charset=utf-8')
                if path=='/api/bootstrap':
                    runs=[r for r in catalog.runs.values() if not r.get('unstarted_assessment')]; saved=notes.all()
                    return self.send({'token':token,'indexed_at':catalog.indexed_at,'issues':catalog.issues,
                        'counts':dict(Counter(r['kind'] for r in runs)),
                        'collections':dict(Counter(r['collection_id'] for r in runs if r['kind']!='synthetic')),
                        'models':sorted({m for r in runs if r['kind']!='synthetic' for m in r['models']}),
                        'conditions':sorted({r['condition'] for r in runs if r['kind']!='synthetic'}),
                        'tags':dict(Counter(t for n in saved for t in n['tags'])),
                        'studies':study_summaries(),
                        'model_catalog':{m:model_info(m) for r in catalog.runs.values() for m in r['models']+r['experiment']['models']+r['experiment']['external_models']},
                        'experiments':{r['id']:r['experiment'] for r in runs},
                        'topic_taxonomy':TOPICS,'topic_referents':REFERENTS,'topic_stances':STANCES,'topic_origins':ORIGINS,
                        'reports':[{'id':i,'title':t} for i,t,f in REPORTS if (Path(__file__).resolve().parents[1]/'docs'/f).exists()]})
                if path=='/api/assessments':
                    return self.send({'assessments':[a for a in catalog.assessments if not a['synthetic']],
                        'prior_checks':[{'id':r['id'],'title':r['title'],'models':r['models'],'cost_usd':r.get('cost_usd')}
                                        for r in catalog.runs.values() if r['kind']=='lab' and r['data_class'] in ('cloud_integration_smoke','cloud_integration_diagnostic')]})
                if path=='/api/jev-atlas': return self.send(jev_atlas.index(topic_atlas,studies))
                if path in ('/api/jev-atlas/batch','/api/jev-atlas/export'):
                    q=parse_qs(url.query);detail=(jev_atlas.export if path.endswith('/export') else jev_atlas.detail)(q.get('id',[''])[0],catalog,topic_atlas)
                    return self.send(detail,**({'download':'jev-topic-atlas-'+detail['plan']['id']+'.json'} if path.endswith('/export') else {}))
                if path=='/api/finder':
                    q=parse_qs(url.query)
                    return self.send(finder_result(catalog,json.loads(q.get('filters',['{}'])[0]),studies,q.get('offset',['0'])[0],topic_atlas=topic_atlas))
                if path=='/api/finder/views': return self.send({'views':finder_views.all()})
                if path=='/api/finder/export': return self.send(finder_views.export(),download='conversation-finder-views.json')
                if path in ('/api/workbench','/api/workbench/export'):
                    q=parse_qs(url.query,keep_blank_values=True);picks=q.get('picks',[None])[0]
                    result=build_workbench(catalog,studies,topic_atlas,q.get('cohort',[''])[0],None if picks is None else [i for i in picks.split(',') if i])
                    return self.send(result,**({'download':'opening-comparison.json'} if path.endswith('/export') else {}))
                if path=='/api/musings': return self.send({'entries':musings.all(),'kinds':MUSING_KINDS,'statuses':MUSING_STATUSES})
                if path=='/api/musings/export': return self.send(musings.export(),download='lab-purpose-and-musings.json')
                if path.startswith('/api/musings/history/'):
                    return self.send({'history':musings.history(path.rsplit('/',1)[-1])})
                if path=='/api/studies': return self.send({'collections':study_summaries()})
                if path.startswith('/api/studies/'):
                    parts=path.split('/')
                    if len(parts)==5 and parts[4]=='export': return self.send(studies.export(parts[3],catalog),download='research-collection-'+parts[3]+'.json')
                    require(len(parts)==4,'Unknown collection route')
                    return self.send(studies.detail(parts[3],catalog))
                if path=='/api/topics': return self.send({'flags':topics.all(catalog)})
                if path=='/api/topics/export': return self.send(topics.export(catalog),download='behavior-lab-topic-flags.json')
                if path in ('/api/topic-atlas','/api/topic-atlas/export'):
                    q=parse_qs(url.query);args=[catalog,studies,q.get('cohort',['all'])[0],q.get('subject',['emergence'])[0],q.get('participant_model',[''])[0]]
                    if path.endswith('/export'):return self.send(topic_atlas.export(*args),download='behavior-lab-topic-atlas.json')
                    return self.send(topic_atlas.analyze(*args))
                if path=='/api/runs': return self.send(catalog.search(parse_qs(url.query),notes.all(),topics.all(catalog)))
                if path.startswith('/api/runs/'):
                    run=catalog.runs[path.rsplit('/',1)[-1]]
                    return self.send(dict(catalog.public(run,True),topic_flags=[f for f in topics.all(catalog) if f['run_id']==run['id']],notes=[n for n in notes.all() if n['run_id']==run['id']]))
                if path=='/api/notes': return self.send({'notes':notes.all()})
                if path=='/api/notes/export': return self.send({'schema':'behaviorlab.exploration-notes/1','notes':notes.all()},download='behavior-lab-notebook.json')
                if path.startswith('/api/reports/'):
                    item=next((r for r in REPORTS if r[0]==path.rsplit('/',1)[-1]),None)
                    require(item is not None,'Unknown report')
                    text=(Path(__file__).resolve().parents[1]/'docs'/item[2]).read_text()
                    return self.send({'title':item[1],'markdown':text})
                return self.send({'error':'Not found'},404)
            except (ValueError,KeyError,TypeError,StopIteration,OSError) as e:
                self.send({'error':str(e)[:250]},400)

        def do_POST(self):
            if not self.allowed(True): return self.send({'error':'Local authenticated request required'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                limit=524288 if self.path=='/api/studies' else 262144 if self.path=='/api/musings' else 65536
                require(0<size<=limit and self.headers.get('Content-Type')=='application/json','Expected a small JSON request')
                data=read_json(self.rfile.read(size).decode())
                if self.path=='/api/jev-atlas/prepare': return self.send(jev_atlas.prepare(data,catalog,topic_atlas,studies))
                if self.path=='/api/jev-atlas/review': return self.send(jev_atlas.save_review(data,catalog))
                if self.path=='/api/musings': return self.send(musings.save(data,{d['id'] for d in studies.summaries()}))
                if self.path=='/api/finder/views': return self.send(finder_views.save(data))
                if self.path=='/api/studies': return self.send(studies.save(data,catalog))
                if self.path=='/api/topics': return self.send(topics.save(data,catalog))
                if self.path=='/api/topics/remove': return self.send(topics.delete(data))
                if self.path=='/api/topic-atlas/dictionary': return self.send(topic_atlas.save_entry(data))
                if self.path=='/api/topic-atlas/openings': return self.send(topic_atlas.save_review(data,catalog))
                if self.path=='/api/notes': return self.send(notes.save(data,catalog))
                if self.path=='/api/notes/remove': return self.send(notes.delete(data))
                if self.path=='/api/refresh': catalog.refresh(); return self.send({'refreshed':True})
                return self.send({'error':'Not found'},404)
            except (ValueError,KeyError,TypeError,UnicodeDecodeError) as e:
                self.send({'error':str(e)[:250]},400)
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.catalog=catalog; server.notes=notes; server.studies=studies; server.topics=topics
    return server


def serve(workspace,port=8765):
    print('Indexing local conversation evidence…',flush=True)
    server=make_server(workspace,port)
    print(f'Behavior Lab Explorer · http://127.0.0.1:{server.server_port} · {len(server.catalog.runs)} runs',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
