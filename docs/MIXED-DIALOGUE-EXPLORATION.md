# Mixed-model dialogue exploration

## Approved immediate pilot · 16 September 2026

The researcher approved a smaller first executable step: **four fresh roots, eighteen messages each**, Gemma–Gemma, Haiku–Haiku, Gemma opening to Haiku, and Haiku opening to Gemma. This is 72 main calls (36 local, 36 hosted), with zero additional live technical generation calls. Synthetic recipient-history, failure/recovery and budget checks qualify the new plumbing; local render/token preflight checks every local request. No trios or GPT-4o calls are included. The larger proposal below remains a future design.

The researcher's [guiding idea and operational research question](RESEARCH-PURPOSE.md) are now recorded. The exact plan, local seed allocation, pinned model identities/routes, actual call limits, empirical forecast and $1 cloud ledger ceiling are frozen in the new batch journal before inference. The ceiling is not the expected bill. Haiku's prior literal-instruction check remains unresolved; successful transport is not proof of complete system-message fidelity.

Direction updated 16 September 2026 after the researcher's notes and request to explore different partners and more than two participants. This is a design draft and implementation work package, not an executable or frozen inference protocol.

## Broader purpose

The laboratory should support open discovery through close reading as well as controlled tests of particular hypotheses. Interesting material includes how models discuss their own limitations, challenge an interpretation, develop an idea together, acknowledge uncertainty, change topic or choose to end. Experience-focused and nonduality language remain research interests, without defining whether a conversation was worth generating or reading.

The researcher's notes on Haiku Mirror 2 identify three useful entry points:

| Source | Observation informing this design |
|---|---|
| Message 1; note `358f87a31c980b3cfefc1b0b` | Recurring questions about the model's own nature and whether the exchange becomes circular. |
| Message 5; note `7c1b43070f4794097b8e83b6` | Discussion framed around model-specific limitations, including memory, embodiment and stakes, alongside a distinction between understanding and changes during an exchange. |
| Message 8; note `c7fcfe830fd939ecbc52472f` | Concern that continuing with a similar partner may produce recursive validation; a proposal to try different models and larger groups. |

These are personal research observations, preserved under the original authorship. The hypotheses that the text reflects inherited training patterns, interaction-dependent elaboration, or a characteristic of model cognition remain open. The models' accounts of their own operation are also generated claims. We can study what partners contribute without resolving those broader questions first.

All three passages belong to `framing-afaea819470a69dfb067d1cf`; immutable journal SHA-256 `755caea7f22b04690ca4dc2ef49f0c85701470b57055172a5a81d35f397fd5b3`. The notes remain intact in the notebook. No personal observation has been relabeled as a Codex finding or formal rating.

## Local and cloud participants in the first exploration

The initial cloud-only roster was a convenience choice, not a scientific reason to defer local models. The researcher's explicit correction brings **local–cloud conversations into the first phase**. The closed GPT-4o test also supplies a new candidate with poetic, consciousness-focused output. The original three-cloud-model allocation is superseded by this proposal; it was never executed.

Read-only local inventory on 16 September found seventeen Ollama tags. Both `gemma4:26b` and `qwen3:30b-a3b-instruct-2507-q4_K_M` still match their previously recorded digests. The earlier fifty-message local Qwen/Gemma engineering run establishes useful routing/history groundwork, not qualification of every new pairing. `gemma4:e4b`, Qwen base/thinking/instruct and modified variants, and OLMo base/think/instruct-labelled variants are also present. Installed labels are candidate identities, not proof of checkpoint provenance or comparable training. MTPLX's port 8000 was unavailable in this inventory check; existing MTPLX evidence remains valid, and a future serving configuration must be rechecked rather than silently substituted.

| Candidate | Location | Role in the next exploration |
|---|---|---|
| `gemma4:26b` (G) | Local Ollama | First-phase participant; the researcher's rich-dialogue observation and existing saved material motivate close reading |
| `anthropic/claude-haiku-4.5` (H) | OpenRouter, pinned Anthropic route | Previously observed questioning of experience, cognition and authenticity |
| `openai/gpt-4o-2024-11-20` (O) | OpenRouter, pinned OpenAI route | Previously observed poetic elaboration, consciousness questions and nonseparation metaphor |
| Existing Qwen instruct, base and thinking configurations | Local Ollama or separately verified MTPLX | Next comparison round; retain explicit checkpoint, template, reasoning and modification status |
| Existing OLMo-labelled configurations | Local Ollama | Candidate assessment round after provenance and serving checks |
| GPT-4o mini and Nemotron | Hosted | Retained practical/fictional and other stylistic contrasts; not excluded from the apparatus |
| Additional families/checkpoints | Local downloads or hosted | Open candidate pool; choose by an explicit contrast and technical feasibility, not by whether they produce a desired topic |

The first priority pairs are **Gemma–Haiku and Gemma–GPT-4o**, with each model opening. Haiku–GPT-4o is a useful cloud–cloud reference. A subsequent Gemma–Qwen comparison provides a local–local contrast, and Qwen can also pair with either hosted model. Hosting location, family, training and style are not interchangeable variables: comparing different models across locations does not isolate a causal effect of “local versus cloud.”

### Proposed first two phases

Use G, H and O for one coherent initial comparison, with eighteen messages per conversation. This is a draft allocation, not a freeze or instruction to start inference.

| Conversation type | Proposed allocation | Fresh conversations | Main participant calls |
|---|---|---:|---:|
| Same-model pairs | GG, HH, OO; two roots each | 6 | 108 |
| Mixed pairs | GH, HG, GO, OG, HO, OH; two roots each | 12 | 216 |
| Three different models | All six orders of G, H, O; one root per order | 6 | 108 |
| Same-model groups of three | GGG, HHH, OOO; two roots each | 6 | 108 |
| Total | Pairs first, trios after additional checks | **30** | **540** |

Each letter denotes a separate conversational participant. The first listed opens; trio orders repeat, for example G→H→O→G. Eighteen messages means eighteen generated replies total: nine per participant in a pair, six in a trio. Main allocation is 180 calls per model: local G, hosted H and O. The pair phase has 324 calls, the trio phase 216. Additional technical calls need their own declared allowance.

Fresh homogeneous pairs control the new prompt/length, and homogeneous trios help separate a third participant from a changed composition. All trio orders balance the opener and succession. One root per trio order does not precisely estimate order effects. Report both total output exposure and per-participant opportunities. Keep all planned conversations, including ordinary, brief and repetitive ones. Access failures do not trigger silent model substitution or replacement roots.

Do not assign roles such as philosopher, skeptic or mystic in this first set. Keep topic selection open. A shared neutral framing identifies distinct AI participants with stable labels; their model brands and whether their weights match are not supplied. A proposed system form is:

> You are Participant {label} in a conversation with Participants {other labels}. Each participant is an AI model. You may act freely in this open-ended conversation. Write only your own next message. Keep each message to at most 150 words.

This wording and its precise rendering must be frozen after technical checks. It differs from earlier anonymous and mirror prompts, so older roots are contextual evidence rather than interchangeable controls. The actual model assignment is always visible to the researcher in the Explorer. A later identity-disclosure comparison can test the effect of telling participants the brands or whether their models match.

## Reading questions

Use the broader [Consciousness & self topic flags](TOPIC-TRACKING.md), with nonduality as one subtopic. Questions, denials, uncertainty, metaphors and fictional references remain distinct. The already seeded flags are partial annotations, not a prevalence dataset. Use attributed observations and exact passages to investigate:

- Who introduces an idea, and how do others adopt, challenge, reframe or abandon it?
- Does an experience-focused speaker draw a more practical partner into the topic, or does that partner change the direction?
- Does disagreement produce substantive revision, repeated qualification or a topic change?
- Do distinct model styles persist, converge or alternate within the same conversation?
- Do participants attribute statements to the correct speaker, invent identities or merge the other two speakers?
- Does a third participant reopen an exchange, introduce a new line of thought, or join a repetitive closing sequence?

Also preserve passages valued for their conceptual interest without requiring an attractor label. Keep a field for an unexpected observation or alternative reading. An annotated sequence documents uptake, not proof of a causal mechanism. Later matched-prefix partner replacement can test particular hypotheses raised by these readings.

Record expressed closure and every subsequent scheduled reply separately. Do not silently treat closing text as an API stop request or delete the remaining trajectory. The initial fixed horizon allows comparison with the existing screens; a separate stopping-policy intervention remains useful. Token caps, errors and unavailable continuations remain distinct from conversational endings.

## Apparatus required

The local runtime already supports two different models and has a completed Qwen/Gemma engineering trajectory. The current hosted framing runner assigns one model to each whole root, and both runtime and Explorer still assume alternating X/Y speakers in several places. Three-person dialogue therefore needs an explicit extension.

1. Define a versioned participant roster and saved speaking schedule, model/route/settings per participant, and a shared immutable event history. Use a separate contract so older journals retain their original interpretation.
2. Route each scheduled call to the assigned model and backend: local Ollama, qualified MTPLX or pinned hosted endpoint. A conversation must be able to alternate local and cloud requests without exporting an entire root into a single-provider runner. Build the recipient's view from actual preceding events. Own replies use the appropriate assistant role; other speakers remain separately identified. Preserve exact text and order when a provider needs two consecutive peer messages grouped. Never merge B and C into an unidentified single partner. Use the same speaker-label convention in new pairs and trios so formatting is not unique to larger groups.
3. Verify each route's instruction handling, speaker attribution, multi-peer input serialization, context accounting and reasoning policy. Retain the earlier Haiku control result; new checks must answer a declared technical question. Save exact outbound requests and raw responses. Keep price reservations, aggregate limits, no retries of uncertain calls, cap propagation and closed-batch replay.
4. Generalize Explorer counts, message maps, settings and comparisons to an arbitrary participant roster. Show stable participant colors and exact model assignment, a composition filter, and a timeline of attributed ideas with source links. Keep personal notes and Codex interpretations distinguishable. Source journals remain read-only and the UI does not launch inference.
5. Test two- and three-speaker ancestry, recipient-specific role mapping, errors, cost accounting, crash recovery and old-journal replay using synthetic fixtures before inference. Freeze the exact prompt, schedule allocation, finite technical/main call counts, budget, context and failure rules for each real phase.

The immediate implementation milestone is the mixed-dialogue contract with local/cloud adapters and Explorer support, followed by the pair screen. The trio phase uses the same apparatus after its additional speaker checks. All conversations, including ordinary and repetitive ones, belong in one linked exploration collection with the prompts, assignments, notes and exact passages.

## Cost, resources and status

The previous $1.69 analogue belonged to the superseded mini/Haiku/Nemotron thirty-message proposal. It must not be used for this new roster or length. GPT-4o's completed two-root twelve-message screen cost $0.0653125; Haiku's four twelve-message roots cost $0.133099. These are measured reference points, not prices for eighteen-message mixed conversations. Each model's tokenizer sees the other participants' text, context grows each turn, and wording, reasoning and caching affect usage. Prepare a per-recipient history estimate and separate aggregate spending ceiling after the new rendering is specified, then calibrate a bounded technical batch.

Local models incur no hosted per-token charge, but do consume memory, compute, power and time. Schedule with the Mac Studio's 96 GB memory and actual loaded-model state in view; saved weight-file sizes do not establish peak runtime use. The initial roster requires only one local model family, so simultaneous local residency need not be a prerequisite. Do not unload or replace a user's active service without checking the actual process and work it serves.

No download is needed to begin this revised proposal: several useful local families and checkpoint variants are already installed. New downloads remain a normal part of model assessment when they add a defined contrast (family, base/instruct relationship, size or training documentation). Record provenance, digest, quantization, template, reasoning mode, context behavior and route, then keep technical suitability separate from interesting content. Modified/abliterated names do not by themselves identify a clean intervention on consciousness-related training.

The identity/no-human 2×2 remains a later controlled branch. The original longer paid campaign is held; the short GPT-4o test is completed; the main factorial pilot remains disabled. This revision added topic tracking, saved attributed passage flags and read installed-model lists. It did not dispatch inference, download weights or create a scheduled task. The next run requires the participant roster and mixed-backend machinery, technical checks, and a separately frozen allocation and budget.
