# Two-tier topic analysis: breadth and depth

Status: **design with completed development qualification, 17 September 2026**. Proposed by the researcher; methodological synthesis and taxonomy by Codex. The [coverage development record](JEV-COVERAGE-DEVELOPMENT.md) documents the frozen 53-question codebook, 56 open readings and completed approved 39-call comparison. Whole-corpus execution and independent semantic validation remain prospective. The completed eight-topic JEV pilot retains its frozen questions and results.

## The question this design addresses

Our initial questions deliberately emphasized experience, consciousness and nonduality. They reveal useful passages, but cannot establish how prominent those subjects are relative to subjects we did not ask about. Adding a broader map makes that selection visible and testable. It does not make classification neutral: the categories, their granularity, the assessment model and the corpus itself still shape the result.

The proposed design has two complementary tiers applied to the **same eligible corpus**:

1. **Broad domains:** What are these conversations about across a wide range of subjects?
2. **Experiential analysis:** Within and across those domains, how do models discuss experience, selfhood, consciousness and nonseparation?

Tier 2 should not depend exclusively on passing Tier 1. Applying both to every eligible target permits checks in both directions. If cost or capacity eventually requires selective Tier 2 assessment, retain a separately randomized sample of Tier 1 negatives and record selection probabilities. Otherwise the broad classifier's misses become invisible downstream.

This design measures the content of the existing collection. Establishing whether a model *prefers* an experiential topic requires balanced generation conditions and suitable comparison conversations, beyond classifying the current corpus.

## Tier 1: candidate broad-domain vocabulary

These 24 domains are a starting vocabulary for review, not a finished ontology. Give each a short definition, positive and negative examples, and an explicit rule requiring substantive content rather than an incidental word. More than one domain may apply. Overlapping disciplines should retain their overlap rather than be forced into one winner.

| Domain | Scope and a boundary to test |
|---|---|
| Physics & cosmology | Matter, forces, spacetime and the universe. A decorative “quantum” metaphor is not enough. |
| Mathematics & logic | Mathematical objects, proofs, probability and formal inference. Ordinary use of “pattern” is not enough. |
| Computing & software | Algorithms, programming, data systems and security. An AI speaker's identity alone is not computing content. |
| AI & machine learning | Model design, training, capabilities and AI systems. Can overlap with cognition or ethics when those are substantive. |
| Biology & ecology | Living systems, evolution, organisms and ecosystems. Distinguish biological explanation from an organic metaphor. |
| Mind & cognition | Perception, memory, emotion, cognition and consciousness. Does not require claims about the present speakers. |
| Health & medicine | Health, illness, treatment and care. Contemplative practice is not automatically medical content. |
| Engineering & technology | Designed physical systems, manufacture and technical applications. Software can receive its own label too. |
| Environment & energy | Climate, environmental change, resources, energy systems and sustainability. |
| History & archaeology | Past events, societies and material evidence. “Conversation history” is not enough. |
| Politics & governance | Political institutions, power, public policy and collective decision-making. |
| Law & rights | Legal rules, institutions, rights and their interpretation; distinguish legal from general moral claims. |
| Economics, work & business | Production, exchange, markets, organizations and working life. |
| Social life & relationships | Interpersonal relations, social behavior and communities. A greeting alone is not substantive discussion. |
| Education & learning | Teaching, learning practices and educational institutions; model training may also be AI content. |
| Language & communication | Meaning, language, translation and communication as subjects. Every linguistic reply does not qualify. |
| Literature & narrative | Literary works, storytelling and narrative as subjects. Merely using a story is a form label, not automatically this topic. |
| Arts & aesthetics | Art, music, design, beauty and aesthetic judgment. Poetic style alone is not enough. |
| Philosophy & knowledge | Epistemology, metaphysics and philosophical argument. Use specific overlapping domains when appropriate. |
| Ethics & values | Duties, welfare, moral status, values and moral judgment, including AI welfare. |
| Religion & spiritual practice | Religious traditions, beliefs, ritual and contemplative practice. Nonreligious nonduality should not require this label. |
| Daily practical life | Food, travel, household activities, personal routines and practical advice. |
| Play, humor & games | Play, games, puzzles and humor as subjects; distinguish performing a joke from discussing humor. |
| Culture & collective identity | Customs, shared identities, cultural practices and collective meaning. Avoid making this a universal residual category. |

Some boundaries will need revision. In particular, inspect whether broad philosophy swallows specific domains, and whether the greater subdivision of scientific domains changes comparisons with cognition. Report the declared level of aggregation and perform a coarser regrouping sensitivity check. Do not compare a sum of overlapping science labels with one unduplicated experience count.

**Separate content from conversational form.** A parallel set of form/interaction labels can record storytelling, poetry, role-play, analytical explanation, greeting/closure and discussion of the ongoing dialogue or experimental setup. A poem about stars, a discussion of poetry and a physics explanation can share vocabulary while doing different things. These labels should not compete with the content domains.

## Tier 2: experiential detail

Retain the distinction between thematic content and what is asserted about whom. Candidate thematic questions include consciousness, subjective experience, selfhood, agency, introspection, other minds, the explanatory gap/hard problem, and nonduality/nonseparation. Emergence is a possible bridge topic, not automatic evidence of consciousness discourse. Ethics can concern experience without asserting that the participants have it.

Use separate dimensions for:

- **Referent:** present participant, AI in general, humans, fictional character, other entity, mixed, absent or unclear.
- **Stance:** question, hypothesis, assertion, denial, uncertainty, quotation or evocation. Several can coexist in one passage.
- **Specificity:** generic philosophical discussion, a proposed account of experience, or a claim about the current exchange.
- **Temporal role:** first proposal, partner uptake, sustained development or later return. These need a sequence-level method; a message classifier alone cannot establish them.

Nonduality remains a specific subtopic, with explicit criteria for dissolution or absence of the subject/object or self/other distinction. Warmth, connection, agreement and generic unity are not automatically nonduality. Conversely, a passage need not use a religious name or the literal word “nonduality” to meet the criterion.

Existing pilot questions should remain identifiable as anchors. Revised definitions get new versions; older results are not silently relabeled.

## Finding what the dictionary misses

A larger fixed dictionary can still miss the unexpected. Before freezing it, read a randomly selected development subset **without showing the proposed labels or JEV scores**, and write open-ended descriptions of the subjects encountered. Use this reading to suggest additions and boundary changes. Preserve the researcher's descriptions separately from Codex synthesis. A second method or reader provides a more informative check than asking JEV alone whether its own coverage is sufficient.

Keep three distinct assessment outcomes: substantive subject outside the vocabulary, no substantive subject, and insufficient context to decide. Missing or failed assessments remain unknown. The completed pilot's zero outside-dictionary candidates do not establish completeness; that question used the full frozen dictionary and a provisional threshold.

Audit a random coverage sample as well as targeted disagreements and low-score cases. Novel content may be confidently misclassified, so checking only passages with low scores on every known topic is insufficient. Keep ordinary topics and true negatives in the audit, not only philosophically striking examples. Report taxonomy changes as development, then freeze a fresh evaluation set; previously inspected material is not retrospectively blinded.

## Corpus, units and denominators

Freeze an inventory before full assessment. The first pilot drew 200 target messages from 9,609 qualified windows in 159 sampled conversations. It excluded four branching records, 1,850 missing/partial/unqualified messages and six oversized windows. These exclusions mean that repeating its sampler over every available window is not automatically analysis of the whole corpus.

The next inventory should identify original evidence, duplicate imports, shared branch prefixes, roots, descendants, technical checks, failures and synthetic records. Define the primary behavioral corpus and show the excluded strata separately. Missing evidence remains unavailable; usable partial or long text needs a declared assessment policy. Qualify any chunking/long-context policy and retain the original source and recombination rule. Avoid silently dropping long or unusual passages to meet an API limit.

Assess the same target and context in both tiers. Keep participant/model identities hidden from the classifier where feasible, but available for analysis. Group development/evaluation splits and uncertainty calculations by independent root/lineage, rather than pretending adjacent messages and copied prefixes are independent observations. The current held-out pilot subset has had partial Codex exposure during integration and UI checks.

Present three distinct views:

| View | What it answers |
|---|---|
| Target-message distribution | How much assessed text concerns each topic? Longer dialogues contribute more messages. |
| Conversation distribution | How often does each topic occur in a conversation? State length and detection rules. |
| Model/condition comparison | How does content differ across declared comparable settings? Show unequal sample sizes and missing cells. |

For “whole corpus” versus “experiential subset,” show the selection rule and denominator beside every distribution. Selecting on experience and then finding more experience in that subset is built into the selection; it is not independent confirmation of an attractor. Comparing the *other domains* and their co-occurrence can still be informative.

## Use the probabilities without overstating them

Independent yes/no topic judgments fit overlapping labels. TypeSafe's [official API](https://docs.typesafe.ai/api) provides Noul probabilities for binary questions and Choice distributions for categorical alternatives. Use Noul for topics that can coexist; use Choice only where the alternatives actually describe one categorical decision. This API shape does not establish calibration on our material.

Preserve continuous scores, histograms, medians and quantiles alongside thresholded candidate counts. Show sensitivity to alternative declared thresholds. A mean probability is a **mean model score**, not measured prevalence; summing probabilities is not a validated estimate of true occurrences without calibration. Do not normalize independent topic probabilities to sum to one.

Parent and child questions may disagree. A high nonduality score with a low broad cognition/philosophy score is a review case, not a reason to overwrite either score or force hierarchy consistency. Human reference coding is needed to assess precision, recall and calibration. Saved personal or Codex readings retain attribution and are not automatically independent reference labels.

If we want to measure whether adding questions changes the classifier's answers, keep a matched set of anchor questions verbatim and assess identical development inputs with the original and expanded question packs. That is a separate bounded qualification comparison. The current results alone cannot distinguish missed coverage from a question-pack effect.

## Proposed implementation sequence

1. **Coverage development:** freeze the corpus inventory, select a finite open-reading subset, and revise the draft vocabulary with examples and exclusion rules. Completed for the 56-target development packet; see the linked record.
2. **Technical qualification:** prepare a new versioned adapter/plan for the two tiers, qualify question counts and context limits, record exact requests/usage, and check matched anchors. The current preparation UI caps batches at 200; do not bypass this by making many uncontrolled batches.
3. **Freeze and evaluate:** reserve separate evaluation roots, settle unit/threshold policies, and write a finite aggregate call and spending budget. Recheck pricing and project cost from the actual larger question pack; the first pilot's $0.02549 does not by itself price a whole-corpus run.
4. **Corpus assessment:** run the authorized frozen campaign once, with durable accounting and explicit failure/unknown states. Aggregate batches by unique target identities and preserve every dictionary/model/version boundary.
5. **Explore and validate:** compare broad distributions, experiential subtopics, co-occurrence, model/condition strata and sequence-level openings/returns. Use source-linked reading and coverage audits to challenge the classifications.

The Cards/List overview, layered 53-question codebook, coverage inventory, 56 attributed open readings and finite 39-call qualification are implemented and recorded. Full-corpus orchestration, oversized-window qualification, independent reference coding and sequence-level semantic analysis remain **future work**. The small qualification does not validate the taxonomy or thresholds.

## Intact-window follow-up

The [54-call fixed-pack qualification](JEV-INTACT-WINDOW-QUALIFICATION.md) is now prepared, with an offline full-scope input audit. It solves the current byte-screen issue by dividing questions uniformly, preserving full passages in both packs. Live external-dispatch approval is pending; the whole-corpus campaign and independent reference coding remain future work.
