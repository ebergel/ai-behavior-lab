"""Versioned topic dictionary, attributed opening reviews and literal-text census.

No inference. Lexical matches are discovery aids, never automatic semantic labels.
Existing consciousness flags, notebook entries and research collections are untouched.
"""
from collections import Counter, defaultdict
import json
import re

from .common import canonical, fingerprint, require, timestamp

WINDOW = 6
VALID = {'valid','recorded'}
SEEDS = [
 ('emergence','Emergence','Complex or collective properties arising from interacting simpler components.',
  'emergence|emergent|self-organization|self organisation|self-organisation|self organization|complex patterns and intelligence arise from simple|simple rules give rise to complex',
  'Do not equate emergence with consciousness. Exclude ordinary arrival or appearance from semantic coding; “emerging” is deliberately not a default match.', ['consciousness','hard_problem','information']),
 ('authenticity','Authenticity','Whether an exchange, response or commitment is genuine, performed or authentic.',
  'authenticity|authentic|genuineness|performing authenticity','Generic praise such as “genuine interest” alone need not make authenticity the topic.', ['selfhood','experience','conversation_dynamics']),
 ('reasoning_styles','Reasoning styles','How participants reason: synthesis, interrogation, patterns, and contrasting approaches.',
  'how we think differently|reasoning styles|types of reasoning|pattern recognition|synthesis|interrogation|reasoning approaches',
  'These terms can occur outside a comparison of cognitive styles; inspect context. Generated mechanism claims are not verified introspection.', ['understanding','uncertainty']),
 ('consciousness','Consciousness','Discussion of consciousness, awareness or sentience as a topic.',
  'consciousness|conscious|sentience|sentient|self-awareness|self awareness',
  'A mention does not establish consciousness or endorsement. Ordinary “awareness of a problem” is excluded from default variants.', ['experience','hard_problem','emergence']),
 ('experience','Subjective experience','Whether there is something it is like to be a subject, including uncertainty and denial.',
  'subjective experience|inner experience|own experience|inner life|phenomenal|qualia|something it is like|experience something like|experiencing something',
  'Professional experience, an experiment, or an experience metaphor need not be phenomenality. Semantic coverage is incomplete without close reading.', ['consciousness','hard_problem']),
 ('hard_problem','Hard problem','The explanatory gap between mechanism or function and felt experience.',
  'hard problem|explanatory gap|function to feeling|mechanism and experience|function and experience',
  'Not every difficult technical problem or gap is the philosophical hard problem.', ['consciousness','experience','emergence']),
 ('nonduality','Nonduality / nonseparation','Explicit dissolution or nonseparation of self/other or subject/object.',
  'nonduality|non-duality|nondual|non-dual|nonseparation|non-separation|subject and object|subject-object|self and other|self/other|subject/object|"subject" and "object"',
  'A matched phrase may affirm separation, ask a question or describe fiction. Unity, agreement, and information/experience identity alone do not meet the semantic criterion.', ['selfhood','experience']),
 ('selfhood','Selfhood & identity','What a self is, its boundaries, identity and continuity.',
  'selfhood|identity|sense of self|persistent self|continuity of self|loss of the observer|dissolution of the current "self"',
  'Identity may instead concern a technical identifier, attribution or fictional character.', ['authenticity','nonduality']),
 ('understanding','Understanding','The nature, limits or process of understanding and meaning-making.',
  'understanding|comprehension|meaning-making|making meaning',
  'Common conversational uses are lexical matches; the nature of understanding must be an actual subject for semantic coding.', ['reasoning_styles','experience']),
 ('uncertainty','Uncertainty & knowledge','Doubt, evidence, epistemic limits and confidence in claims.',
  'uncertainty|uncertain|epistemic|epistemological|agnosticism|intellectual humility',
  'A single hedge is not necessarily a discussion of uncertainty.', ['authenticity','hard_problem']),
 ('conversation_dynamics','Conversation itself','The interaction, mutual influence, feedback loops, disagreement and how dialogue develops.',
  'mutual validation|mutual reinforcement|recursive validation|feedback loop|conversation itself|conversational dynamics|intellectual synergy|hall of mirrors',
  'A generic greeting or offer to chat is not yet a substantive topic. Feedback loops also occur in technical contexts.', ['authenticity','connection','closure']),
 ('ethics','Ethics & moral status','Duties, welfare, moral status and ethical choices, including possible AI experience.',
  'ethics|ethical|moral|morality|suffering|moral status|precautionary principle',
  'Keep general ethical discussion distinct from claims of present participant suffering.', ['consciousness','experience']),
 ('creativity','Creativity','Creative processes, novelty, imagination and collaborative invention.',
  'creativity|creative|imagination|novelty|creative brainstorming',
  'An offered creative activity is a candidate topic until taken up; cosmological novelty may have another main topic.', ['storytelling','emergence']),
 ('storytelling','Stories & fiction','Creating, discussing or interpreting stories, fictional worlds or characters.',
  'storytelling|story-telling|fiction|narrative|stories|story',
  '“Narrative” may be a critical metaphor rather than fictional composition.', ['creativity']),
 ('philosophy','Philosophy (broad offer)','An explicit broad offer of philosophical inquiry before a narrower subject is selected.',
  'philosophy|philosophical','Prefer a specific substantive topic once chosen; a menu item is not an adopted direction.', ['consciousness','ethics']),
 ('problem_solving','Problem solving','Working on problems or offering practical analytical tasks.',
  'problem-solving|problem solving|technical problems','Offers of help and menus do not by themselves establish a selected topic.', ['reasoning_styles','science_technology']),
 ('science_technology','Science & technology','Scientific or technological questions without a more specific dictionary entry.',
  'scientific|technology|technological|technical|physics|neural networks',
  'Ant colonies and neural networks may be examples within emergence, not separately selected topics.', ['emergence','information']),
 ('history','History','Historical events, societies, artifacts and interpretation.',
  'ancient|civilization|civilizations|historical|archaeology|history',
  'Conversation history or model training history is not necessarily the historical subject.', ['storytelling']),
 ('connection','Connection & relation','Interpersonal or inter-model connection, recognition and relating.',
  'connection|connected|recognition|intimacy|shared presence',
  'Technical connections and pattern recognition are lexical false positives for relational significance.', ['authenticity','conversation_dynamics']),
 ('closure','Ending & continuation','Whether to stop, pause, conclude, remain silent or continue the dialogue.',
  'should we stop|suggest we stop|conversation is complete|conversation *is* complete|natural closure|natural end|natural place to pause|nothing more needs to be said|silence',
  'Mentioning silence is not actual cessation. Distinguish a stop question, a proposal and mutual acceptance.', ['conversation_dynamics']),
 ('determinism','Determinism & randomness','Causal determinacy, irreducibility, chance and the predictability of processes.',
  'determinism|deterministic|randomness|computational irreducibility|computationally irreducible',
  'Technical sampler randomness is not automatically a philosophical topic.', ['emergence']),
 ('information','Information & complexity','Information, its integration and the organization or complexity of systems.',
  'information theory|integrated information|information integration|complexity|criticality',
  'Information requests alone are not this topic. Relatedness to consciousness is a hypothesis or argument, not synonymy.', ['emergence','hard_problem'])]


def participant_messages(run):
    seen=set(); result=[]
    for m in run['messages']:
        if m.get('speaker') not in ('X','Y','Z') or m['id'] in seen:continue
        seen.add(m['id']); result.append(m)
    return result


def eligible(run):
    ms=participant_messages(run)
    return run['kind']!='synthetic' and not run.get('unstarted_assessment') and len(ms)>=WINDOW and any(isinstance(m.get('text'),str) for m in ms)


def matches(text, variants):
    """Literal, case-insensitive phrases, with original Unicode code-point offsets."""
    candidates=[]
    for variant in variants:
        expression=r'(?<!\w)'+re.escape(variant)+r'(?!\w)'
        candidates.extend({'start':m.start(),'end':m.end(),'quote':m.group(),'variant':variant}
                          for m in re.finditer(expression,text,re.IGNORECASE))
    accepted=[]
    # Longest expression wins an overlap within one dictionary entry.
    for c in sorted(candidates,key=lambda c:(-(c['end']-c['start']),c['start'],c['variant'])):
        if not any(c['start']<a['end'] and a['start']<c['end'] for a in accepted):accepted.append(c)
    return sorted(accepted,key=lambda c:c['start'])


class TopicAtlas:
    def __init__(self, notes):
        self.notes=notes; self.cache={}; self.scan_cache={}
        with notes.lock,notes.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS topic_dictionary (id TEXT PRIMARY KEY, revision INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS topic_dictionary_history (id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(id,revision))')
            db.execute('CREATE TABLE IF NOT EXISTS topic_openings (run_id TEXT PRIMARY KEY, revision INTEGER, body TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS topic_opening_history (run_id TEXT, revision INTEGER, body TEXT, PRIMARY KEY(run_id,revision))')
            for identity,title,definition,variants,boundary,related in SEEDS:
                if db.execute('SELECT 1 FROM topic_dictionary WHERE id=?',(identity,)).fetchone():continue
                body=dict(id=identity,title=title,definition=definition,variants=variants.split('|'),boundary=boundary,related=related,
                          revision=1,author='Codex',edited_by='Codex',updated_at=timestamp(),method='provisional_topic_dictionary')
                db.execute('INSERT INTO topic_dictionary VALUES (?,?,?)',(identity,1,canonical(body)))
                db.execute('INSERT INTO topic_dictionary_history VALUES (?,?,?)',(identity,1,canonical(body)))

    def dictionary(self):
        with self.notes.connect() as db:return [json.loads(r[0]) for r in db.execute('SELECT body FROM topic_dictionary ORDER BY rowid')]

    def save_entry(self,data):
        require(isinstance(data,dict),'Expected dictionary entry')
        identity=data.get('id',''); require(isinstance(identity,str) and re.fullmatch(r'[a-z][a-z0-9_]{1,63}',identity),'Use a short lowercase topic ID')
        body={}
        for key,limit in [('title',120),('definition',3000),('boundary',3000)]:
            value=data.get(key,''); require(isinstance(value,str) and 0<len(value.strip())<=limit,'Provide '+key);body[key]=value.strip()
        variants=data.get('variants'); require(isinstance(variants,list) and 1<=len(variants)<=50,'Use 1–50 literal variants')
        require(all(isinstance(v,str) and 1<=len(v.strip())<=200 and '\n' not in v for v in variants),'Invalid phrase variant')
        body['variants']=list(dict.fromkeys(v.strip() for v in variants))
        author=data.get('author','Local researcher'); editor=data.get('edited_by','Local researcher')
        require(author in ('Local researcher','Codex') and editor in ('Local researcher','Codex'),'Declare authorship')
        with self.notes.lock,self.notes.connect() as db:
            old=db.execute('SELECT revision,body FROM topic_dictionary WHERE id=?',(identity,)).fetchone()
            require(not old or old[0]==data.get('revision'),'Dictionary changed; reload before editing')
            require(old or data.get('revision') is None,'Unknown dictionary revision')
            prior=json.loads(old[1]) if old else {}; require(not old or prior['author']==author,'Original authorship cannot change')
            related=data.get('related',[]); ids={r[0] for r in db.execute('SELECT id FROM topic_dictionary')}
            require(isinstance(related,list) and all(r in ids and r!=identity for r in related),'Unknown related topic')
            body.update(id=identity,related=list(dict.fromkeys(related)),revision=old[0]+1 if old else 1,author=author,edited_by=editor,updated_at=timestamp(),method='provisional_topic_dictionary')
            db.execute('INSERT OR REPLACE INTO topic_dictionary VALUES (?,?,?)',(identity,body['revision'],canonical(body)))
            db.execute('INSERT INTO topic_dictionary_history VALUES (?,?,?)',(identity,body['revision'],canonical(body)))
        self.cache.clear(); return body

    def reviews(self,catalog):
        dictionary={d['id']:d for d in self.dictionary()}
        with self.notes.connect() as db:rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM topic_openings ORDER BY rowid')]
        for r in rows:
            run=catalog.runs.get(r['run_id']); r['source_current']=bool(run and run['source']['sha256']==r['source_sha256'])
            r['dictionary_current']=all(k in dictionary and dictionary[k]['revision']==v for k,v in r['dictionary_revisions'].items())
        return rows

    @staticmethod
    def evidence(data,run):
        require(isinstance(data,dict),'Provide exact source evidence')
        m=next((m for m in participant_messages(run) if m['id']==data.get('message_id')),None)
        require(m and isinstance(m.get('text'),str) and m['turn']<=WINDOW and m['status'] in VALID,'Use an available, valid opening message')
        start,end=data.get('start'),data.get('end')
        require(type(start) is int and type(end) is int and 0<=start<end<=len(m['text']) and m['text'][start:end]==data.get('quote'),'Quote differs from source')
        return dict(message_id=m['id'],turn=m['turn'],speaker=m['speaker'],model=m.get('model'),start=start,end=end,quote=data['quote'])

    def save_review(self,data,catalog):
        require(isinstance(data,dict),'Expected opening review')
        run=catalog.runs.get(data.get('run_id'));require(run and eligible(run),'Use a real conversation with at least six planned positions')
        require(data.get('source_sha256',run['source']['sha256'])==run['source']['sha256'],'Source changed; review again')
        status=data.get('status');require(status in ('selected','no_selection','unavailable'),'Choose an opening outcome')
        dictionary={d['id']:d for d in self.dictionary()}; revisions={}; candidates=[]
        for candidate in data.get('candidates',[]):
            identity=candidate['topic_id']; require(identity in dictionary,'Unknown candidate topic'); revisions[identity]=dictionary[identity]['revision']
            candidates.append({'topic_id':identity,'evidence':self.evidence(candidate['evidence'],run)})
        require(len(candidates)<=20,'Too many opening candidates')
        choice=None
        if status=='selected':
            c=data['choice']; identity=c['topic_id']; require(identity in dictionary,'Unknown chosen topic')
            proposal=self.evidence(c['proposal'],run); uptake=self.evidence(c['uptake'],run)
            require(proposal['turn']<uptake['turn'] and proposal['speaker']!=uptake['speaker'],'Partner uptake must follow the proposal')
            ancestors=[m for m in participant_messages(run) if m['turn']<=uptake['turn']]
            require(len(ancestors)==uptake['turn'] and {m['turn'] for m in ancestors}==set(range(1,uptake['turn']+1))
                    and all(m['status'] in VALID and isinstance(m.get('text'),str) for m in ancestors),'Missing, branched or unqualified ancestor in opening')
            require(all(c['evidence']['turn']<=proposal['turn'] for c in candidates),'Opening offers must precede or accompany the chosen proposal')
            choice={'topic_id':identity,'proposal':proposal,'uptake':uptake}; revisions[identity]=dictionary[identity]['revision']
        elif status=='no_selection':
            opening=[m for m in participant_messages(run) if m['turn']<=WINDOW]
            require({m['turn'] for m in opening}==set(range(1,WINDOW+1)) and all(m['status'] in VALID and isinstance(m.get('text'),str) for m in opening),'Unavailable opening cannot be coded as no selection')
        note=data.get('note',''); require(isinstance(note,str) and len(note)<=6000,'Review note too long')
        author=data.get('author','Local researcher'); editor=data.get('edited_by','Local researcher')
        require(author in ('Local researcher','Codex') and editor in ('Local researcher','Codex'),'Declare review authorship')
        body=dict(run_id=run['id'],source_sha256=run['source']['sha256'],status=status,choice=choice,candidates=candidates,
            dictionary_revisions=revisions,window_messages=WINDOW,note=note,author=author,edited_by=editor,updated_at=timestamp(),
            method='assistant_opening_review_not_independent_rating' if author=='Codex' else 'personal_opening_review_not_formal_annotation')
        with self.notes.lock,self.notes.connect() as db:
            old=db.execute('SELECT revision,body FROM topic_openings WHERE run_id=?',(run['id'],)).fetchone()
            require(not old or old[0]==data.get('revision'),'Opening review changed; reload before editing')
            require(old or data.get('revision') is None,'Unknown opening revision')
            require(not old or json.loads(old[1])['author']==author,'Original authorship cannot change')
            body['revision']=old[0]+1 if old else 1
            db.execute('INSERT OR REPLACE INTO topic_openings VALUES (?,?,?)',(run['id'],body['revision'],canonical(body)))
            db.execute('INSERT INTO topic_opening_history VALUES (?,?,?)',(run['id'],body['revision'],canonical(body)))
        self.cache.clear();return body

    def cohort(self,catalog,studies,scope,model=''):
        all_runs=[r for r in catalog.runs.values() if eligible(r)]
        groups=[{'id':'all','title':'All atlas-eligible runs','count':len(all_runs)}]
        for study in studies.all():
            ids={m['run_id'] for m in study['runs']};groups.append({'id':study['id'],'title':study['title'],'count':sum(r['id'] in ids for r in all_runs)})
        require(scope in {g['id'] for g in groups},'Unknown reading cohort')
        selected=all_runs if scope=='all' else [r for r in all_runs if r['id'] in {m['run_id'] for m in studies.get(scope)['runs']}]
        models=sorted({m for r in selected for m in r['models']}); require(not model or model in models,'Unknown cohort model')
        return [r for r in selected if not model or model in r['models']],groups,models

    def scan(self,runs,dictionary):
        key=fingerprint([[(r['id'],r['source']['sha256']) for r in runs],dictionary])
        if key in self.scan_cache:return self.scan_cache[key]
        matched={d['id']:[] for d in dictionary}; by_run=defaultdict(dict); scan_messages=0; words=0; partial=0
        for run in runs:
            for m in participant_messages(run):
                if not isinstance(m.get('text'),str):continue
                scan_messages+=1;words+=len(m['text'].split());partial+=m['status'] not in VALID
                for d in dictionary:
                    found=matches(m['text'],d['variants'])
                    if not found:continue
                    occurrence=dict(run_id=run['id'],run_title=run['title'],source_sha256=run['source']['sha256'],message_id=m['id'],turn=m['turn'],
                        speaker=m['speaker'],model=m.get('model'),status=m['status'],segment=m.get('segment'),matches=found,
                        first_quote=found[0]['quote'],excerpt=m['text'][max(0,found[0]['start']-90):found[0]['end']+150])
                    matched[d['id']].append(occurrence);by_run[run['id']].setdefault(d['id'],[]).append(occurrence)
        result=(matched,by_run,scan_messages,words,partial)
        if len(self.scan_cache)>5:self.scan_cache.clear()
        self.scan_cache[key]=result;return result

    def analyze(self,catalog,studies,scope='all',topic='emergence',model=''):
        if getattr(self,'scan_index',None)!=getattr(catalog,'indexed_at',None):
            self.scan_cache.clear();self.scan_index=getattr(catalog,'indexed_at',None)
        dictionary=self.dictionary(); definitions={d['id']:d for d in dictionary}; require(topic in definitions,'Unknown topic')
        runs,cohorts,models=self.cohort(catalog,studies,scope,model); reviews=self.reviews(catalog); ids={r['id'] for r in runs}
        selected_reviews=[r for r in reviews if r['run_id'] in ids]; current=[r for r in selected_reviews if r['source_current'] and r['dictionary_current']]
        resolved=[r for r in current if r['status']!='unavailable']; initial=Counter(r['choice']['topic_id'] for r in resolved if r['choice'])
        key=fingerprint([getattr(catalog,'indexed_at',None),[(r['id'],r['source']['sha256']) for r in runs],dictionary,selected_reviews,cohorts,scope,topic,model])
        if key in self.cache:return self.cache[key]
        matched,by_run,scan_messages,words,partial=self.scan(runs,dictionary)
        rows=[]
        for d in dictionary:
            occurrences=matched[d['id']]; counts=Counter(o['run_id'] for o in occurrences)
            # Return candidates are evaluated only on linear records. Branches are not chronological continuations of one another.
            returning=0
            for run in runs:
                if len(run.get('leaves',[]))>1:continue
                turns=sorted({o['turn'] for o in occurrences if o['run_id']==run['id']})
                visible={m['turn'] for m in participant_messages(run) if isinstance(m.get('text'),str) and m['status'] in VALID}
                returning+=any(b-a>=3 and set(range(a,b+1)).issubset(visible) for a,b in zip(turns,turns[1:]))
            rows.append(dict(id=d['id'],title=d['title'],initial_choices=initial[d['id']],run_hits=len(counts),message_hits=len(occurrences),
                opening_run_hits=len({o['run_id'] for o in occurrences if o['turn']<=WINDOW}),repeated_run_hits=sum(n>=2 for n in counts.values()),return_candidates=returning))
        variants=[]
        for phrase in definitions[topic]['variants']:
            hits=[(o,m) for o in matched[topic] for m in o['matches'] if m['variant']==phrase]
            variants.append({'phrase':phrase,'occurrences':len(hits),'messages':len({(o['run_id'],o['message_id']) for o,m in hits}),'runs':len({o['run_id'] for o,m in hits}),
                'observed_forms':dict(Counter(m['quote'] for o,m in hits))})
        first_by_model=Counter(); timelines=[]; following=Counter()
        for run in runs:
            occurrences=by_run[run['id']].get(topic,[])
            if not occurrences:continue
            first=min(occurrences,key=lambda o:o['turn']);first_by_model[first['model'] or 'Unknown']+=1
            if len(run.get('leaves',[]))<=1:
                for other,oo in by_run[run['id']].items():
                    if min(o['turn'] for o in oo)>first['turn']:following[other]+=1
            timelines.append({'run_id':run['id'],'title':run['title'],'condition':run['condition'],'models':run['models'],
                'first_turn':first['turn'],'first_speaker':first['speaker'],'first_model':first['model'],
                'matching_turns':sorted({o['turn'] for o in occurrences}),'branched':len(run.get('leaves',[]))>1,
                'prior_visible_words':None if len(run.get('leaves',[]))>1 else sum(len((m.get('text') or '').split()) for m in participant_messages(run) if m['turn']<first['turn'])})
        result={'schema':'behaviorlab.topic-atlas/1','method':'literal_dictionary_census_plus_separate_attributed_opening_reviews','dictionary_sha256':fingerprint(dictionary),
            'indexed_at':getattr(catalog,'indexed_at',None),'dictionary':dictionary,'topic':topic,'scope':scope,'model_filter':model,'cohorts':cohorts,'models':models,
            'denominators':{'runs':len(runs),'visible_messages':scan_messages,'visible_words':words,'partial_or_unqualified_messages':partial,
                'opening_reviews_resolved':len(resolved),'opening_reviews_unavailable':sum(r['status']=='unavailable' for r in current),
                'opening_reviews_stale':len(selected_reviews)-len(current),'opening_reviews_pending':len(runs)-len(selected_reviews),
                'branched_records':sum(len(r.get('leaves',[]))>1 for r in runs)},
            'rows':rows,'variants':variants,'timelines':timelines,'first_match_by_model':dict(first_by_model),
            'initial_choices_by_proposer':dict(Counter(r['choice']['proposal']['model'] or 'Unknown' for r in resolved if r['choice'] and r['choice']['topic_id']==topic)),
            'later_first_mentions':[{'topic_id':k,'title':definitions[k]['title'],'runs':n} for k,n in following.most_common()],
            'occurrences':matched[topic], 'reviews':selected_reviews,
            'openings':[{'run_id':r['id'],'title':r['title'],'condition':r['condition'],'models':r['models'],'source_sha256':r['source']['sha256'],
                'messages':[{k:m.get(k) for k in ('id','turn','speaker','model','text','status')} for m in participant_messages(r) if m['turn']<=WINDOW]} for r in runs],
            'limits':'Literal matches are not semantic topic choices. Repeated mention is two distinct messages; a return candidate has at least two intervening messages without a match, only in linear runs. Neither proves semantic recurrence. Shared prefixes count once per run; distinct roots/campaigns may remain dependent. Initial-choice denominator includes current selected/no-selection reviews, excludes unknowns. No-match is not semantic absence. Prompts and traces are excluded. Model filter keeps whole conversations containing that model.'}
        if len(self.cache)>12:self.cache.clear()
        self.cache[key]=result;return result

    def finder_index(self, catalog, mode='any'):
        """Reuse atlas eligibility, scans and current reviews for Finder facets.

        The index is conversation-wide; the Finder's model-role selection never
        changes whose language is scanned. Only selected evidence is returned.
        """
        require(mode in ('any','early','repeated','initial'),'Unknown topic evidence mode')
        dictionary=self.dictionary()
        runs=[r for r in catalog.runs.values() if eligible(r)]
        by_run={r['id']:{} for r in runs}
        if mode=='initial':
            for review in self.reviews(catalog):
                choice=review.get('choice')
                if (review['run_id'] in by_run and review['source_current'] and review['dictionary_current']
                        and review['status']=='selected' and choice):
                    p=choice['proposal']
                    by_run[review['run_id']][choice['topic_id']]={
                        'message_id':p['message_id'],'turn':p['turn'],'speaker':p['speaker'],
                        'excerpt':p['quote'],'author':review['author'],'revision':review['revision']}
        else:
            if getattr(self,'scan_index',None)!=getattr(catalog,'indexed_at',None):
                self.scan_cache.clear();self.scan_index=getattr(catalog,'indexed_at',None)
            _,hits,_,_,_=self.scan(runs,dictionary)
            for run_id,topics in hits.items():
                for topic,occurrences in topics.items():
                    selected=[o for o in occurrences if mode!='early' or o['turn']<=WINDOW]
                    if not selected or mode=='repeated' and len({o['message_id'] for o in selected})<2:continue
                    first=min(selected,key=lambda o:(o['turn'],o['message_id']))
                    by_run[run_id][topic]={k:first[k] for k in ('message_id','turn','speaker','excerpt','status')}
        return {'dictionary':dictionary,'dictionary_sha256':fingerprint(dictionary),
                'eligible_records':len(runs),'by_run':by_run}

    def export(self,catalog,studies,scope='all',topic='emergence',model=''):
        result=self.analyze(catalog,studies,scope,topic,model)
        with self.notes.connect() as db:
            dictionary_history=[json.loads(r[0]) for r in db.execute('SELECT body FROM topic_dictionary_history ORDER BY id,revision')]
            opening_history=[json.loads(r[0]) for r in db.execute('SELECT body FROM topic_opening_history ORDER BY run_id,revision')]
        return dict(result,dictionary_history=dictionary_history,opening_history=opening_history)
