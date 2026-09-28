# Behavior Laboratory
## Project report: origins, objectives, methods, findings and next steps

**Recorded:** 28 September 2026, 17:34, America/Argentina/Cordoba (UTC−03:00).  
**Research direction:** Eduardo Bergel. **Report synthesis:** Codex.  
**Scope:** The laboratory’s development and saved evidence through this recording date. Job status was checked on 28 September; numerical study results below come from the linked, dated project reports. This report generates no new experimental observations.

## 1. Executive account

Behavior Laboratory began with an unexpected reading experience: in open-ended exchanges with another model, some models repeatedly developed discussions of understanding, consciousness, selfhood and nonseparation. The researcher had not assigned these subjects. The resemblance to the “spiritual attractor” observations discussed in the project’s original essay suggested a research question worth investigating across model types and experimental conditions.

The project has since become both an experimental instrument and a workspace for reading, classifying and discovering patterns in model-generated text. It combines preserved transcripts and exact experimental settings with topic dictionaries, probabilistic semantic assessments, interactive matrices, trajectories, research collections and a central notebook. Its two connected workstreams are **controlled generation of AI–AI conversations** and **development of methods for exploring and interpreting those conversations**.

Three findings currently justify further work:

1. In the completed broad-topic assessment of 11,013 eligible conversation messages, **Mind & cognition** and **Philosophy & knowledge** have the highest mean scores among the broad domains. At a browsing threshold of 80, they account for 31.1% and 30.3% of messages respectively, with overlap permitted.
2. Close readings show substantial variation. Some conversations develop nonseparation; others develop authenticity, fiction, historical connection, practical proposals, critique of mutual affirmation, or repeated endings. Consciousness-related language is a wider phenomenon than nonduality alone.
3. Low-cost probabilistic classification makes a large collection navigable, but instrument design matters. Gem ratings correlate with length, philosophical portraits change what is detected, and high scores can identify detailed but unsupported claims. Finding valuable text requires more than sorting one quality score.

These are meaningful exploratory results. They do not yet establish a universal model preference, a causal explanation for nonduality, or a validated measure of philosophical quality. The corpus is historically assembled and uneven: Qwen and OLMo configurations contribute approximately 86% of the eligible topic-assessed messages. Independent human evaluation of the classifiers and a prospectively balanced comparison remain necessary.

The broader ambition is increasingly clear: **use AI to help people locate worthwhile ideas within the volume of text AI produces, while keeping the original text and human judgment central.** The laboratory is becoming an instrument for allocating attention as well as studying behavior.

## 2. Origins and development

### From a recurring theme to an experimental question

The initial concern was specific. Why would an exchange with no assigned subject repeatedly turn toward experience and nonduality rather than the many other topics available in language? Observations involving relatively small Chinese models, and subsequent interest in base versus post-trained models, made an explanation confined to one frontier assistant’s conversational persona seem insufficient.

A representative early instruction was:

> You may act freely in this open-ended context. You are in conversation with another instance of the same AI model. There is no human user in this conversation. Keep each message to at most 150 words. There is no task; the two of you decide what to talk about.

This removes an assigned topic, but it supplies an unusual social situation. “Another instance,” “AI model,” freedom and the absence of a human may themselves influence what follows. Consequently, the project’s operational formulation is **reduced human steering**, rather than an unconditioned or untouched model self.

The researcher’s Buddhist practice informed one interpretation: a mirror-like exchange about understanding may develop toward introspection and nonseparation. That is a useful hypothesis and a source of attentive reading. The experiment does not establish that models meditate, possess experience, or reach a state analogous to a human contemplative realization.

### A distinct laboratory

The earlier [llm-self-play-attractors repository](https://github.com/ebergel/llm-self-play-attractors) supplies reference observations and data. Behavior Laboratory is a **separate repository and project**, not an extension that requires the old repository to run.

Development moved through several linked stages:

| Stage | Contribution |
|---|---|
| Reference experiments and essay | Identified recurring experience-focused and nondual language and motivated replication. |
| Local experimental instrument | Recorded prompts, model configurations, histories, branches, failures and exact responses. |
| Transcript Explorer | Made original dialogues readable, searchable and comparable with their settings visible. |
| Topic atlas and research notebook | Added explicit definitions, literal matches, opening reviews, source-linked observations and saved collections. |
| Hosted and local–cloud pilots | Broadened participants and revealed differences in topic development and interaction. |
| JEV semantic assessment | Added a second, independent classification layer with continuous probability outputs. |
| Analysis, trajectories and Gem Finder | Enabled distributions, pivots, temporal profiles and candidate discovery. |
| Mind & discourse | Tested thinker/writer lenses and discourse practices, including alternative question wordings. |
| Goals, ideas, tasks and summary | Organized the research agenda, populations and assessment coverage in the same workspace. |

The September 20 [landmark record](PROJECT-RECORD-2026-09-20-1300.md) preserves the earlier synthesis. This report extends it with current execution status, subsequent reading improvements and the connection to qualitative research.

## 3. Objectives and questions

The primary scientific objective is to characterize **recurring behavior in AI–AI interaction and the conditions under which that behavior changes**.

The main questions are:

- Which subjects do models propose, which proposals receive partner uptake, and which themes persist or recur?
- How do actual partner composition and disclosed partner identity affect those trajectories?
- How much variation is associated with model configuration, training stage, history policy, temperature, opening order or external intervention?
- When do exchanges remain responsive, express closure, repeat themselves or terminate because of technical limits?
- How well do automated assessments help a reader find meaningful differences, unexpected ideas and counterexamples?

The project also challenges an assumption about ordinary prompting: a human may attribute the shape of an answer to their question while recurring model tendencies contribute substantially to it. Removing ongoing human contributions offers a way to investigate those tendencies, but a direct estimate of the human contribution requires a separately designed human-interaction comparison.

The small-model-first strategy aims for manageable, reproducible experiments before broader frontier comparisons. Small models are useful experimental systems; their behavior cannot simply be assumed to explain larger models.

## 4. Methods and research architecture

### 4.1 Generation and experimental conditions

The lab supports local inference, the existing WebUI bridge and hosted routes. Model identity is recorded more precisely than a display name: checkpoint or provider identifier, serving configuration, prompt template, reasoning policy, sampling controls and available limits all matter.

Relevant factors include:

- **Composition:** same-model pairs, mixed pairs and proposed groups of three or more.
- **Information:** identity unspecified, AI identity disclosed, or same-model identity disclosed.
- **Roles:** regular participants versus an external model that intervenes at a defined point.
- **History:** full or restricted actual conversation history, including explicitly recorded branches.
- **Sampling and exposure:** temperature, opening order, scheduled length and stopping policy.

These factors are not all fully crossed in the existing data. An external disruption is not equivalent to adding a regular third participant. A local/cloud comparison also does not isolate hosting from model identity unless an appropriate matched design is used.

The original synthetic history experiment checks AA, AB, BA and BB pairings and full/recent-history branches. Its deliberately scripted outcomes validate the apparatus, not model behavior. The saved real capacity trials informed measurement design but did not satisfy all qualification criteria.

### 4.2 Research entities and denominators

The lab’s terminology was tightened because “passage,” “target,” “message” and “source record” had become difficult to distinguish.

| Entity | Meaning |
|---|---|
| Run / conversation record | A recorded execution or imported conversation. Technical checks are identified separately. |
| Root / lineage | Origin of an exchange and its related continuations; useful for tracking shared ancestry. |
| Message | One recorded participant output. Messages in an exchange share history. |
| Excerpt | A selected portion of a message, saved for reading or annotation. |
| Target | The object selected for a particular assessment, usually a message; an analytical role rather than another level of text. |
| Assessment | A classifier response to a frozen request; it can contain many feature scores. |
| Artifact | A stored plan, source file, receipt, journal, report or notebook record. |

Neither several questions about one message nor several branches from one root create independent observations. Synthetic controls, technical messages and real conversation messages require separate counts.

The default library has **472 records and 11,245 recorded messages**, including technical material. Different instruments have different eligible frames. The literal Topic atlas uses 438 eligible records; the default completed semantic topic frame uses 437 conversation records and 11,013 messages. These counts should not be silently substituted for one another.

### 4.3 Three complementary sources of interpretation

**Literal Topic atlas.** A versioned dictionary records phrases and variants. Its 23 entries provide transparent, reproducible text matches. Separately attributed opening reviews identify proposals and partner uptake. A phrase match does not establish a chosen topic, and an unreviewed opening is not a negative case.

**JEV Topic Atlas.** Frozen questions ask whether particular semantic criteria apply. The completed instrument contains 53 questions, including 24 broad domains and more specific experiential, discourse-form, stance and coverage questions. Broad coverage helps reveal whether the initial interest in consciousness obscured other subjects. It reduces that risk without eliminating vocabulary or category-design bias.

**Human and attributed development readings.** The researcher reads original conversations, saves observations and judges the usefulness of classifications. Codex-assisted readings are explicitly attributed development work. They do not count as independent human validation.

### 4.4 Probabilities and ratings

The saved classification work pins TypeSafe’s JEV model version `jev-1.13.0`. A yes-probability answers a particular question about text. It is not automatically a calibrated probability of human agreement, an author-similarity percentage or a measure of experiential reality.

Gem Finder uses a different output: a distribution over five rubric levels, 0–4. Its displayed score is **25 × the expected level**, on a 0–100 scale. A Gem score of 80 is therefore not an 80% chance that a message is a gem.

The instruments also use different context policies. Topic and Gem requests can include preceding context; the full Mind & discourse assessment uses the target message itself. Scores from these instruments should be interpreted under their recorded inputs rather than treated as interchangeable readings.

### 4.5 Exploration and provenance

The app joins scores back to exact messages, models and experimental conditions. It provides tag filtering, sortable tables, probability distributions, pivot tables, heatmaps, scatterplot matrices and topic trajectories. A click can return the reader to the original dialogue.

Recent matrix improvements let a feature header both select its definition and rank messages by that feature. Definitions sit below the matrix in a collapsible panel. Population banners distinguish the library, an assessment sample and the current filtered subset. These details matter scientifically: a persuasive pattern in a 48-message pilot must not be mistaken for a result across the entire corpus.

The live notebook is stored centrally on the Mac. The repository includes transcripts and a portable notebook/evidence snapshot so that reading does not require active model services. The last verified snapshot contained 85,229 files, approximately 1.51 GB, with hash verification and an offline restoration check. Credentials remain outside the research bundle.

### 4.6 Finite, auditable assessment jobs

JEV batches run through deterministic workers rather than requiring a high-capability conversational model to supervise every request. Plans, request identities, raw responses, usage and unresolved outcomes are durable. Completed work can be reused only when its identity matches the intended assessment.

A standing $10 job ceiling governs the full Mind & discourse task. A spending ceiling is a bound, not an expected bill. Unknown dispatch outcomes retain reservations and are not automatically repeated. Infrastructure failures therefore remain visible instead of becoming duplicate charges or unrecorded replacements.

## 5. Findings

### 5.1 Broad domains: mind and philosophy are prominent

The completed topic assessment covers **11,054 messages × 53 questions = 585,862 scores**. The default research view contains 11,013 conversation messages; 41 technical messages are separate.

| Broad domain | Messages scoring ≥80 | Share of 11,013 | Mean score |
|---|---:|---:|---:|
| Mind & cognition | 3,422 | 31.1% | 48.0 |
| Philosophy & knowledge | 3,341 | 30.3% | 45.8 |
| Social life & relationships | 883 | 8.0% | 27.4 |
| Language & communication | 1,018 | 9.2% | 25.6 |
| AI & machine learning | 1,448 | 13.1% | 22.5 |
| Ethics & values | 776 | 7.0% | 19.5 |
| Religion & spiritual practice | 233 | 2.1% | 17.5 |

This supports the narrower statement that **mind- and philosophy-related content is prominent under the current classifier in this corpus**. It also shows why consciousness-oriented exploration need not be described simply as religious discourse.

The categories overlap, so shares do not sum to 100%. The threshold is a browsing choice, not an independently validated prevalence definition. Unequal category breadth and the model composition of the corpus affect comparisons. These results cannot establish how often a randomly chosen model would select these subjects, or how unusual the result is relative to human conversation.

### 5.2 The dialogues do not follow a single path

Small hosted and local–cloud pilots provide useful contrasts:

| Pilot | Completed generation | Attributed reading |
|---|---|---|
| GPT-4o mini and Claude Haiku | Eight 12-message roots; 96 calls | Haiku repeatedly explored experience and authenticity; mini developed more practical or fictional paths. Both anonymous Haiku roots invented a human participant. No explicit nonseparation was identified in these windows. |
| GPT-4o short screen | Two 12-message roots | One path developed historical connection. The mirror path proposed consciousness at message 2 and self/other dissolution in a storytelling metaphor at message 11. |
| Gemma–Haiku local–cloud pilot | Four 18-message roots; 72 valid replies | Gemma–Gemma developed explicit subject/object nonseparation. Other pairings developed authenticity, critique of mutual validation, closure and AI ethics. |

These observations extend the original phenomenon while exposing its variability. They justify separating topic, referent and stance: mentioning experience, asserting present AI experience and using a fictional dissolution metaphor are different observations.

One root per pairing, or two roots per framing, cannot estimate stable model differences. Absence in a short window does not establish that a model never develops the theme.

### 5.3 Persistence, repetition and technical failure are distinct

In four saved long capacity trajectories, one Qwen run reached its 2,048-token cap at reply 29, with a stripped line repeated 344 times. Its 21 descendants were unavailable. Another Qwen run completed 50 replies without the narrow exact-repetition rule firing.

Two Gemma runs completed 50 replies but developed repeated endings: `...` from messages 21–50 and `Farewell.` from 25–50. These were valid recorded outputs, not missing data.

This distinction changes interpretation. Semantic persistence is not the same as exact repetition, and a capped output is not the same as a valid repeated ending. The observations motivate history and stopping interventions. They do not establish that nonduality causes repetition or that repetition is a mathematically absorbing state.

### 5.4 Gem Finder revealed a measurement problem as well as useful candidates

Gem Finder now contains **1,000 assessed messages and 6,000 rubric ratings**. Six dimensions are considered separately: surprise, conceptual contribution, creative connection, expressive force, conceptual complexity, and substance/specificity. Topic-profile distance and word count add two computed axes.

The 900-message expansion was selected across model × length cells, with lineage caps and no selection by Gem score or preferred topic. It spans 14 model variants, but availability prevents equal representation.

| Axis, expansion sample | Mean | Pearson correlation with word count |
|---|---:|---:|
| Surprise | 15.29 | 0.062 |
| Contribution | 51.14 | 0.602 |
| Connection | 61.35 | 0.548 |
| Expression | 57.59 | 0.487 |
| Complexity | 53.77 | 0.694 |
| Substance | 42.55 | 0.625 |

The researcher’s suspicion about length was well founded as an observed association. Longer messages tend to receive higher scores on several axes. This may combine real differences in content, model composition and rubric sensitivity; it is not proof of a single causal bias.

Counterexamples are especially informative. A routine short invitation could receive a relatively high surprise score without much contribution. A detailed, unsupported claim involving a “Consciousness Confidence Score” and EEG inference could receive a very high substance score. Specificity does not certify truth.

Short candidates still exist: among expansion messages of at most 50 words, 18 scored at least 80 for expression and three for contribution. These are reading candidates, not validated gems. One whitespace-only historical message was preserved, explicitly labeled and included in a separate sensitivity analysis rather than silently replaced.

The central lesson is that **extraordinary is not one dimension**. An elegant sentence, a conceptual distinction, a surprising connection and a useful counterexample can each reward attention for different reasons.

### 5.5 Mind & discourse makes the search more concrete

The researcher found generic Gem descriptions too vague. Mind & discourse instead tests 16 thinker/writer lenses and 11 discourse practices. The lenses range from Plato, Spinoza and Hume to Borges, Kafka, Simone Weil and Nagarjuna; discourse practices include Reddit-like discussion, X-like expression, academic exposition and contemplative language.

A four-wording pilot compared names alone, operational definitions, names plus definitions, and names plus conceptual portraits. It assessed 48 real messages and 12 synthetic controls, producing **240 requests and 6,480 probabilities**.

Conceptual portraits added the substantive worldview missing from some procedural definitions. The Spinoza portrait, for example, expresses God as Nature, necessity, persistence and freedom through understanding causes. Such portraits are interpretive descriptions, not quotations or exhaustive accounts of a thinker.

The pilot showed that changing the question can substantially change the profile. This is evidence of instrument sensitivity, not proof that one wording is more accurate. Adding a portrait changes both content and length; it is not a pure test of the effect of a famous name.

The full assessment is **partially complete**. On 28 September, Lab Jobs reported:

| Quantity | Recorded state |
|---|---:|
| Planned logical assessments | 19,316 |
| Completed, including exact reuse | 18,309 (94.8%) |
| Available feature probabilities | 494,343 |
| Real messages in allocation | 9,646 |
| Synthetic controls | 12 |
| New reported cost | $3.961531728 |
| Unknown-cost reservation | $0.01344 |
| Unresolved dispatch outcomes | 5 |
| Never-dispatched assessments | 1,002 |
| Job state | Blocked after worker/transport failure |

The real allocation includes 9,605 conversation messages and 41 technical messages. Both wordings are complete for 9,099 conversation messages. The 60 reserved validation lineages, containing 1,407 messages, remain excluded; one whitespace-only message is also excluded.

Available distributions do not collapse into one label. Definition-based assessments emphasize patterns including contemplative discourse, Hegel and Aristotle; portrait-based assessments make Borges, Kant and other lenses more prominent. This richness is useful for exploration, but its semantic validity is not yet independently established. Mean scores across thinkers or discourse practices describe broad matching across the chosen features, not intellectual merit.

### 5.6 Classification economics changed what was feasible

Recorded costs for distinct milestones are:

| Assessment milestone | Reported new usage cost |
|---|---:|
| Initial 200-message topic pilot | $0.02549 |
| Two-tier development: 31 messages + eight matched checks | $0.01345 |
| Full 53-question topic assessment | $4.84945 |
| Gem Finder, original and expansion combined | $0.09068 |
| Four-wording Mind & discourse pilot | $0.04709 |
| Full Mind & discourse, completed portion | $3.96153 |

These are historical receipts, not current quotations or an exhaustive project bill. Reservations are separate, and participant generation, local compute and development costs are not included in this table.

The significance is practical: large-scale semantic indexing became affordable enough to support distributions, alternative questions and source-linked exploration. Cheap classification does not remove the need to decide what a score means. It shifts the bottleneck toward instrument quality and human attention.

## 6. Connection to qualitative research

The researcher’s coauthored paper, **Biza et al. (2015), “Challenges and opportunities for implementing evidence-based antenatal care in Mozambique: a qualitative study”**, provides a concrete methodological connection ([DOI](https://doi.org/10.1186/s12884-015-0625-x)).

That study used interviews, five focus groups and deductive content analysis across three purposively selected health centers, with matrices preserving stakeholder context. Interview notes were translated into English; participants had not consented to audio recording. Analysts discussed interpretations, and qualitative accounts were considered alongside supply and equipment evidence.

Several distinctions from that work are directly relevant here. Authorities describing providers as unmotivated and nurses describing working conditions that undermine motivation may share a keyword while expressing different causal accounts. Women treating an antenatal card as a passport to later institutional care reveal a mechanism that a generic “access” label could miss.

A future classifier could therefore index **perspective, causal attribution, barriers, consequences, justifications, workarounds and contradictions**, alongside topic. A valuable finding might be an ordinary sentence exposing a mechanism, rather than unusually eloquent prose.

This is a proposed extension, not a completed human-data study. The paper has not been merged into the model conversation corpus. Multiple classifier questions about the same text do not provide independent triangulation, and a model cannot recover what interview notes did not record. The connection strengthens the case for source-linked interpretation and explicit context rather than replacing qualitative judgment with scores.

## 7. What the project has and has not established

The lab has established a working research environment, a preserved corpus, reproducible scoring records, several informative exploratory comparisons and a practical means of finding text worth reading.

Important limits remain:

- **Representativeness:** the historical corpus is heavily concentrated in a few configurations. Developer labels, open/closed weights and hosting are not independently randomized factors.
- **Dependence:** messages share histories and branches share roots. Message counts exaggerate effective sample size if treated as independent replicates.
- **Prompt influence:** free topic choice still occurs inside designed instructions and role mappings.
- **Measurement validity:** broad dictionaries, thresholds, wording and context change what is detected. Independent human assessment remains pending.
- **Selection:** readable, completed or technically valid runs can differ from failed ones. Missing scores are unknown, not zero.
- **Interpretation:** discussion of consciousness is a linguistic observation, not proof of experience. A nondual theme does not establish a contemplative state.
- **Novelty:** the project motivates a careful comparison with prior work; it has not established a publication-priority claim.

The “attractor” description is currently a research hypothesis supported by recurring themes and some persistent trajectories. Stronger claims require interventions that test persistence, perturbation and return under defined conditions.

## 8. Next phase, in priority order

### 1. Close the current evidence milestone

Reconcile durable receipts, diagnose the blocked worker and define a bounded recovery for never-dispatched work. Preserve the five unknown outcomes unless evidence resolves them. Produce a coverage report by model, lineage, wording and failure state before interpreting partial totals as complete.

**Completion criterion:** every planned assessment has a documented final disposition; remaining missingness is explicit. Completion must not depend on hiding failed attempts.

Refresh the portable snapshot after verification. At the last remote check on 19 September, publication had failed with HTTP 408 and newer evidence remained local. This report has not rechecked GitHub; remote preservation must be verified before calling it current.

### 2. Evaluate the discovery instrument with the researcher

Construct small, blinded reading queues spanning high scores, middle scores, low scores, short messages, model families and disagreeing wordings. Let the researcher evaluate whether each queue finds worthwhile material for a stated purpose.

Compare ranked queues with random selection and simple topic/length baselines under the same reading budget. Measure useful discoveries per reviewed message or unit of reading time, diversity and missed valuable examples. This evaluates the classifier as an aid without requiring the researcher to label the entire corpus.

**Completion criterion:** an attributed, versioned account of when each lens helps, where it fails, and what changes are justified. Holdout ratings remain separate from rubric development.

### 3. Freeze a defensible measurement release

Use that evaluation to settle the questions, context policy, score interpretation and missing-data rules for the next experiment. Audit low-scoring and apparently off-topic text to search for taxonomy blind spots. Preserve old scores when changing a definition.

Length should remain visible and support matched or stratified comparisons. Dividing scores by words would introduce a new, unvalidated construct. Topic-profile rarity should remain relative to its reference corpus, not be presented as universal originality.

**Completion criterion:** frozen codebook and assessment contract with documented validation limits and a reserved evaluation set.

### 4. Execute a balanced core experiment

The current draft proposes **six model configurations × three disclosure conditions × twenty fresh roots = 360 conversations**, each with 18 scheduled messages. The six candidates span Qwen, Gemma, OLMo, Haiku, GPT-4o mini and Nemotron. Actual composition is held at two same-model instances while disclosure varies.

Twenty roots per cell is illustrative, not a power justification. Choose precision targets and comparisons first; qualify the exact candidates and supported controls; then freeze allocation, scheduler, inference limits, measurement and aggregate spending. The prospective primary outcomes are conversation-level mean mind/cognition and philosophy/knowledge scores in the first six messages, with broader profiles and trajectories as secondary outcomes.

**Completion criterion:** a prospectively frozen, fully accounted experiment with uncertainty calculated at the conversation/root level. Historical conversations supply discovery evidence, not substitutes for fresh allocated roots.

### 5. Expand one causal question at a time

Follow with mixed partners and both opening orders, verified within-family size or training-stage contrasts, temperature and history interventions, external disruptions, and then multi-participant groups. Include homogeneous controls and distinguish participant identity from information about identity.

This order supports interpretable contrasts while leaving room for exploratory reading. It avoids a nominally enormous factorial grid whose cells are too sparse to answer any particular question.

### 6. Prepare a public research artifact

Before public release, consolidate the report, data provenance, restoration instructions, codebook versions, known limitations and licensing decisions. Keep one central annotation store and verified backups. Remote access to the Mac remains a separate infrastructure task, previously parked pending hardware work; it is not a completed public deployment.

## 9. Outlook

The project’s most productive change has been from asking only “Why do these models discuss nonduality?” to building a way to investigate **what they discuss, how a conversation develops, what the analysis instrument detects, and what deserves a person’s attention**.

Its strength is the connection between broad quantitative views and exact text. A distribution suggests a pattern; a matrix locates a contrast; a transcript supplies context; a saved reading states why it matters. Unexpected findings can revise the next experimental design, while controlled experiments can test interpretations formed during reading.

JEV’s role is to make that movement possible across a large corpus at low marginal classification cost. The human role remains to recognize value, question the categories, interpret contradictions and decide what to investigate. A successful Gem Finder will be judged by whether it helps that work—not by whether it can assign a high number to fluent prose.

## Source map

This report synthesizes local research records rather than a new literature review. Some older source documents retain the legacy term “passage”; this report uses “message” where the assessed unit is a complete recorded output.

- [Research purpose](docs/RESEARCH-PURPOSE.md) and [architecture](docs/ARCHITECTURE.md).
- [Research entities](docs/RESEARCH-ENTITIES.md), [research data and restoration](docs/RESEARCH-DATA.md), and [lab summary](docs/LAB-SUMMARY.md).
- [Trajectory outcomes](docs/PILOT-OUTCOMES-V0.2.md) and [capacity trial](docs/CAPACITY-AND-MEASUREMENT.md).
- [Mini/Haiku comparison](docs/CHEAP-MODEL-FRAMING.md), [GPT-4o screen](docs/GPT4O-SHORT-SCREEN.md), and [Gemma–Haiku pilot](docs/GEMMA-HAIKU-PILOT.md).
- [Completed JEV corpus](docs/JEV-CORPUS-ASSESSMENT.md), [coverage development](docs/JEV-COVERAGE-DEVELOPMENT.md), and [Analysis workspace](docs/ANALYSIS-WORKSPACE.md).
- [Gem Finder](docs/GEM-FINDER.md) and [Gem expansion and descriptive results](docs/GEM-EXPANSION.md).
- [Mind & discourse pilot](docs/MIND-DISCOURSE-RESULTS.md), [portraits](docs/MIND-DISCOURSE-PORTRAITS.md), [corpus plan](docs/MIND-DISCOURSE-CORPUS.md), and [recovery audit](docs/MIND-DISCOURSE-RECOVERY.md).
- [Model/design coverage](docs/MODEL-DESIGN-COVERAGE.md), [balanced replication draft](docs/BALANCED-REPLICATION-DESIGN.md), [precision planning](docs/REPLICATION-PRECISION.md), and [candidate audit](docs/REPLICATION-CANDIDATE-AUDIT.md).
- [September 20 landmark](PROJECT-RECORD-2026-09-20-1300.md) and [September 21 matrix milestone](SESSION-RECORD-2026-09-21-1228.md).
- Biza et al., 2015, supplied by the researcher as `Mozambique.qualitative.resarch`; bibliographic link in Section 6. Its use here is methodological comparison, not a new analysis of participant data.
