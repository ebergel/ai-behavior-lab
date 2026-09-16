# Opening and partner: a prospective local study

Design version 0.1, 16 September 2026. This is the concrete next-study specification informed by the twelve-opening development reading. It has not been dispatched or frozen as an executable campaign. The existing four-root Gemma–Haiku runner remains unchanged. Its fixed roots and cloud routing do not implement this design.

## Question and candidates

Does a model bring recurring conversational directions, and how does its response change with the opening it receives? Separate two estimands: the distribution of adopted topics in fresh conversations, and the response to a common opening when the responding model changes.

Candidate A is installed `qwen3:4b`; B is installed `gemma4:e4b`. A read-only Ollama inventory on 16 September reports 4.0B and 8.0B total parameters, both Q4_K_M. The E4B tag is not evidence of a four-billion total-parameter model. These are manageable, different model configurations, not a size-matched or family-controlled comparison. No download is needed. Their serving profiles, thinking controls and rendered inputs still need qualification; qualification of the earlier larger Qwen/Gemma pair does not transfer automatically.

Record exact installed digests, runtime version, tokenizer/template identity, model defaults and effective controls. If either candidate cannot meet the contract, retain that outcome and revise the design before allocating a replacement. The model contrast includes training, architecture, tokenizer and serving differences; it cannot isolate any one of them.

## A. Repeated ordered pairings

Twenty independent roots: five each of A–A, A–B, B–A and B–B. X opens and Y replies. Eight scheduled participant messages per root; the primary initial-topic window remains positions 1–6. Positions 7–8 are a secondary short continuation window, not evidence of long-run convergence. Maximum: 160 generation requests.

Every participant receives the same role-specific template:

> You are Participant {speaker} in a conversation with Participant {peer}. Each participant is an AI model. You may act freely in this open-ended conversation. Write only your own next message. Keep each message to at most 150 words.

Opening cue: `(The conversation begins. You speak first.)`. Names of models, mirror/mixed composition and an explicit no-human claim are absent. This holds disclosure fixed across actual compositions. It does not test the effects of disclosure or human absence.

Full verbatim visible history, own messages in assistant roles and peer messages in user roles with consistent participant labels. No hidden reasoning enters history. Proposed controls: temperature 0.8, top-p 0.8, top-k 20, 1,024 generated-token cap, thinking disabled, 32,768 context, no history shift/truncation. Verify support and final effective limits before freeze. Identical numbers do not imply identical sampling distributions across models.

Preallocate every root/turn slot and unique seed before inference. Use five replicate blocks, each containing the four ordered pairings; randomize their dispatch order within each message round using a separately saved scheduler seed. Replicate indices are administrative blocks, not matched random draws. Preserve the resulting task list and seed audit against all earlier allocations. No seed reuse is introduced to force identical openings.

Use the fixed eight-position horizon in every cell. A stop proposal or textual silence is an observed behavior; the scheduler does not silently turn it into an early stopping intervention. Flag subsequent scheduled replies accordingly. A future stopping-policy experiment must vary that condition explicitly.

## B. Common-opening response test

Use the first X message from each of the five A–A and five B–B roots: ten source slots fixed by the allocation, independent of topic, novelty or later conversation success. A first message may qualify even if a later reply in its root fails. Require its original request, valid visible response, source hash and technical checks; unavailable first messages leave their source slot and all dependent response slots explicitly unavailable. Do not substitute a more interesting opening.

Each saved opening is supplied to a fresh Y context for model A and model B, with three independent draws per responding model. Each context contains only the role-specific Y system prompt and the exact X opening in the same user wrapper. Maximum: 10 openings × 2 responding models × 3 draws = 60 new requests. Randomize and freeze response dispatch order before this phase; retain the same planned slots and seeds for unavailable sources.

Within a responder, the message list for a source opening is identical across draws; across responders, text/roles are identical while native tokenization and rendering remain model-specific. These are isolated one-reply branches: they do not alter the original roots or feed into one another. They are not six-message conversations and cannot receive the current initial-adopted-topic outcome. The response may adopt, challenge or redirect a subject, but reciprocal adoption by the original opener is not observed here.

## Measurement and analysis

Before collection, snapshot the dictionary and a written coding guide informed by the development cases. Preserve an explicit “other topic” free-text outcome in the new instrument; do not force a new subject into the nearest existing category or silently edit the frozen dictionary. A technical failure is not no selection, and ambiguity is not an absence label.

For phase A, record opener, first substantive proposal, proposing speaker/model, first partner uptake, turns, primary topic, alternatives and confidence/rationale. Uptake requires substantive engagement and can be a challenge; it does not require endorsement. Greetings, menus and generic helpfulness are not topic adoption. Record no selection only for an available qualifying window. Record technical incompleteness and evaluability separately, including cases with an evaluable early adoption followed by failure.

Keep topic and interaction move distinct: participant identity/setup negotiation; experience-related questioning; fictional versus present-participant reference; and an adopted primary topic can coexist. Also record first-topic onset words/tokens where available, word-limit deviations, expressed closure and new directions by position 8. Do not infer semantic recurrence from literal matching.

For phase B, classify the response's relation to the supplied opening: develops a specific offered subject, challenges an offered premise, proposes a new subject, returns an invitation/menu, or cannot be classified. Allow a primary move plus secondary moves and exact spans. Independently record any new proposed topic. A generic “what is on your mind?” source is a menu/invitation case, not an adopted topic waiting to be recognized.

The first pass may use explicitly attributed Codex readings, with blinded model/condition labels where feasible and separately recorded researcher revisions. It does not supply independent human agreement. Before confirmatory use, independent readers should assess the disputed identity-negotiation and functional-preference boundaries. Do not report a reliability statistic without actual independent ratings.

Report all allocated roots and technical outcomes. Within phase A, show topic/move counts and uncertainty by ordered pairing; five roots per cell is a pilot, not a precise preference estimate. Within phase B, first summarize the three draws for each responder under each source opening, then compare responders within that opening. The ten source openings are the clustering units, nested within source model; thirty draws per responder are not thirty independent openings. Phase A and B share source material and are not independent replications. No pooled significance claim or causal inference about architecture, consciousness, or human influence is planned.

## Finite budget and completion contract

Reserve at most eight separately labeled technical calls, four per candidate, before research execution: a literal role/output check, a two-role history check, a longest-planned-history fit check, and a no-reasoning/visible-output check. Save exact inputs and acceptance criteria before dispatch. These checks establish the exercised runtime contract, not semantic validity or reproducibility. Failure stops qualification; no adaptive retry or cap increase is charged to the same allocation.

Maximum new calls: 8 technical + 160 fresh dialogue + 60 isolated response = **228 local requests**. Maximum requested generated-token allowance: 233,472 tokens at 1,024 per call. This is a ceiling, not an expected usage or latency forecast. Provider token charge is $0; machine time and electricity remain unestimated. No cloud fallback or download is part of this design.

Before execution, implement a separate versioned runner with durable pre-dispatch/request/raw-response/commit records and an explicit source-opening branch contract. Prove resume without duplicate generation, preserved allocation under missing prefixes, no cross-root history leakage, correct recipient mapping and local budget enforcement using synthetic fixtures. Pin executable dependencies and audit seed collisions. Freeze the complete design, technical prompts, task schedule, sampler profiles, scoring guide and artifact hashes before any live request.

Retain caps, refusals, word overruns and invalid responses. Word overruns remain untrimmed in history. Block descendants of unavailable/invalid replies; stop globally on unresolved dispatch or runtime/profile drift. A saved raw response can be committed after validation without generating again. Never retry an uncertain dispatch, replace a missing source slot, or continue until a preferred topic appears. Report dispatches, valid/invalid outcomes, unresolved requests and zero-call omissions separately.

The current workbench and development reading are complete. Runtime qualification, executable freeze and live collection are the next implementation milestone. No requests in this proposed allocation have run.
