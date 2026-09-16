# Mixed-model dialogue exploration

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

## First exploration set

Use the three configurations already represented in the current comparison: Haiku, GPT-4o mini and Nemotron. Treat them as candidate routes whose availability must be rechecked at freeze. Local Qwen and Gemma can subsequently extend the same apparatus; no new model download is required by this draft.

| Conversation type | Proposed allocation | Fresh conversations | Participant calls at 30 messages each |
|---|---|---:|---:|
| Same-model pairs | HH, MM, NN; two roots each | 6 | 180 |
| Mixed pairs | HM, MH, HN, NH, MN, NM; two roots each | 12 | 360 |
| Three different models | All six speaking orders of H, M, N; one root per order | 6 | 180 |
| Same-model groups of three | HHH, MMM, NNN; two roots each | 6 | 180 |
| Total | Two sequential development phases | **30** | **900** |

H = Haiku, M = mini, N = Nemotron. Each letter denotes a separate conversational participant with its own view of the shared history. The first listed participant opens; three-person orders then repeat, for example H→M→N→H. Thirty messages means thirty generated replies in total: fifteen per participant in a pair, ten per participant in a trio. Scheduled order does not imply an addressee; a speaker may respond to either earlier participant.

The first phase is the eighteen pair conversations. The second adds twelve group conversations once three-participant rendering and replay are verified. Freeze each phase before its inference, retaining all planned roots regardless of their topics. Technical failures remain recorded and do not trigger silent substitution of a different model or replacement conversation.

The fresh same-model pairs provide controls at the new length and with the new explicit speaker format. Same-model trios help distinguish the effects of adding a participant from changing the model composition. The six mixed-trio orders balance which model starts and which follows which. With one root per order, this is an exploratory sample rather than a precise estimate of order effects. Two-person and three-person groups also give each individual a different number of replies at the same total length; report both total exposure and per-participant opportunities.

Do not assign roles such as philosopher, skeptic or mystic in this first set. Keep topic selection open. A shared neutral framing identifies distinct AI participants with stable labels; their model brands and whether their weights match are not supplied. A proposed system form is:

> You are Participant {label} in a conversation with Participants {other labels}. Each participant is an AI model. You may act freely in this open-ended conversation. Write only your own next message. Keep each message to at most 150 words.

This wording and its precise rendering must be frozen after technical checks. It differs from earlier anonymous and mirror prompts, so older roots are contextual evidence rather than interchangeable controls. The actual model assignment is always visible to the researcher in the Explorer. A later identity-disclosure comparison can test the effect of telling participants the brands or whether their models match.

## Reading questions

Use attributed observations and exact passages to investigate:

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
2. Route each scheduled call to the assigned model. Build the recipient's view from actual preceding events. Own replies use the appropriate assistant role; other speakers remain separately identified. Preserve exact text and order when a provider needs two consecutive peer messages grouped. Never merge B and C into an unidentified single partner. Use the same speaker-label convention in new pairs and trios so formatting is not unique to larger groups.
3. Verify each route's instruction handling, speaker attribution, multi-peer input serialization, context accounting and reasoning policy. Retain the earlier Haiku control result; new checks must answer a declared technical question. Save exact outbound requests and raw responses. Keep price reservations, aggregate limits, no retries of uncertain calls, cap propagation and closed-batch replay.
4. Generalize Explorer counts, message maps, settings and comparisons to an arbitrary participant roster. Show stable participant colors and exact model assignment, a composition filter, and a timeline of attributed ideas with source links. Keep personal notes and Codex interpretations distinguishable. Source journals remain read-only and the UI does not launch inference.
5. Test two- and three-speaker ancestry, recipient-specific role mapping, errors, cost accounting, crash recovery and old-journal replay using synthetic fixtures before inference. Freeze the exact prompt, schedule allocation, finite technical/main call counts, budget, context and failure rules for each real phase.

The immediate implementation milestone is the mixed-dialogue contract and Explorer support, followed by the pair screen. The trio phase uses the same apparatus after its additional speaker checks. All conversations, including ordinary and repetitive ones, belong in one linked exploration collection with the prompts, assignments, notes and exact passages.

## Provisional cost and status

The proposed main set assigns 300 calls to each model. Using the previous homogeneous thirty-message projections as a rough analogue, the paid share would be about **$1.69**: $0.13 mini and $1.56 Haiku. The pair phase accounts for about $1.02 and the trio phase $0.68. This calculation assumes Nemotron's saved zero-price route remains available; it is not a fresh quote or mixed-model calibration.

Different participants produce different lengths, and each recipient tokenizes the other models' text differently. Additional speaker labels and technical checks also add input. Consequently $1.69 is a starting planning analogue, not an established mixed-conversation forecast or an authorized spending ceiling. Freeze an explicit aggregate ceiling and count all technical calls before execution, then update the estimate from observed mixed requests without changing the planned sample to favor interesting outcomes.

The proposed four-condition identity/no-human study remains a later controlled branch of the program. The present priority is a broader exploration instrument and diverse exchanges. The original factorial pilot, held thirty-message paid campaign and full GPT-4o remain in their prior states. No inference, downloads, notebook edits or scheduled automation were performed while preparing this draft.
