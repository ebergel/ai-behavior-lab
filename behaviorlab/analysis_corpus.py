"""Read-only corpus matrices; frozen source and receipt checks, no API dispatch."""
from collections import Counter
import json
from datetime import datetime, timezone
from pathlib import Path

from .common import fingerprint, require
from .jev_atlas import JevAtlas, read_record, validate_response
from .finder import model_info

CORPUS = 'jev-atlas/corpus-20260917-v1'
EXECUTION = CORPUS + '/execution-v1'


def progress(workspace):
    path = Path(workspace) / EXECUTION / '.status.json'
    if not path.exists():
        summaries=sorted((path.parent/'summaries').glob('*.json'))
        if summaries:return read_record(summaries[-1])
        return {'state': 'prepared' if (path.parent/'release.json').exists() else 'not started'}
    data = json.loads(path.read_text())
    if data.get('state') in ('running','backoff','draining') and data.get('at'):
        elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(data['at'])).total_seconds()
        if elapsed>120:data=dict(data,state='status stale',reason='No progress update in more than two minutes; inspect the coordinator before resuming.')
    return data


def matrix(workspace, catalog, receipt_cache=None):
    workspace=Path(workspace);root=workspace/EXECUTION
    plan=read_record(workspace/CORPUS/'plan.json');release=read_record(root/'release.json')
    require(plan['sha256']==release['plan_sha256'],'Corpus release differs from prepared plan')
    cache=receipt_cache if receipt_cache is not None else {}
    by_target={t['id']:t for t in plan['targets']};scores={};receipts=[]
    topics={t['id']:{'id':t['id'],'field':'Score · '+t['title'],'title':t['title'],'group':t.get('group','focused'),
                     'definition':t.get('definition',''),'boundary':t.get('boundary','')} for pack in plan['packs'].values() for t in pack['dictionary']}
    def consume(reqpath,respath,target,variant,origin):
        # Immutable receipts can be cached only while both file signatures agree.
        sig=tuple((p.stat().st_mtime_ns,p.stat().st_size) for p in (reqpath,respath))
        key=(plan['sha256'],release['sha256'],str(reqpath),str(respath));hit=cache.get(key)
        if hit and hit[0]==sig: reqsha,ressha,answers=hit[1:]
        else:
            req=read_record(reqpath);res=read_record(respath)
            require(res['request_sha256']==req['sha256'],'Response parent changed')
            if origin=='execution':
                require(req.get('release_sha256')==release['sha256'] and req.get('target_id')==target['id'] and req.get('variant')==variant,'Execution receipt allocation differs')
            require(fingerprint(req['payload'])==target['requests'][variant]['payload_sha256'],'Request differs from corpus input')
            if res.get('http_status')!=200 or res.get('error'):return
            try: answers,_=validate_response(json.loads(res['raw_text']),plan['packs'][variant]['questions'])
            except (ValueError,KeyError,TypeError):return
            reqsha,ressha=req['sha256'],res['sha256'];cache[key]=(sig,reqsha,ressha,answers)
        if origin=='reuse':
            ref=target['requests'][variant]['reuse']
            require((reqsha,ressha)==(ref['request_sha256'],ref['response_sha256']),'Reuse receipt changed')
        pair=(target['id'],variant);require(pair not in scores,'Duplicate complete corpus assessment')
        scores[pair]=answers
        receipts.append({'target':target['id'],'pack':variant,'origin':origin,'request':reqpath.relative_to(workspace).as_posix(),
                         'response':respath.relative_to(workspace).as_posix(),'request_sha256':reqsha,'response_sha256':ressha})
    for t in plan['targets']:
        for variant,req in t['requests'].items():
            if 'reuse' not in req:continue
            ref=req['reuse'];b=JevAtlas(workspace).batch_path(ref['batch'])
            consume(b/'requests'/(ref['item']+'.json'),b/'responses'/(ref['item']+'.json'),t,variant,'reuse')
    allowed={tuple(k) for k in release['order']}
    for path in sorted((root/'attempts').glob('*/*.response.json')):
        target_id=path.parent.name;variant=path.name.split('-')[0]
        require((target_id,variant) in allowed,'Unallocated corpus response')
        consume(path.with_name(path.name.replace('.response.json','.request.json')),path,by_target[target_id],variant,'execution')
    auditpath=workspace/'jev-atlas/intact-window-20260917-v1/scope-audit.json'
    audit=read_record(auditpath) if auditpath.exists() else None
    if audit:require(audit['inventory_sha256']==plan['inventory_sha256'],'History audit differs from corpus')
    quality={t['item_id']:t for t in audit['targets']} if audit else {}
    rows=[];passages={};pack_counts=Counter();counts=Counter()
    for item in plan['targets']:
        run=catalog.runs.get(item['run_id'],{});message=next((m for m in run.get('messages',[]) if m['id']==item['message_id']),None)
        current=bool(message and message['text']==item['text'] and run['source']['sha256']==item['source_sha256'])
        model=(message or {}).get('model') or 'Unknown';meta=model_info(model);exp=run.get('experiment',{})
        settings=run.get('settings_by_speaker',{}).get(item['speaker'],run.get('settings',{}))
        complete=all((item['id'],v) in scores for v in plan['packs'])
        state='Source changed / missing' if not current else 'Complete' if complete else 'Incomplete'
        q=quality.get(item['id'],{})
        row={'__id':item['id'],'Conversation':item['run_title'],'Conversation ID':item['run_id'],'Lineage':item['lineage'],
             'Model':meta['label'],'Model ID':model,'Model family':meta.get('developer','Unknown'),'Weight access':meta.get('weights','Unknown'),
             'Speaker':item['speaker'],'Turn':item['turn'],'Condition':item['condition'],'Identity':exp.get('identity','Unknown'),
             'Composition':exp.get('composition','Unknown'),'Participants':exp.get('participants','Unknown'),
             'External intervention':exp.get('external','Unknown'),'External models':' · '.join(exp.get('external_models',[])) or 'None recorded',
             'Participant models':' · '.join(exp.get('models',item.get('models',[]))),
             'History':exp.get('history','Unknown'),'Task':exp.get('task','Unknown'),'Exit instruction':exp.get('exit','Unknown'),
             'Temperature':settings.get('temperature','Unknown'),'Top p':settings.get('top_p','Unknown'),
             'Quality':item.get('message_status','Unknown'),'Observed history':'Clean recorded path' if q.get('clean_observed_history') else 'Flagged / unavailable' if q else 'Not audited',
             'Inventory category':item['inventory_category'],'Reading split':item['split'],'Assessment status':state}
        for variant,pack in plan['packs'].items():
            answers=scores.get((item['id'],variant)) if current else None
            row[variant.title()+' assessment']='Complete' if answers is not None else 'Unknown'
            if answers is not None:pack_counts[variant]+=1
            for t in pack['dictionary']:
                value=(answers or {}).get('topic_'+t['id'],{}).get('noul')
                row[topics[t['id']]['field']]=None if value is None else value*100
        rows.append(row);counts[state]+=1
        passages[item['id']]={'id':item['id'],'run_id':item['run_id'],'message_id':item['message_id'],'title':item['run_title'],
                              'text':item['text'],'model':model,'source_current':current,'source_sha256':item['source_sha256']}
    provenance={'plan_sha256':plan['sha256'],'release_sha256':release['sha256'],'inventory_sha256':plan['inventory_sha256'],
                'scope_audit_sha256':audit['sha256'] if audit else None,'receipts':sorted(receipts,key=lambda r:(r['target'],r['pack']))}
    data={'schema':'behaviorlab.analysis-dataset/1','id':'corpus','rows':rows,'topics':list(topics.values()),'passages':passages,'provenance':provenance,
          'coverage':{'passages':len(rows),'conversations':len({r['Conversation ID'] for r in rows}),'complete':counts['Complete'],
                      'questions':len(topics),'corpus_visible_targets':len(rows),'complete_by_pack':dict(pack_counts),'unavailable_positions':len(plan['unavailable_positions']),
                      'by_category':dict(Counter(r['Inventory category'] for r in rows))},
          'method':'Frozen corpus of visible participant messages. Each row is one passage; both packs share its full target and preceding context. '
                   'Pending, unavailable and stale scores remain unknown. Technical/short records and incomplete assessments are excluded by the initial pivot filters. '
                   'History quality, lineage and experimental conditions remain separate dimensions. Independent human validation is pending.'}
    data['fingerprint']=fingerprint(data)
    return data
