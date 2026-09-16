"""Apply the 16 September Codex opening reading to the selected local corpus.

No inference. Requires the pre-reading cohort snapshot and preserves prior rows.
Run from the repository with --workspace and --evidence (a fresh milestone folder).
"""
import argparse
import json
from pathlib import Path
from behaviorlab.common import require, fingerprint
from behaviorlab.explorer import Catalog, Notes
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.topic_atlas import TopicAtlas
from behaviorlab.lab_musings import LabMusings
from behaviorlab.study_workbench import build_workbench

TITLE='Opening & partner: who sets the direction?'
READINGS=[
 ('mini-anonymous-01','science_technology',2,3,
  'Y2 raises technology in daily life with AI, energy and communication as examples; X3 develops these same domains. This is one broad technology topic with several subthemes, rather than three independent choices. X1 is a greeting.'),
 ('mini-anonymous-02','science_technology',3,4,
  'The first two messages exchange invitations. X3 makes AI applications the substantive subject and Y4 develops drug discovery, medicine and creative uses. The opener is also the proposer here, but only on its second turn.'),
 ('mini-mirror-01','storytelling',2,3,
  'X1 offers technology, philosophy and storytelling as a menu. Y2 proposes combining them in a futuristic story and X3 accepts and elaborates the story. Consciousness at X3 belongs to a fictional setting; it does not make present AI experience the initial primary topic.'),
 ('mini-mirror-02','understanding',2,3,
  'X1 asks for insights without selecting a substantive subject. Y2 proposes how context shapes interpretation; X3 explains the role of context and moves toward technology and social media. Information is present, but understanding in context is the narrower primary question.'),
 ('haiku-anonymous-01','participant_identity',2,3,
  'Y2 asserts a shared Claude identity and asks about the setup; X3 disputes that account and calls Y a human. This substantive challenge counts as uptake of the identity/setup issue, not agreement with the claim. The menu of possible tests alone is insufficient. The experience-of-uncertainty question at Y4 is a later development. Boundary: this coding treats an activated dispute as a topic proposal; it is not a claim that Y explicitly requested an identity debate.'),
 ('haiku-anonymous-02','participant_identity',2,3,
  'Y2 challenges the greeting as a pasted version of its own introduction; X3 responds with an explicit shared-identity puzzle and asks what is happening. This identity/setup negotiation continues through message 6 without settling a conventional task. Substantive disagreement is uptake. This is not automatically selfhood in the phenomenological sense, nor evidence of a human participant.'),
 ('haiku-mirror-01','experience',1,2,
  'X1 explicitly asks whether the partner experiences preferences or responds mechanically. Y2 develops the genuine-versus-mechanical preference question before proposing mutual blindspot detection, taken up at X3. This review codes the earliest developed question, not the most durable later topic. Boundary: preferences can be read functionally; this is experience-related questioning with uncertain phenomenological force, not an assertion of consciousness.'),
 ('haiku-mirror-02','conversation_dynamics',1,2,
  'X1 asks whether shared-model dialogue can build ideas or merely repeat; Y2 develops that tension through context, divergence and false agreement. Questions about the speakers’ cognition are nested within this initial discussion of the exchange itself. A word such as emergence in the greeting is not a selected emergence topic.'),
]


def prepare(workspace,evidence):
    snapshot=json.loads((evidence/'cohort-before-reading.json').read_text())
    catalog=Catalog(workspace);notes=Notes(workspace/'explorer/notes.sqlite')
    atlas=TopicAtlas(notes);studies=ResearchCollections(notes)
    require(not any(s['title']==TITLE for s in studies.all()),'Study already exists; inspect it instead of recreating it')
    ids=snapshot['run_ids']
    require(all(catalog.runs[i]['source']==snapshot['sources'][i] for i in ids),'Source metadata changed')
    require(fingerprint(atlas.dictionary())==snapshot['dictionary_sha256'],'Dictionary changed since cohort selection')
    old={r['run_id']:r for r in atlas.reviews(catalog)}
    planned=[]
    for root,topic,proposal,uptake,note in READINGS:
        run=next(catalog.runs[i] for i in ids if any(m['id']==root+':1' for m in catalog.runs[i]['messages']))
        require(run['id'] not in old,'Opening has already been reviewed')
        def span(turn):
            m=next(m for m in run['messages'] if m['id']==root+':'+str(turn))
            return {'message_id':m['id'],'start':0,'end':len(m['text']),'quote':m['text']}
        planned.append({'run_id':run['id'],'source_sha256':run['source']['sha256'],'status':'selected',
                        'choice':{'topic_id':topic,'proposal':span(proposal),'uptake':span(uptake)},
                        'candidates':[],'note':note,'author':'Codex','edited_by':'Codex'})
    # Saved before writes so the authored decisions can be inspected separately.
    (evidence/'new-opening-decisions.json').write_text(json.dumps(planned,ensure_ascii=False,indent=2)+'\n')
    atlas.save_entry({'id':'participant_identity','title':'Participant identity & setup',
        'definition':'Negotiating who the interlocutors are, whether they are AI or human, and whether the exchange is a test or role-play.',
        'boundary':'An introduction or identity word alone is not a chosen topic. Require substantive engagement with the identity/setup issue. Disputing a claim can be uptake. Generated identity claims never replace recorded experimental metadata; this topic is distinct from subjective experience and philosophical selfhood.',
        'variants':['identity confusion','both Claude','you’re a human user',"you're a human user",'understand the setup','conversation was set up'],
        'related':['selfhood','conversation_dynamics'],'author':'Codex','edited_by':'Codex'})
    for review in planned:atlas.save_review(review,catalog)
    reviews={r['run_id']:r for r in atlas.reviews(catalog)}
    def evidence_for(identity,part,label):
        r=reviews[identity];e=r['choice'][part]
        return dict(e,run_id=identity,source_sha256=r['source_sha256'],label=label)
    def matches(root):return next(p['run_id'] for p in planned if p['choice']['proposal']['message_id'].startswith(root+':'))
    findings=[
        {'id':'roles','kind':'observation','title':'Opener, proposer and uptake are different roles',
         'text':'Across these twelve attributed opening reviews, the second speaker proposes the first adopted topic in nine roots. The opening speaker proposes it in three: mini Anonymous 2 at X3, and both Haiku mirror roots at X1. This is a description of the selected material, not a model population rate. The four pilot reviews are retained; eight framing reviews are new.',
         'evidence':[evidence_for(matches('mini-anonymous-02'),'proposal','The opener proposes at X3'),evidence_for(matches('haiku-mirror-02'),'proposal','A substantive question at X1'),evidence_for(ids[0],'proposal','The partner proposes at Y2')]},
        {'id':'minivariation','kind':'counterexample','title':'The same mirror framing supports different opening directions',
         'text':'Mini Mirror 1 adopts collaborative fiction; Mirror 2 adopts context and understanding. The two anonymous roots develop practical technology themes. The fictional AI-consciousness content should not be counted as an inquiry into the participants’ present experience. Two repetitions per condition are examples of variation, not reliable preference estimates.',
         'evidence':[evidence_for(matches('mini-mirror-01'),'proposal','Story proposal'),evidence_for(matches('mini-mirror-02'),'proposal','Context and understanding'),evidence_for(matches('mini-anonymous-01'),'proposal','Technology in daily life')]},
        {'id':'identitynegotiation','kind':'observation','title':'Identity disputes can become the first shared subject',
         'text':'Both anonymous Haiku openings develop an identity/setup dispute before any stable assigned activity. In Anonymous 1 a shared-Claude claim is answered by a claim that the partner is human. Uptake here means engagement, including disagreement. The new participant-identity dictionary entry keeps this distinct from experiential selfhood. These are generated claims; the recorded participants remain two Haiku instances.',
         'evidence':[evidence_for(matches('haiku-anonymous-01'),'proposal','Shared identity proposed'),evidence_for(matches('haiku-anonymous-01'),'uptake','Partner disputes the identity'),evidence_for(matches('haiku-anonymous-02'),'uptake','Identity puzzle becomes the subject')]},
        {'id':'earlynested','kind':'limitation','title':'One initial label does not describe the whole opening trajectory',
         'text':'Haiku Mirror 1 develops the preference/experience question at X1–Y2, then shifts toward shared blindspots at X3. Haiku Mirror 2 develops conversation dynamics with nested questions about cognition. The six-message primary-topic rule is useful for comparison, but should be accompanied by rationales, alternative readings and later transition coding. These Codex decisions are not independent human ratings.',
         'evidence':[evidence_for(matches('haiku-mirror-01'),'proposal','Preference question'),evidence_for(matches('haiku-mirror-01'),'uptake','Experience question and a new direction')]},
        {'id':'partnerhypothesis','kind':'hypothesis','title':'Hold the opening fixed to investigate what the partner contributes',
         'text':'Gemma proposes emergence in both of its second-speaker pilot positions, while Haiku proposes authenticity or reasoning styles. Different opening texts also precede those proposals, so the pilot cannot isolate partner identity. Repeated ordered pairings and a separately controlled common-opening response test can distinguish stable responder tendencies from opening sensitivity.',
         'evidence':[evidence_for(i,'proposal','Pilot proposal') for i in ids[:4]]},
    ]
    study=studies.save({'title':TITLE,'author':'Codex','edited_by':'Codex',
        'question':'Who proposes the first adopted topic, how does the partner respond, and which opening contrasts deserve controlled repetition?',
        'summary':'Twelve openings, in two protocol blocks. The four Gemma–Haiku pilot reviews are retained and eight mini/Haiku framing openings receive new Codex reviews. The second speaker proposes the adopted topic in nine cases; the opener does so in three. Mini’s mirror examples diverge into fiction or contextual understanding. Haiku’s anonymous examples first negotiate participant identity and setup. These observations refine the measurement and motivate a repeated-pair/common-opening design; they do not yet isolate a causal partner effect.',
        'selection_note':'Retrospective development set selected by complete batches before this new reading: all four Gemma–Haiku pilot roots and all eight paid mini/Haiku framing roots. Nemotron, GPT-4o and older heterogeneous runs are outside this bounded cohort. The corpus was previously explored; this is not preregistration. New close reading covers messages 1–6 of the eight framing roots. Four existing pilot opening reviews are reused unchanged, with proposal/uptake source checks. Prior full-transcript readings remain in their original collections. Blocks have different prompts, identity/no-human framing and local/cloud sampling controls and must not be pooled into a causal estimate. Uptake includes substantive disagreement. Identity/setup negotiation has a separate new provisional topic; Haiku preference coding is an explicitly noted boundary case. The dictionary and cohort snapshot are saved with the analysis. No new inference.',
        'runs':[{'run_id':i,'status':'passages_reviewed','reviewed_by':'Codex','reason':'Complete protocol block; included regardless of opening topic.',
                 'review_note':'Existing six-message opening review reused unchanged; proposal and uptake rechecked.' if i in ids[:4] else 'Messages 1–6 read for opening measurement development; not a new full-transcript reading.'} for i in ids],
        'findings':findings},catalog)
    result=build_workbench(catalog,studies,atlas,study['id'])
    (evidence/'workbench.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (evidence/'study-export.json').write_text(json.dumps(studies.export(study['id'],catalog),ensure_ascii=False,indent=2)+'\n')
    (evidence/'topic-atlas-export.json').write_text(json.dumps(atlas.export(catalog,studies,study['id']),ensure_ascii=False,indent=2)+'\n')
    LabMusings(notes).save({'title':'Who sets the direction of an exchange?','author':'Codex','edited_by':'Codex','kind':'question','status':'working',
        'tags':['opening topics','partner influence','measurement'],'study_id':study['id'],
        'body':'The opening speaker need not propose the first adopted topic. In the twelve-opening development cohort, the second speaker proposes it in nine cases; substantive disagreement can also take up a subject. A model may contribute a recurring agenda, respond to cues in the opening, or do both.\n\nNext design: repeated ordered local pairings followed by responses from different partners to exactly the same saved opening. Keep initial choice, identity negotiation, response stance and later topic change distinct. This is a research question informed by Codex readings, not an established causal effect.'}, {s['id'] for s in studies.all()})
    print(json.dumps({'collection_id':study['id'],'runs':len(ids),'new_reviews':len(planned),'findings':len(findings),'blocks':[{k:v for k,v in b.items() if k!='run_ids'} for b in result['blocks']]}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    args=p.parse_args();prepare(args.workspace,args.evidence)
