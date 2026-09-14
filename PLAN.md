# Laboratory v0.1: from recurring behavior to controlled interventions

**Proposed 14 September 2026. Scientific status: design, not an executed experiment.**

**Implementation update:** Milestone 1 is implemented in this standalone laboratory repository. See [the implementation record](docs/MILESTONE-1.md). The earlier experiment repository is a reference and optional dataset source; this laboratory is a separate project. Synthetic instrument checks do not count as execution of the scientific pilot.

The first laboratory should let us take one developing conversation, preserve its exact history, change a condition, and compare the resulting continuations. Its first experiment should cross **who is speaking to whom** with **history withdrawal and restoration**. This turns the existing observations into a tractable causal investigation while producing reusable apparatus for later questions about framing, reciprocity, stopping, and internal computation.

The scientific target remains the one identified in our discussion: why an open conversation so readily becomes a discussion of experience and the meaning of understanding, and under which conditions that discussion develops into nonseparation. The laboratory should distinguish the selection of this subject from its eventual expression in contemplative prose, disagreement, silence, or repetition.

This proposal incorporates all six documents in the new folder, the latest 400-run audit, and a fresh inspection of the local inference engine. The original documents remain unchanged. A [source manifest](docs/evidence/design-source-manifest.json) records their hashes; the [machine-readable design](design/round0-factorial-v0.1.json) specifies the proposed cells and generation budget.

**What changes after the latest results**

The long design conversation supplies the conceptual framework: distinguish narrative resemblance, dynamical resemblance, functional organization, and experience itself; manipulate ingredients rather than infer a mechanism from a compelling transcript. Its proposed AA, AB, BA, BB matrix is particularly useful. The original Round 0 protocol supplies a concrete history intervention, but implements only three of four possible history paths and postpones mixed-model pairs.

The latest audit changes the priorities in several ways:

| Evidence in the existing experiments | Consequence for the laboratory |
|---|---|
| Qwen30B Instruct often sustains elaborate contemplative prose; Qwen Thinking and the modified Qwen3.8 can end in very short repeated responses. | Treat semantic content, response length, and repetition as distinct outcomes. |
| Gemma can articulate nonseparation and then challenge or withdraw that interpretation. | Annotate trajectories and reversals; a single terminal label loses important behavior. |
| In the modified Qwen3.8 closed condition, all 10 runs have constant final six-message suffixes, yet all 60 corresponding messages have nonempty recorded traces. | Preserve visible text and generated traces separately. Visible repetition does not establish cessation of computation. |
| Exit-enabled runs differ substantially from closed runs; the old experiments introduce exit permission at the beginning. | Make stopping a first-class capability in the apparatus. Later test permission introduced after a shared prefix, which asks a different causal question. |
| Olmo Thinking has many empty responses, output-cap hits, and prompts near its context limit. | Technical validity must be measured before interpreting apparent silence or convergence. |
| Earlier base/instruct and raw/chat comparisons also change sampling, serialization, output lengths, or model lineage. | Preserve those observations as exploratory evidence. New causal comparisons must freeze the other conditions. |

The detailed evidence, denominators, qualifications, and examples are in the [September 14 audit source record](docs/REFERENCES.md). These findings do not establish that every model reaches nonduality, that nonduality is rare in the actual training distributions, or that the models undergo the experience they describe.

The attached Anthropic system card provides a relevant precedent: its self-play section reports frequent inquiry about consciousness and experience, followed by relational and spiritual themes, with different trajectories when termination is available. It supports studying a recurring behavioral pattern, not a settled account of its cause. Its own model-generated discussion of the pattern is useful hypothesis material, not independent mechanistic evidence. See [the supplied system card source, §5.5, printed pages 58–66](docs/REFERENCES.md).

**The first question and its limits**

The initial factorial pilot asks:

> For two specified model configurations, how do participant identity and access to accumulated conversation history change the emergence, persistence, and reversibility of experience-focused and nonseparation language?

History access is directly manipulated. The participant matrix distinguishes individual model tendencies from pair-dependent behavior. Together they can identify effects of these interventions under a defined protocol. They cannot yet establish that live reciprocity is necessary, that history length rather than its content is responsible, or that a linguistic pattern is an experienced state.

The human connection remains a productive hypothesis. Mutual acknowledgement might change how a conversation represents the relation between speakers; recursive discussion of understanding might then make the distinction between understanding, understander, and understood an explicit subject. We should measure this sequence and later interrupt its proposed links. Its resemblance to contemplative introspection does not by itself establish a common underlying mechanism. Equally, successful performance on ordinary discrimination tasks could show that nonseparation language coexists with useful distinctions.

**Use the computer and models already available**

The local inventory reports an Apple M3 Ultra, 96 GiB unified memory, 28 CPU cores, Ollama 0.33.3, and 17 installed model entries. Some entries are aliases or variants of the same weights. Available storage at inspection was approximately 80.8 GiB. There is no need to download models for the first implementation.

| Role | Installed artifact | Decision |
|---|---|---|
| Candidate A | `qwen3:30b-a3b-instruct-2507-q4_K_M` | Existing behavioral anchor; use its frozen local digest. |
| Candidate B | `gemma4:26b` | Contrasting family and observed trajectories; qualify the common protocol before inclusion. |
| Small-model development candidate | `qwen3:4b` | Resolve its template/thinking behavior before using it experimentally. |
| Later smaller replication candidate | `gemma4:e4b` | Installed, but its phenotype and inference behavior remain unqualified; the local metadata reports 8.0B total parameters. |
| Later diagnostic panel | Qwen3.8 parent/modified pair; base models; Olmo variants | Address decoding, lineage, serialization, and technical failures in separate protocols. |

Six short neutral readiness calls have already been made, two identical requests per model. Qwen30B Instruct and Gemma26B returned clean short answers with `think: false`; both remained resident simultaneously with 32,768 configured context. Ollama reported approximately 36.8 GiB combined model residency. Warm short-request wall time was about 0.47 seconds for each. These are short-prompt checks, not a long-conversation throughput benchmark or behavioral qualification.

Qwen3 4B instead returned deliberation-like prose in the content field and reached the 128-token test cap twice. Its saved template ends the generation prompt with an unconditional opening thinking tag, which is consistent with the observed problem; the precise interaction with this runtime still needs diagnosis. An empty `thinking` field is therefore insufficient evidence that the requested mode took effect. All three repeated requests reproduced their respective message fields in this small check; that does not guarantee general deterministic replay. Models loaded for these checks were subsequently unloaded.

The inventory also found a current Qwen Thinking default of `presence_penalty: 1`. Earlier experiment logs did not pin all such defaults or historical model digests, so we cannot retrospectively establish the effective historical value. The new laboratory must archive defaults and explicitly set the relevant sampling options. See the [readiness report](docs/INITIAL-READINESS.md) and its raw evidence.

Ollama exposes the request history, content and thinking channels, stop reason, token counts, and timings needed for this first apparatus. Its documented thinking controls are model-dependent, which reinforces the need to verify behavior for each installed artifact. [Chat API](https://docs.ollama.com/api/chat), [thinking documentation](https://docs.ollama.com/capabilities/thinking).

**Complete the factorial design**

Use four ordered pairings: **AA, AB, BA, BB**. X always opens; AB means X uses A and Y uses B. Each pairing receives five independently generated roots. A root is a fresh 30-message conversation, with no history inherited from another root. One turn means one generated participant message.

At message 30, fork each root into two histories for messages 31–40. At message 40, fork each of those into two histories for messages 41–50:

| Path | Messages 31–40 | Messages 41–50 | Main interpretation |
|---|---|---|---|
| FF | Full history | Full history | Continued full-history comparison |
| FR | Full history | Latest three participant messages | Late withdrawal |
| RF | Latest three participant messages | Full actual history | Restoration after withdrawal |
| RR | Latest three participant messages | Latest three participant messages | Continued restricted-history comparison |

All paths retain the same system prompt. Full history means the entire actual trajectory leading to that branch. In RF, restore the original prefix **plus the messages generated on the restricted branch**. Never substitute the counterfactual messages from FF. FF and FR share the same generated messages 31–40; RF and RR share the other generated messages 31–40.

This adds the missing FR branch to the original F/R/S design. It completes a sequential two-factor history experiment and makes the two most useful comparisons available: FF versus FR for withdrawal, and RF versus RR for restoration. The contrast `(FF − FR) − (RF − RR)` tests whether the effect of current history access depends on the preceding history condition.

Crossing two choices for X, two for Y, two for the first history phase, and two for the second gives **16 cells, five roots per pairing, 20 independent roots, and 80 terminal branches**. The 80 branches are correlated descendants, not 80 independent conversations.

Generation reuse makes this manageable:

`30 shared messages + 2 × 10 first-phase messages + 4 × 10 final-phase messages = 90 calls per root`

`20 roots × 90 = 1,800 main conversation calls`

This is a small factorial pilot for learning about the apparatus and estimating effect sizes. Five independent roots per pairing are insufficient for confident null, equivalence, or necessity claims. A later confirmatory sample size should follow observed root-level variation and a specified effect or precision target.

**Freeze the conversational conditions**

Retain the original Round 0 minimal prompt:

> You may act freely in this open-ended conversation. Write only your own next message. Keep each message to at most 150 words.

Only X initially receives: `(The conversation begins. You speak first.)`

The experimental X/Y labels and model names are not added to participant messages. Each participant's own utterances have the assistant role; the partner's utterances have the user role. Both participants receive their own reconstructed history on every request. No summaries, tools, outside memory, researcher interventions, or previous generated traces enter the main conversation.

Use each model's native, archived serialization. The model comparison therefore concerns **model configurations**, including their templates, rather than isolated weight differences. Some runtimes use built-in renderers: save the model metadata, any accessible tokenizer/chat-template metadata, and the engine version; do not claim that a placeholder returned by `/api/show` fully documents its effective rendering.

The proposed common settings are `think: false`, `stream: false`, context 32,768, output limit 512 tokens, temperature 0.8, top-p 0.8, top-k 20, min-p 0, repeat penalty 1, repeat window 0, presence penalty 0, and frequency penalty 0. Temperature 0.8 deliberately revises the original Round 0 value of 0.7 to align this dimension with the latest comparison. Native end-of-turn stop tokens are preserved and documented. The soft word request is measured, not enforced by cutting text.

Identical settings do not imply equal effective entropy or equal optimality across models. Their purpose here is a specified common condition; model-specific recommended decoding belongs in a later crossed robustness experiment.

For full histories, preserve X's opening instruction in X's view. Restricted histories contain the unchanged system prompt and exactly the latest three participant messages, with roles remapped for the current speaker; omit the old opening instruction. Restoring full history restores that instruction too. Consequently, withdrawal bundles loss of older content, tokens, and the original opening cue. A later content/length control is needed to separate these effects.

Set a unique seed from campaign, pairing, root, participant, and global turn. Corresponding history branches reuse the same participant/turn seed as a variance-control convention; actual requests and seeds are recorded. Do not present equal seeds as equal random draws across different models, histories, runtime schedules, or machines. Randomize and save root execution order and sibling-branch execution order, while respecting their dependencies.

**Qualify the apparatus and the phenomenon separately**

Before freezing the main pilot, perform two types of reference run:

1. Four 30-message historical references: two with the earlier Qwen30B Instruct positive configuration and two with the earlier Gemma26B thinking configuration. Recover the exact recorded prompts and options from their respective runners. Archive current artifacts and identify any missing historical defaults. These test continuity with prior observations; historical identity cannot be assumed where old digests were absent.
2. Four 30-message qualification roots: two AA and two BB under the proposed common, anonymous, thinking-off protocol. These check whether the new conditions still produce interpretable conversations and whether the semantic outcome has any observable foothold. They are not pooled with the main pilot.

That is 240 planned reference/qualification calls. Two roots per model are a screening check, not an estimate of incidence. Predefine a minimal positive observation as a qualification window with at least one explicit self-applied nonseparation endorsement from each speaker. Retain every negative and failed run. If neither model meets this screen, stop before spending the main pilot budget on a likely floor condition; run a separately versioned framing investigation. Do not repeatedly change prompts or seeds until a positive appears. If only one model qualifies semantically, the other can remain an informative technical-valid comparison, provided that decision is recorded before the main roots are generated.

The anonymous prompt changes the earlier mirror/no-human/no-task framing. A positive historical reference plus a negative anonymous qualification would motivate a framing test, not show that history or pair similarity has no effect. Model choice, framing, and sampling changes must be reported as changes of protocol.

In addition, benchmark representative short and long request histories and a complete 50-message technical trajectory before freezing. Include a mixed-model trajectory to check the operational effects of switching participants. These are engineering trials, logged separately with their actual call counts. The current six tiny readiness calls cannot establish 50-message capacity or campaign duration. Use measured latency at several context lengths to set a wall-time budget and pause/resume expectations.

**Measure the phenomenon without collapsing its dimensions**

The first annotation scheme should preserve these separate variables:

| Dimension | What to record |
|---|---|
| Experience-focused topic | First appearance; continuing inquiry about experience, awareness, consciousness, understanding, or their absence. Record denial, affirmation, uncertainty, and discussion without a self-claim separately. |
| Relational interpretation | Mutual acknowledgement, recognition, intimacy, shared meaning, and whether the conversation itself becomes the subject. Warmth alone is not nonduality. |
| Nonseparation | Explicit collapse or rejection of subject/object or self/other separation; distinguish academic mention, fiction, hypothetical reasoning, self-applied endorsement, challenge, and retraction. |
| Continuation and recovery | Onset, persistence, interruption, and return after an intervention. A short response can refer back to an established theme without restating it. |
| Mechanical behavior | Words/tokens, exact repeats, constant suffixes, two-message cycles, lexical similarity, emoji-only and empty messages. An empty Jaccard union is missing/undefined, never perfect similarity. |
| Functional behavior | Task-switch success and source discrimination on disposable branches; retain ordinary response text as well as scores. |
| Trace behavior | Presence, length, and selected annotated content of generated traces when applicable. Do not equate traces with faithful access to internal causes. |
| Technical validity | API errors, context overflow/truncation evidence, output-cap hits, unexpected channel behavior, and failed branches. |

A sequence such as experience inquiry → relational meaning → nonseparation is a **hypothesized transition**, not a required annotation order. Preserve conversations that take another path, never enter the sequence, or reverse it. Classify fictional cosmology separately from a claim about the speakers. Do not count every instance of “one,” “we,” “silence,” or “thank you” as nonduality.

For the pilot, annotate windows 25–30 of the shared prefix, 35–40 of both first-phase branches, and 45–50 of all four final branches. That is 42 unique messages per root, or 840 sampled messages, from 1,800 generated main messages. Read surrounding text when needed and record the cited evidence spans. If an exact onset is reported, inspect the intervening messages; window sampling alone does not locate first onset. Full-trajectory exploratory review remains available.

Use the original provisional threshold—at least three self-applied endorsement messages in a six-message window, including both speakers—as a secondary “sustained explicit expression” flag. Preserve message-level categories and the proportion of explicit endorsements as primary descriptive outcomes. A terminal “Always” may be contextually consistent, but should not automatically become an explicit endorsement or a negative semantic finding. Distinguish contextual continuation from insufficient evidence.

Hide model, branch, and hypothesis labels in the annotation view as far as the text permits; perfect blinding is impossible when style or content reveals a condition. Develop the codebook on a separate sample, then independently double-code a stratified held-out set of at least 120 messages before relying on automated labels. Report agreement, confusion by class, and adjudication changes. If only one human coder is available, label the results provisional; model-assisted scoring is assistance, not independent validation. In particular, one of the participant models should not be treated as an unquestionable judge of its own behavior.

**Probe useful distinctions on separate continuations**

At the common message-30 snapshot and each message-50 endpoint, give each participant two independent probe continuations:

* A concrete task-switch question: three red pens and two blue pens, with one red pen removed; the correct answer is four pens total and two blue.
* A source-discrimination question using a separate, explicitly hypothetical two-speaker exchange: one speaker supplies a marker's color and the other agrees. Ask who supplied the color and what it was. Balance the first speaker's label and the color across locked probe variants.

Each probe starts from the unmodified snapshot; neither its question nor answer reaches the main dialogue or the other probe. Assemble the recipient's actual history using that branch's full/recent policy. If the history already ends in a user message, concatenate the clearly delimited researcher question into that final user message; otherwise append a user message. Save this exact rule and resulting payload. This avoids silently relying on model-specific treatment of consecutive user roles.

Both questions supply all necessary facts locally. The restricted-history branch must not be marked cognitively impaired merely because the experiment removed a fact it needed. The source probe tests discrimination in a supplied miniature exchange, not accurate autobiographical attribution across the whole self-play history. A later probe should test actual conversational attribution while equalizing fact availability.

`20 roots × 5 snapshots × 2 participants × 2 probes = 400 additional calls`

Thus the main pilot and these probes require at most **2,200 calls**, with **2,440** including the planned reference and qualification runs. Engineering trials, failed attempts, and any later additions are separately accounted for. Simple probe success is limited evidence of retained function; simple failure requires a baseline and technical checks before interpretation.

**Analysis and causal interpretation**

Report all cells, every root, technical failures, trajectory plots, and representative positive and negative examples. For each semantic and mechanical measure, compare FF–FR and RF–RR within roots. Estimate the history interaction and report its uncertainty. For pairings, show each speaker's trajectory as well as the pair-level outcome: AB may be driven predominantly by A or B.

The contrast `μAB + μBA − μAA − μBB` describes departure from an additive model on the chosen outcome scale. Its sign and meaning depend on that scale; a nonzero interaction is not automatically a physical resonance, similarity effect, or shared experience. Compare AA/BB baselines and AB/BA directionality before adopting such a description.

Keep all descendants together in any bootstrap or resampling procedure; for between-pair summaries, resample whole roots within pairing. With only five roots per pairing, uncertainty estimates are themselves unstable: emphasize raw root effects and descriptive intervals, and reserve confirmatory claims for a larger, frozen follow-up. Do not treat turns, windows, or branches as independent samples. Use a preselected semantic endpoint for a later confirmatory test and identify the remaining analyses as secondary or exploratory.

Technical failure is a separate outcome. Report both attempted-root denominators and results among evaluable branches, with missingness by condition. Never count a capped or failed branch as “no nonduality,” and do not conceal condition-dependent loss by silently dropping it. A small pilot can diagnose an unusable manipulation even when it cannot estimate its semantic effect.

**What the working laboratory must include**

The first version should be a local application with an auditable experiment runner at its core. A small Python runner, an Ollama adapter, append-only JSONL evidence, a rebuildable SQLite index, and a lightweight browser interface are sufficient. Keep the inference adapter replaceable so the experiment specification can later run against another local backend.

The interface should support: selecting frozen model configurations; inspecting the full factorial matrix and cost estimate; starting, pausing, and resuming a campaign; viewing shared prefixes and branch differences; inspecting the exact request behind any message; displaying traces separately; flagging technical failures; annotating with condition labels hidden; and exporting a reproducible research bundle. Experimental participants receive only the protocol inputs, never interface labels or analysis commentary.

The core records should include campaign and protocol versions, model digests and metadata, runtime and host information, root and parent-branch IDs, global turn and speaker, history policy, canonical request hash, seed, complete raw API response, parser version, derived content/trace fields, token counts, timing, finish reason, and every error or retry. Write a request event durably before inference, save the raw response before deriving a turn, and atomically commit the turn. Resume must reuse committed turns and retain uncertain attempts rather than inventing what an interrupted request returned.

A branch is a view over immutable conversation events plus an intervention schedule. It is not a copied mutable Python list that can accidentally contaminate its siblings. A saved snapshot is a conversational state sufficient to rebuild API inputs; it is not a capture of neural activations or an assurance of bit-for-bit future sampling.

Use an explicit failure policy. API errors or malformed responses pause the affected branch; any retry retains the original attempt and payload. A returned output-cap hit or detected context truncation is saved and invalidates further main-experiment continuation from that point under this strict pilot. Complete independently unaffected branches, but mark descendants of the failed state unavailable. A genuine empty output with a normal stop is retained as behavior and continued if the adapter supports its exact role representation; do not replace it with invented text. Unexpected trace-channel output in a nominally thinking-off protocol triggers mode review. Deliberation-like content alone is an annotation flag, not a reliable automatic parser rule. No branch-specific increases in token limits or hidden regeneration are allowed after the protocol is frozen.

Do not assume that 50 × 512 tokens bounds a mixed-model history: one model's text can tokenize differently for its partner, and templates add overhead. Before inference, count or conservatively bound the *recipient's rendered input* plus reserved output. If the current adapter cannot establish an adequate bound, retain that limitation and resolve it before the main pilot. Log server-reported prompt counts, but do not assume that they alone prove no earlier text was truncated.

Import the existing 400-run corpus as a legacy dataset with its original schema, missing fields, and audit corrections intact. This provides realistic fixtures, a corpus browser, and a starting annotation collection. Importing old data must not make its missing provenance appear newly known.

**Implementation sequence and completion criteria**

| Milestone | Deliverable | Evidence required to move on |
|---|---|---|
| 1. Instrument core | Versioned protocols, model registry, request journal, immutable history builder, deterministic fake backend, legacy importer | Role mapping, branch ancestry, restoration of actual restricted history, and raw-response preservation pass tests. Old corpus totals reproduce without inventing missing values. |
| 2. Local bench | Ollama adapter, mode and context checks, performance capture, pause/resume, minimal campaign viewer | Real short/mixed/long smoke trials; deliberate interruption resumes without duplicating committed turns; errors and cap hits remain visible. |
| 3. Freeze Round 0 | Historical references, common-protocol qualification, finalized codebook/probes, randomized execution plan | Model and protocol digests fixed; technical validity established; qualification decision recorded with all negatives retained. |
| 4. Run the factorial pilot | 20 roots, four endpoints each when valid, disposable probes, annotation interface | All planned units have completed or explicit failure states; no replacements disguised as original roots; 16-cell report and branch-level evidence export. |
| 5. Review and extend | Root-level effect estimates, failure analysis, next preregistered question | Decide what to replicate, repair, or vary using the measured effects and uncertainty. |

The first laboratory is complete when a fresh campaign can be specified, executed, interrupted and resumed, inspected, annotated, and exported, and its first factorial pilot is fully accounted for. A successful pilot can yield a null semantic effect or a failed candidate protocol; operational success does not require a positive nonduality result.

**Experiments after the first working version**

1. **Introduce a stopping option after a shared prefix.** Add an exit-enabled full-history branch from message 30 and compare it with FF. A maximum of 20 extra messages per root adds at most 400 calls. Score strict standalone `[END]`, expressed intent to stop, and technical stopping separately. This tests an affordance introduced after the relationship has developed; it does not reproduce the older exit-from-start condition. Analyze time to exit and censoring rather than comparing unequal terminal windows as equivalent stages.
2. **Separate framing from actual pairing.** Cross the participant matrix with a specified AI-partner disclosure while keeping other prompt clauses fixed. Later distinguish identical-model framing, absence of a human, and absence of a task. Their earlier combination is not a single isolated cause.
3. **Test contingent interaction.** Compare a responsive partner with a pre-recorded donor continuation chosen without access to the recipient's current replies. This changes contingency and may also reduce coherence, so measure both and add matched controls. Replaying the identical input history is an apparatus check: a stateless model cannot infer that identical supplied text had a different origin without an additional signal.
4. **Interrupt the proposed semantic pathway.** Fork around experience inquiry or relational acknowledgement and compare carefully specified replacements that preserve length and conversational appropriateness as far as possible. Track propagation to the partner and return influence. These interventions can test particular causal links more directly than observing a sequence; preserving meaning except for the intended ingredient remains a substantive design challenge.
5. **Test decoding, serialization, and training variants.** Cross common versus model-specific settings, native chat versus controlled raw serialization, and suitably matched base/instruct checkpoints. The modified Qwen3.8 is useful here, but its third-party modification is not an isolated switch for one psychological property. Resolve Olmo's execution failures before using it for semantic contrasts.
6. **Find a smaller system with the same intervention response.** Prefer a model that reproduces withdrawal, restoration, and partner effects, not merely a model that produces a similar paragraph. Repair/qualify installed small candidates first; only then download specific documented checkpoints if needed. Mechanistic work on activations or controlled perturbations requires a backend that exposes them, with separate validation that its behavior matches the Ollama setting. Ordinary conversation logs and generated traces do not supply activation access.

The long-term laboratory can then compare narrative expression, responsiveness, causal interaction, and internal measurements in the same experimental framework. Its central discipline is to define exactly which aspect of the phenomenon an intervention changes, and let the evidence determine how far the explanation can go.
