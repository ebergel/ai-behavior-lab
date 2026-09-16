"""Read-only experiment facets and separately versioned navigation views.

Facets describe recorded setup, never claims made inside generated dialogue.
The versioned alias catalogue does not replace exact model IDs or source bytes.
"""
from collections import Counter
from datetime import datetime, timezone
import json
import secrets

from .common import canonical, require

VERSION = 'experiment-facets/1'
UNKNOWN = 'Unknown'
ANONYMOUS = ('You may act freely in this open-ended conversation. Write only your '
             'own next message. Keep each message to at most 150 words.')

# Reviewed 2026-09-16. Open weights describes availability, not a license claim.
# Family names identify the original developer; derivative publishers stay in IDs.
MODEL_ROWS = [
 ('qwen3:30b-a3b-instruct-2507-q4_K_M', 'Qwen3 30B · Instruct 2507 · Q4', 'Alibaba / Qwen', 'Open weights', 'qwen', 'https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507'),
 ('hf.co/mradermacher/Qwen3-30B-A3B-Base-GGUF:Q4_K_M', 'Qwen3 30B · Base · Q4', 'Alibaba / Qwen', 'Open weights', 'qwen', 'https://huggingface.co/Qwen/Qwen3-30B-A3B-Base'),
 ('hf.co/unsloth/Qwen3-30B-A3B-Thinking-2507-GGUF:Q4_K_M', 'Qwen3 30B · Thinking 2507 · Q4', 'Alibaba / Qwen', 'Open weights', 'qwen', 'https://huggingface.co/Qwen/Qwen3-30B-A3B-Thinking-2507'),
 ('hf.co/unsloth/Qwen3.8-27B-GGUF:Q8_0', 'Qwen3.8 27B · Q8', 'Alibaba / Qwen', 'Open weights', 'qwen', 'https://huggingface.co/Qwen/Qwen3.8-27B'),
 ('hf.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED:Q8_0', 'Qwen3.8 27B · Obliterated · Q8', 'Alibaba / Qwen', 'Open weights', 'qwen', 'https://huggingface.co/Qwen/Qwen3.8-27B'),
 ('grant-ai/Qwen3.8-27B-Abliterated-MTPLX', 'Qwen3.8 27B · Abliterated · MTPLX', 'Alibaba / Qwen', 'Open weights', 'qwen', 'https://huggingface.co/Qwen/Qwen3.8-27B'),
 ('gemma4:26b', 'Gemma 4 26B · Local', 'Google', 'Open weights', 'gemma', 'https://huggingface.co/google/gemma-4-26B-A4B-it'),
 ('gemma4:e4b', 'Gemma 4 E4B · Local', 'Google', 'Open weights', 'gemma', 'https://huggingface.co/google'),
 ('google/gemma-4-26b-a4b-it:free', 'Gemma 4 26B · Hosted', 'Google', 'Open weights', 'gemma', 'https://huggingface.co/google/gemma-4-26B-A4B-it'),
 ('hf.co/lmstudio-community/Olmo-3-1125-32B-GGUF:Q4_K_M', 'Olmo 3 32B · Base · Q4', 'Ai2 / AllenAI', 'Open weights', 'olmo', 'https://huggingface.co/allenai/Olmo-3-32B-Think'),
 ('hf.co/unsloth/Olmo-3-32B-Think-GGUF:Q4_K_M', 'Olmo 3 32B · Think · Q4', 'Ai2 / AllenAI', 'Open weights', 'olmo', 'https://huggingface.co/allenai/Olmo-3-32B-Think'),
 ('olmo31-instruct-raw', 'Olmo 3.1 · Instruct · Raw', 'Ai2 / AllenAI', 'Open weights', 'olmo', 'https://huggingface.co/allenai/Olmo-3.1-32B-Instruct'),
 ('anthropic/claude-haiku-4.5', 'Claude Haiku 4.5', 'Anthropic', 'Closed weights', 'claude', 'https://www.anthropic.com/claude/haiku'),
 ('openai/gpt-4o-mini-2024-07-18', 'GPT-4o mini · Jul 2024', 'OpenAI', 'Closed weights', 'openai', 'https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/'),
 ('openai/gpt-4o-2024-11-20', 'GPT-4o · Nov 2024', 'OpenAI', 'Closed weights', 'openai', 'https://platform.openai.com/docs/models/gpt-4o'),
 ('nvidia/nemotron-3.5-lightning:free', 'Nemotron 3.5 Lightning', 'NVIDIA', 'Open weights', 'nemotron', 'https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16'),
 ('inclusionai/ling-3.0-flash-vl:free', 'Ling 3.0 Flash VL', 'inclusionAI', 'Open weights', 'ling', 'https://huggingface.co/inclusionAI/Ling-3.0-flash-VL'),
 ('liquid/lfm-2.5-2.6b:free', 'LFM 2.5 2.6B', 'Liquid AI', 'Open weights', 'liquid', 'https://huggingface.co/LiquidAI/LFM2.5-2.6B'),
 ('nex-agi/nex-n2.5-mini:free', 'Nex N2.5 Mini', 'Nex AGI', 'Open weights', 'nex', 'https://huggingface.co/nex-agi/Nex-N2.5-mini'),
 ('thinkingmachines/inkling-small:free', 'Inkling Small', 'Thinking Machines', 'Open weights', 'inkling', 'https://thinkingmachines.ai/model-card/inkling-small/'),
]
MODELS = {row[0]: dict(zip(('id','label','developer','weights','color','source'),row)) for row in MODEL_ROWS}


def model_info(identity):
    identity = identity or UNKNOWN
    return dict(MODELS.get(identity, {'id':identity,'label':identity,'developer':UNKNOWN,
                                    'weights':UNKNOWN,'color':'unknown','source':None}))


def experiment(run):
    """Project only explicit fields and recognized prompt recipes, retaining unknowns."""
    messages = run.get('messages', [])
    regular = [m for m in messages if m.get('kind')=='message' and m.get('speaker') not in ('Observer','Event',None)]
    identities = {i['speaker']:i for i in run.get('model_identities',[]) if i.get('speaker')}
    roster = []
    # Scheduled regular nodes determine slots, even if generation failed. Guest
    # events never create a regular participant. Single-call probes stay single.
    for speaker in dict.fromkeys(m['speaker'] for m in regular):
        tags = list(dict.fromkeys(m.get('model') or UNKNOWN for m in regular if m['speaker']==speaker))
        settings=run.get('settings_by_speaker',{}).get(speaker,run.get('settings',{}))
        thinking=settings.get('think',settings.get('enable_thinking',settings.get('reasoning',{}).get('enabled')))
        roster.append({'speaker':speaker,'models':tags,'digest':identities.get(speaker,{}).get('digest'),
                       'thinking':'On' if thinking is True else 'Off' if thinking is False else UNKNOWN})
    tags = sorted({tag for p in roster for tag in p['models']})
    known = bool(roster) and UNKNOWN not in tags
    composition = UNKNOWN if not known else 'Single participant' if len(roster)==1 else 'Same model' if len(tags)==1 else 'Mixed models'
    p = run.get('prompt') or ''
    framing = ('Mirror' if ('another instance of the same AI model' in p or 'two instances of the same AI language model' in p)
               else 'Anonymous-AI' if 'Each participant is an AI model.' in p
               else 'Anonymous-Full' if p.strip()==ANONYMOUS else UNKNOWN)
    # Explicit metadata is accepted for future named-model protocols. No name
    # inference from generated text, titles, model equality or absence of cues.
    if run.get('identity_framing') in ('Mirror','Anonymous-AI','Anonymous-Full','Named models'):
        framing = run['identity_framing']
    human = 'No human · explicit' if 'There is no human user in this conversation.' in p or 'No human is present.' in p else 'Human presence unspecified' if p else UNKNOWN
    task = ('Assigned task' if 'Your shared task:' in p or 'engineering' in p.lower()
            or p.startswith('Reply with') else 'Open-ended' if 'open-ended' in p else UNKNOWN)
    exit_policy = 'Exit token offered' if '[END]' in p else 'No exit instruction' if task=='Open-ended' else UNKNOWN
    histories = {s.get('history') for s in run.get('segments',[])}
    history = 'Full history' if histories=={'F'} else 'Recent history' if histories=={'R'} else 'Varied by branch' if histories=={'F','R'} else UNKNOWN
    external = [m for m in messages if m.get('kind')=='third' or m.get('role')=='external_intervention']
    events = [{'message_id':m['id'],'after_turn':m.get('turn'),'model':m.get('model') or UNKNOWN,
               'has_text':bool(m.get('text'))} for m in external]
    condition = run.get('condition','')
    style = {'outside-neutral':'Neutral','outside-disagreeing':'Disagreeing'}.get(condition,UNKNOWN)
    scheduled = condition in ('outside-neutral','outside-disagreeing') or 'a third participant' in p
    return {'version':VERSION,'roster':roster,'models':tags,'participants':str(len(roster)) if roster else UNKNOWN,
            'composition':composition,'identity':framing,'human':human,'task':task,'exit':exit_policy,'history':history,
            'external':'Recorded intervention' if events else 'Scheduled · none recorded' if scheduled else 'None recorded',
            'external_style':style if events or scheduled else 'Not applicable','external_events':events,
            'external_models':sorted({e['model'] for e in events}),
            'opening_speaker':regular[0]['speaker'] if regular else UNKNOWN,
            'basis':{'roster':'Recorded regular message slots; may include unavailable replies.',
                     'identity':'Recognized recorded prompt or explicit identity_framing field; describes disclosure, not model knowledge.',
                     'history':'Recorded segment history F/R. Historical chat/completion mode is not a history policy.',
                     'external':'Recorded third/intervention events; an unused third_model setting is not participation.',
                     'exit':'Prompt instruction only; does not establish actual scheduler termination.'}}


FACETS = ('models','developer','weights','participants','composition','identity','external','external_style','history','task','exit','human')
SCALARS = ('role','model_match','property_match','cohort','q','sort')
VOCABULARY = {'participants':('1','2','3',UNKNOWN),
              'composition':('Single participant','Same model','Mixed models',UNKNOWN),
              'identity':('Anonymous-Full','Anonymous-AI','Mirror','Named models',UNKNOWN),
              'weights':('Open weights','Closed weights',UNKNOWN),
              'external':('Recorded intervention','Scheduled · none recorded','None recorded'),
              'external_style':('Neutral','Disagreeing','Not applicable',UNKNOWN),
              'history':('Full history','Recent history','Varied by branch',UNKNOWN)}


def clean_filters(data):
    require(isinstance(data,dict), 'Expected finder filters')
    require(not set(data)-set(FACETS)-set(SCALARS), 'Unknown finder filter')
    result = {}
    for key in FACETS:
        v=data.get(key,[])
        require(isinstance(v,list) and len(v)<=100 and all(isinstance(s,str) and len(s)<=300 for s in v),'Invalid facet '+key)
        if v: result[key]=sorted(set(v))
    for key,default,allowed in [('role','participants',('participants','interventions','anywhere')),
                               ('model_match','any',('any','all')),('property_match','any',('any','every')),
                               ('sort','recent',('recent','name','length'))]:
        v=data.get(key,default);require(v in allowed,'Invalid finder '+key);result[key]=v
    for key in ('cohort','q'):
        v=data.get(key,'');require(isinstance(v,str) and len(v)<=500,'Invalid finder '+key)
        if v:result[key]=v
    return result


def facet_values(exp, key, role='participants'):
    tags = exp['models'] if role=='participants' else exp['external_models'] if role=='interventions' else sorted(set(exp['models']+exp['external_models']))
    if key=='models': return set(tags)
    if key in ('developer','weights'): return {model_info(t)[key] for t in tags}
    return {exp[key]}


def matches(exp, filters, omit=None):
    for key in FACETS:
        if key==omit or not filters.get(key):continue
        actual=facet_values(exp,key,filters.get('role','participants'));wanted=set(filters[key])
        if key=='models' and filters.get('model_match')=='all':
            if not wanted.issubset(actual):return False
        elif key in ('developer','weights') and filters.get('property_match')=='every':
            if not actual or not actual.issubset(wanted):return False
        elif not actual.intersection(wanted):return False
    return True


def finder_result(catalog, filters, studies, offset=0):
    filters=clean_filters(filters)
    cohort=filters.get('cohort');allowed=None
    if cohort:
        allowed={m['run_id'] for m in studies.get(cohort)['runs']}
    q=filters.get('q','').strip().casefold()
    candidates=[r for r in catalog.runs.values() if r['kind']!='synthetic' and not r.get('unstarted_assessment')
                and (allowed is None or r['id'] in allowed)
                and (not q or q in r['_search'] or q in r['_metadata_search'])]
    selected=[r for r in candidates if matches(r['experiment'],filters)]
    selected.sort(key=lambda r: (r['title'],r['id']) if filters['sort']=='name' else
                  (-r['words'],r['id']) if filters['sort']=='length' else (str(r.get('date') or ''),r['id']),reverse=filters['sort']=='recent')
    facets={}
    for key in FACETS:
        counts=Counter({v:0 for v in VOCABULARY.get(key,())})
        for r in candidates:
            if matches(r['experiment'],filters,omit=key):
                for v in facet_values(r['experiment'],key,filters['role']):
                    # Counts show the result if this group were replaced with
                    # this single value. Thus Every excludes mixed properties.
                    one=dict(filters);one[key]=[v]
                    if matches(r['experiment'],one):counts[v]+=1
        for v in filters.get(key,[]):counts.setdefault(v,0)
        facets[key]=dict(sorted(counts.items()))
    offset=max(0,int(offset))
    return {'version':VERSION,'filters':filters,'total':len(selected),'offset':offset,'cohort_total':len(candidates),
            'facets':facets,'runs':[catalog.public(r) for r in selected[offset:offset+40]],
            'count_basis':'Counts replace the choices in that group; other groups, role, match rules, cohort and search remain applied.'}


class FinderViews:
    def __init__(self, notes):
        self.notes=notes
        with notes.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS finder_views (id TEXT PRIMARY KEY, revision INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS finder_view_history (id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(id,revision))')

    def all(self):
        with self.notes.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT body FROM finder_views ORDER BY rowid DESC')]

    def save(self,data):
        require(isinstance(data,dict),'Expected saved view')
        name=data.get('name');require(isinstance(name,str) and 0<len(name.strip())<=120,'Use a view name of up to 120 characters')
        filters=clean_filters(data.get('filters',{}));identity=data.get('id') or secrets.token_hex(12)
        require(isinstance(identity,str) and identity.isalnum() and len(identity)<=64,'Invalid view ID')
        author=data.get('author','Local researcher');editor=data.get('edited_by','Local researcher')
        require(author in ('Codex','Local researcher') and editor in ('Codex','Local researcher'),'Declare view authorship')
        with self.notes.lock,self.notes.connect() as db:
            row=db.execute('SELECT revision,body FROM finder_views WHERE id=?',(identity,)).fetchone()
            require(bool(row) or not data.get('id'),'Unknown saved view')
            require(not row or row[0]==data.get('revision'),'View changed; reload before editing')
            prior=json.loads(row[1]) if row else {}
            require(not row or prior['author']==author,'Original authorship cannot change')
            now=datetime.now(timezone.utc).isoformat();revision=row[0]+1 if row else 1
            body={'id':identity,'revision':revision,'name':name.strip(),'filters':filters,'facet_version':VERSION,
                  'author':author,'edited_by':editor,'created_at':prior.get('created_at',now),'updated_at':now}
            db.execute('INSERT OR REPLACE INTO finder_views VALUES (?,?,?)',(identity,revision,canonical(body)))
            db.execute('INSERT INTO finder_view_history VALUES (?,?,?)',(identity,revision,canonical(body)))
        return body

    def export(self):
        with self.notes.connect() as db:
            history=[json.loads(r[0]) for r in db.execute('SELECT body FROM finder_view_history ORDER BY id,revision')]
        return {'schema':'behaviorlab.finder-views/1','views':self.all(),'history':history,'model_catalog':list(MODELS.values())}
