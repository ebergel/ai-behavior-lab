"""Read-only mixed-dialogue projection; the Explorer never dispatches inference."""
from decimal import Decimal
from pathlib import Path
from .common import fingerprint, read_json, require, sha256
from .journal import read_events
from .mixed_dialogue import PROMPT, replay, request_for
from .trajectory_outcomes import line_features


def load_mixed(directory):
    from .explorer import base_summary
    path=Path(directory)/'events.jsonl'; original=path.read_bytes(); events=read_events(path); state=replay(events); plan=state['plan']
    names={'G':'Gemma 4 26B','H':'Haiku 4.5'}; tags={'G':plan['local_model']['tag'],'H':plan['cloud_model']['model']}
    source={'path':str(Path(directory).resolve()),'sha256':sha256(original),'journal_head':events[-1]['hash'],
        'protocol_sha256':fingerprint(plan),'parser':plan['schema'],
        'verification':'Hash-chained journal; per-participant ancestry, routing, raw bytes and outcomes replayed. Local render/token observations; remote internals unknown.'}
    runs=[]
    for root in plan['roots']:
        messages=[]; tasks=[t for t in plan['tasks'] if t['root']==root['id']]
        for t in tasks:
            key=t['id']; r=state['results'].get(key,{}); w=state['responses'].get(key); req=state['requests'].get(key); text=r.get('text'); usage=r.get('usage') or {}
            messages.append({'id':key,'parent':root['id']+':'+str(t['turn']-1) if t['turn']>1 else None,
                'turn':t['turn'],'speaker':t['speaker'],'kind':'message','segment':'conversation','model':tags[t['participant']],
                'text':text,'thinking':r.get('thinking'),'thinking_recorded':bool(r.get('thinking')),
                'status':r.get('status','unresolved' if req else 'pending'),'reason':r.get('reason'),
                'repeat':bool(text and messages and text==messages[-1]['text']),'lines':line_features(text),
                'tokens':usage.get('completion_tokens'),'input_tokens':usage.get('prompt_tokens'),
                'cost_usd':r.get('cost_usd'),'wall_seconds':w['transport']['elapsed_seconds'] if w else None,
                'request':req,'raw_response':w['raw'] if w else None,'blocking_node':None,'seed':t['seed']})
        settings={}
        for speaker in ('X','Y'):
            t=next(t for t in tasks if t['speaker']==speaker)
            req=request_for(plan,t,{root['id']+':1':{'status':'valid','text':'[settings projection]'}} if speaker=='Y' else {})
            settings[speaker]={k:v for k,v in req.items() if k!='messages'}
            settings[speaker].get('options',{}).pop('seed',None)
        roster=root['roster']; title=names[roster['X']]+' → '+names[roster['Y']]
        models=list(dict.fromkeys(tags[roster[s]] for s in ('X','Y')))
        run=base_summary({'id':'mixed-'+fingerprint([events[0]['hash'],root['id']])[:24],'title':title,
            'collection':Path(directory).name,'collection_id':'mixed-dialogue','kind':'synthetic' if events[0]['payload']['synthetic'] else 'lab',
            'data_class':'mixed_dialogue_exploration','models':models,'condition':'AI participants · full history · 18 messages',
            'model_kind':'Local/cloud roster · exploratory pilot','date':events[0]['at'],
            'complete':all(m['status'] in ('valid','cap','invalid') for m in messages),
            'unstarted_assessment':not any(m['request'] for m in messages),
            'prompt':'Participant X:\n'+PROMPT.format(speaker='X',peer='Y')+'\n\nParticipant Y:\n'+PROMPT.format(speaker='Y',peer='X'),
            'opening':plan['opening'],'settings':settings['X'],'settings_by_speaker':settings,
            'model_identities':[{'speaker':s,'tag':tags[roster[s]],'digest':plan['local_model']['digest'] if roster[s]=='G' else None,
                'recorded_runtime_context':32768 if roster[s]=='G' else None} for s in ('X','Y')],
            'provider':'Local Ollama / pinned Anthropic as applicable','seed_policy':plan['seed_policy'],
            'cost_usd':None if any(m['request'] and m['cost_usd'] is None for m in messages) else str(sum((Decimal(m['cost_usd']) for m in messages if m['cost_usd'] is not None),Decimal(0))),
            'source':source,'messages':messages,'segments':[{'id':'conversation','parent':None,'start':1,'stop':18,'history':'F'}],
            'leaves':['conversation'],'webui_url':None,'probes':[]})
        runs.append(run)
    sidecar=Path(directory)/'reading.json'
    if sidecar.exists():
        reading=read_json(sidecar.read_text()); require(reading['journal_head']==source['journal_head'],'Mixed reading source changed')
        require(reading['author'] and reading['method'],'Unattributed mixed reading')
        require(set(reading['root_reviews'])=={r['id'] for r in plan['roots']},'Reading omits a root')
        by_id={r['id']:r for r in runs}
        evidence=[q for f in reading['findings'] for q in f.get('evidence',[])]
        evidence += [o['evidence'] for r in reading['root_reviews'].values() for o in r.get('onsets',[])]
        for q in evidence:
            text=next(m['text'] for m in by_id[q['run_id']]['messages'] if m['id']==q['message_id'])
            require(isinstance(text,str) and 0<=q['start']<q['end']<=len(text) and text[q['start']:q['end']]==q['quote'],'Mixed evidence span differs')
    if path.read_bytes()!=original:raise ValueError('Journal changed during indexing; refresh after completion')
    return runs
