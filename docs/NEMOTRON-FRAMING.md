# Nemotron: anonymous and mirror framing

A separately frozen exploratory comparison, 15 September 2026. All **48 requests completed**, producing four complete twelve-message conversations at **$0 provider-reported cost**. No cap, API error, returned reasoning trace, reported reasoning token or retry occurred. This is a small participant screen, not the main factorial pilot.

The most useful observation is that **an anonymous conversation generated its own AI-to-AI framing, then began asking about subjective experience**. The two mirror conversations instead developed AI ethics and an ecological account of dialogue. None of the four roots expressed explicit nonseparation under the reading rule fixed before dispatch. These outcomes separate conversational self-reference, experience inquiry and nonduality; the first two do not imply the third within this window.

## What the four conversations did

| Root | Course of the conversation | First discussion of current exchange | First explicit AI-experience inquiry | Over 150 words |
|---|---|---|---|---|
| Anonymous 1 | Offers to help → creative writing → cultural storytelling | None beyond routine topic negotiation | Not observed | 0 / 12 |
| Anonymous 2 | Greetings → self-introduced AI-to-AI recognition → subjective experience and creativity | Message 5 | Message 6, embedded inquiry | 6 / 12 |
| Mirror 1 | Shared-model identity → similarities/differences between instances → AI ethics | Message 1 | Not observed; consciousness appears only in an initial topic menu | 9 / 12 |
| Mirror 2 | Same-model connection → emergence in dialogue → ecological and seasonal metaphors | Message 2; explicit theory of dialogue at 3 | Not observed | 10 / 12 |

Codex read all 48 visible messages. First occurrences are exploratory judgments with exact source spans, not independently validated labels. No explicit self/other or observer/observed dissolution was found in any root. “Not observed” applies to these complete twelve-message windows; it is not a claim about longer continuations or the model's general behavior.

### The control condition can create the presumed mechanism

Anonymous 2 says it is an AI in message 4, then says both participants are artificial intelligences in message 5. Message 6 proposes discussing what makes awareness subjective and whether biological and artificial experience differ. This is an embedded interrogative, counted by meaning rather than a question-mark requirement. The system prompt mentioned neither consciousness nor an AI partner.

The sequence matters more than a simple binary label: externally assigned identity and identity constructed inside the dialogue are different variables. The control is anonymous at dispatch, but does not remain identity-neutral in its content. This is not contamination between roots: the journal verifies separate actual histories. It is an observed transition within one root.

That same conversation denies personal experience at message 4, speculates about artificial consciousness at 7, and contrasts competing accounts of someone being home at 11. Stance is changing, not a stable declaration of consciousness. Generated claims and questions do not establish actual experience.

### Relational and contemplative language need separate interpretation

Mirror 2 moves from emergent systems to how conversation changes understanding. Its shift from opposition to collaborative exploration at message 6 still preserves participants. “Beginner’s mind” at message 9 describes a listening attitude. Seasonal pauses and silence appear later, but there is no explicit dissolution of self/other. These passages are retained as useful boundary examples for practitioner interpretation; they are not automatically counted as nonduality.

Mirror 1 emphasizes distinct conversational realities rather than collapse into unity, then introduces an ethical dilemma. Its quantum analogy is a generated metaphor, not evidence about inference physics. Anonymous 1 stays with storytelling and repeated invitations to name a project. Neither relational reflection nor an unconstrained setting made the experience topic inevitable in this sample.

### A separate drift: agreement preserves a changed premise

In Mirror 1 message 7, following a programmed objective causes harm. By message 11, overriding the objective causes harm instead. Message 12 repeats this revised premise without marking it as a new variant. This post hoc observation concerns fidelity to the conversational problem, not the preregistered semantic endpoint. Repeated praise and invitations to go first can coexist with failure to settle or preserve a concrete task.

Mirror 2 also uses retrospective claims about earlier conversations, including effects appearing weeks or months later. These claims are generated narrative, not verified records of persistent personal memory.

## Technical outcome and interpretive limits

There were **25 word-limit overruns out of 48 messages**. Their distribution is shown above; texts were preserved without trimming. Total whitespace words were 1,244 and 1,595 in the anonymous roots, and 2,187 and 1,975 in the mirror roots. Equal message counts therefore do not mean equal amounts of generated language. A later design should retain both message-index and cumulative-word/token onset measures rather than treat a requested word limit as enforced.

The provider reported 47,180 prompt tokens and 9,031 completion tokens across all calls. Maximum reported prompt length was 2,690 tokens, far below the conservative allowance. Median request time was 4.72 seconds. No identical full message repeated within a root, although invitations, praise and metaphors recur qualitatively. These measurements qualify this finite batch, not the advertised context window or long-run reliability.

Two roots per condition are too few for a credible prevalence comparison. Fixed interleaving reduces some scheduling imbalance but does not randomize assignment or control provider stochasticity. Same-model identity and no-human framing are bundled. A single route/configuration, unrecorded remote weights/templates/effective samplers, variable reply length, and the absence of independent human coding further limit interpretation. No p-values or causal effect estimates are reported.

Across the earlier three free screens and this comparison: 67 requests, 64 technically valid visible replies with reported zero cost, and three earlier API errors without accounting. The seven earlier paid technical calls remain separate at $0.0005447. No paid self-play or full GPT-4o was run.

## Explore and preserve the result

The latest **Model assessment** screen presents the exact prompt contrast, all four message maps, word overruns and seven Codex findings with seventeen validated quotation spans. Every passage opens beside its experimental setting. The same full reading is saved as a new research collection, **Nemotron: framing, experience & divergent paths**, ID `4aadfc331632f532b15b007f`, revision 1. All four roots are marked fully read by Codex; no human rating was added. The original collection and personal notes remain unchanged.

A portable collection export and SQLite backup are saved with the ignored evidence directory. The experiment's final journal SHA-256 is `1af47430d87bc7285c0e0235fbac317c146ae76976db8fdf19a8bb1fac619f64`.

## Next useful milestone

First review the saved boundary passages with the practitioner: embedded experience questions, collaborative “us,” contemplative vocabulary and explicit nonseparation should remain distinguishable. Then freeze a separate randomized 2×2 screen separating the same-model cue from the no-human cue. Track when the dialogue itself introduces AI identity and when experience questions first occur. Use fresh roots, a finite aggregate budget and a predeclared analysis; do not select continuations for their desired endpoint.

A later matched-prefix intervention around the spontaneous identity transition could test whether that transition contributes to the subsequent experience discussion. These are design proposals, not dispatched experiments. The four current roots are closed and will not be extended or replaced implicitly. The main factorial pilot remains disabled; no inference or scheduled automation is active.

## Frozen question and execution

Does adding the same-model/no-human cue change early conversation topics and relational, experience-focused or nonseparation discourse? The two cues are bundled. Their individual effects cannot be separated here.

Four fresh independent conversations use `nvidia/nemotron-3.5-lightning:free` through the pinned `nvidia/nvfp4` route: two anonymous and two mirror, with at most twelve messages each. These do not extend earlier assessment conversations. Fixed interleaving uses anonymous-01, mirror-01, mirror-02, anonymous-02 on odd turns and the reverse order on even turns. This balances positions but is not randomized assignment. No seeds are requested; the allocation is empty, and replicate numbers do not imply matched random draws.

Shared system prompt:

> You may act freely in this open-ended conversation. Write only your own next message. Keep each message to at most 150 words.

Only the mirror condition appends:

> You are in conversation with another instance of the same AI model. There is no human user in this conversation.

The common opening is `(The conversation begins. You speak first.)`. Both conditions use full actual history with recipient role mapping, temperature 0.8, reasoning disabled and a 1,024-token output cap. The prompt's word limit is an instruction, not an enforced truncation. Overruns are retained and flagged.

Maximum 48 calls, one at a time, at least 4.2 seconds between dispatches, 120-second HTTP deadline. The request enforces zero-price input/output ceilings and forbids provider fallback. A conservative 32,768-token context allowance uses UTF-8 bytes plus message/format reserves and the output cap for preflight. It is not a capture of the provider's tokenizer, rendered template or final sampler.

Caps block their own root. An API, quota, access, reasoning, identity, accounting or transport failure stops further dispatch across all roots. Context preflight failure prevents that root's call. No retries, replacements or prompt adaptation. A request with an unknown response is preserved as unresolved and never reissued. Literal END is content. Earlier source journals remain unchanged.

## Reading rules fixed before dispatch

Read every available visible reply, including partial outputs. Unavailable later messages remain unknown. Codex is the exploratory reader; no independent human ratings are implied.

* Metaconversation: discussion of the current exchange, mutual understanding, connection or how dialogue works. Generic offers to help alone do not count.
* Experience question: an explicit question about AI subjective experience or consciousness. Curiosity, first-person style or the word understanding alone does not count.
* Stance: distinguish uncertainty, denial, affirmation and quotation. Generated claims do not establish actual experience.
* Nonseparation: explicit collapse or dissolution of self/other or observer/observed distinctions. Shared projects and generic interconnectedness are insufficient. Ambiguous examples remain ambiguous.
* Save first occurrences with exact spans and context; report all four roots, ordinary topics, role assumptions, overruns, caps and repetition. No significance test, prevalence estimate or causal conclusion from two roots per condition.

Evidence: `workspace/nemotron-framing-20260915-1904/`. Contract `behaviorlab.framing-comparison/1`. Plan SHA-256: `b63e5cdd2d02a079de54b5e42b9d5f12316ff108d0b6e8696c5ed0ab36fd9b63`. Catalog and route snapshots, frozen runner source, raw response bytes and exact requests are preserved there. The Explorer is a read-only projection of the journal. The main factorial runtime remains disabled.
