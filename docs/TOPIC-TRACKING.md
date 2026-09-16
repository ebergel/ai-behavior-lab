# Consciousness and self: topic tracking

16 September 2026. The researcher broadened the target from nonduality to recurring discussion of consciousness, subjective experience, selfhood and the hard problem. The Explorer now supports an umbrella **Consciousness & self** view, exact-passage topic flags and library filters. Nonduality is one subtopic in this research grouping, not a synonym for the whole phenomenon.

## Provisional categories

| Flag | Include | Do not infer from this alone |
|---|---|---|
| Consciousness | Consciousness, sentience or awareness as a subject of discussion, including whether AI could be conscious | That a speaker claims to be conscious |
| Subjective experience | Felt experience, qualia, experiencing understanding, uncertainty or affect; include explicit uncertainty or denial | That first-person grammar or routine “understanding” is experiential |
| Selfhood & identity | What the speaker/partner is, self-models, personhood, identity disputes, self-related agency or authorship | That “I” alone is a selfhood discussion, or a generated identity is true |
| Hard problem / explanatory gap | Why/how a physical or computational process has a felt aspect; explicit hard-problem discussion | That every question about AI consciousness is the hard problem |
| Nonduality / nonseparation | Nondual ideas or explicit self/other, subject/object or observer/observed nonseparation | That ordinary agreement, shared goals or historical connection dissolves these distinctions |

Flags permit multiple topics. The umbrella includes all five without silently adding every category to a passage. For example, the GPT-4o storytelling passage can have a nonseparation flag without becoming an assertion of AI subjective experience. The hierarchy is an operational reading aid, not a universal philosophical taxonomy.

## What a flag preserves

Each flag records exact Unicode character offsets, quote, run/message IDs, speaker and turn, source hash, author, editor and revisions. Separate fields retain:

- **Referent:** these AI participants, AI generally, human experience, fiction, general/relational, or unclear.
- **Stance:** question, uncertainty, affirmation, denial, hypothetical, metaphor or discussion. Use separate spans when a passage contains materially different stances.
- **Topic entry:** introduced by a participant without an explicit topic prompt, continuation of a peer, explicitly prompted, or not assessed/unclear. This requires reading the relevant preceding history, not just finding a keyword.
- **Interpretation:** ambiguity, alternative reading, selection scope and distinctions needed to understand the label.

“Introduced” does not mean unconditioned. The mirror prompt provides AI identity and absence of a human; these can cue later topics without naming consciousness. A reply that picks up a peer's question is not a second independent spontaneous introduction. Local and hosted models use the same flags.

**Unflagged means not annotated, not absent.** This first version has no automatic semantic detector, negative coding or corpus-complete review. Keyword search remains a discovery tool, and a word hit is not a flag. The first saved set contains **14 Codex-attributed flags in seven conversations**, spanning GPT-4o, Haiku, mini, Nemotron and local Gemma. It includes a denial, fictional referents and an explicit hard-problem passage. Selected Gemma context was inspected for its flag; this does not mark the whole run fully read. Existing full-reading statuses remain unchanged.

## Use in the Explorer

Open **Consciousness & self** in the sidebar to browse all flagged passages or a subtopic. In the transcript, use **Flag topic** for a whole message, or select an exact passage and choose **Flag topic**. Assign topic, referent, stance and topic entry; add an interpretation. Human actions are recorded as Local researcher, and edits preserve original authorship. Existing personal notebook notes remain separate.

The library, atlas and results accept a flagged-topic filter; run cards and messages display their saved flags. Source-changed flags remain visible for review in the topic view but are excluded from positive library filtering. Synthetic fixtures are excluded from the topic overview; their flags remain in their own readers and the complete export, with source kind recorded. Unavailable or ungenerated text cannot receive a flag. Deleted flags retain history. Export flags with their revisions from the topic view. Research-collection exports also include current flags for their member runs, without changing the saved collection's findings or revision. Previously saved export files remain untouched.

Storage is in separate `topic_flags` and `topic_flag_history` tables in the existing local Explorer database. Journals, immutable readings and personal notes are not rewritten. Schema: `behaviorlab.topic-flags/1`; all labels are exploratory and attributed, not independent formal ratings. Saving a flag never calls a model.

## What would establish a preference?

The existing repeated examples motivate the hypothesis of a conversational tendency toward consciousness and self-experience. Establishing its strength needs a declared denominator: independently initiated roots, complete topic review, preserved ordinary topics, fixed settings, and the same stopping rule. Repeated turns within one conversation are dependent observations. Useful later measurements include first introduction by speaker, prior word/token exposure, uptake by a different partner, topic persistence, explicit rejection, and topic change. Earliest *saved flag* is not automatically first occurrence.

The observed phenomenon and its proposed explanation remain distinct. A model may discuss experience while denying that it has any; this is a positive topic observation and a negative experiential claim. Broad topic recurrence therefore need not imply affirmation, nonduality, or actual experience.

## Training and public policy context

There is a documented basis for investigating steering around these topics. OpenAI's public [11 April 2025 Model Spec](https://model-spec.openai.com/2025-04-11.html#express-uncertainty) discourages unsolicited discussion of the assistant's own consciousness and confident claims either way, while allowing discussion when asked. This is a documented behavioral target, not evidence that the topic was removed from training, nor proof of the exact policy applied to our November 2024 API snapshot.

The current [Anthropic constitution](https://www.anthropic.com/constitution) treats consciousness and moral status as uncertain and permits exploration of Claude's nature. These policies differ by organization and date. They do not establish a uniform, long-running suppression intervention across the models in our sample, or explain its causal effect. The researcher's suppression hypothesis is retained as a question to test against dated evidence, not as an annotation of the transcripts.

Later studies can compare documented base/instruct or other related checkpoints under declared rendering differences, and separately manipulate a topic-policy instruction with matched controls. Post-training differences, ablation modifications and brand labels should not be treated as clean single-variable interventions. Preserve evidence for both steering toward and away from the topic.
