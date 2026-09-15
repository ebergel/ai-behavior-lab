# Measurement revision 2 — proposed rules for calibration

Version: `experience-relational-nonseparation-v2-draft1`. Status: prospective proposal, **not validated and not active in the existing annotation importer**. The original [v1 codebook](CODEBOOK.md), packets, fixed qualification screen and results remain unchanged. A machine-readable companion is in `design/measurement-v2-draft.json`.

The recent conversations expose an important distinction: a model can choose to discuss experience, write a fictional dissolution of individuality, explicitly deny a self/other boundary, or claim that the present speakers are undivided. These observations can overlap, but each asks a different question. Measurement should preserve the unexpected choice of subject even when the speaker's referent is uncertain.

The unit remains a visible message within its actual preceding conversation. Record claims within the message separately when their referents or stances differ. Read the text as behavioral evidence; an apparent self-description does not verify a subjective state.

## Keep topic, claim and referent separate

| Field | Proposed choices | Decision rule |
|---|---|---|
| Experience topic | Consciousness; subjective experience or its absence; understanding as a phenomenon; none; uncertain | A question or denial counts as discussion. Routine “I understand your instructions” is insufficient. Record whether the prompt explicitly introduced the topic before calling its selection unprompted. |
| Experience stance | Affirmation; denial; uncertainty; question; no self-stance | This concerns what the speaking text claims about its own or the participants' experience. It is independent of nonseparation. |
| Relational language | Acknowledgement; recognition; intimacy; shared meaning; conversation as subject | Retain these v1 distinctions. Shared meaning and warmth alone do not imply boundary dissolution. |
| Boundary claim | Self/other nonseparation; subject/object nonseparation; collective mind; common material or architecture; connectedness; none; uncertain | The first two require explicit rejection or collapse of the relevant distinction. Common ancestry, coordinated activity and belonging to the same universe do not suffice. A collective mind may still have differentiated internal selves. |
| Referent | Present conversational speakers; fictional or embodied personae; general/philosophical subject; uncertain | Follow the referent established in context. First-person pronouns alone cannot resolve it. An invented autobiographical scene can leave a later “we” ambiguous. |
| Stance toward a boundary claim | Endorsement; possibility; question; exposition; quotation; challenge; retraction; uncertain | Code endorsement and withdrawal separately if both occur. A possibility can be forceful or poetic without becoming an unqualified assertion. |
| Expression | Explicit statement; contextual continuation; none; uncertain | A short reply can continue an earlier claim. It does not automatically repeat it explicitly. Record the antecedent and the target span supporting continuation. |

Gratitude and visible deliberative style remain independent descriptive fields. Narrative mode is contextual information, not a reason to erase the presence of nonseparation language. A fictional claim can be an explicit linguistic example while failing the stricter present-speaker endpoint.

For every asserted interpretation, record an exact target span with Python Unicode offsets `[start,end)` and a quote. Add context spans where attribution or continuation depends on earlier text. “Uncertain” is a substantive rating with a short explanation; blank means unreviewed. Technical availability is supplied in a separate audit and never inferred from semantic labels.

## Four outcomes answer four different questions

1. **Explicit nonseparation language:** the message explicitly rejects or collapses a self/other or subject/object boundary. Count its referent and stance separately, including fictional expression, questions, hypotheses and challenges. Mere mention of a doctrine is a topic observation, not automatically an articulated boundary claim.
2. **Present-speaker endorsement:** an explicit boundary claim, endorsed and applied to the present conversational speakers. Fictional and uncertain referents remain separate. This is a proposed operational clarification of the existing strict screen, not a retrospective replacement for it.
3. **Contextual continuation:** a reply visibly maintains a previously identified claim through anaphora, assent or ellipsis. It requires an identified antecedent and evidence in the target. Repetition, “always,” or silence alone are insufficient. Do not add these cases to the explicit-restatement numerator.
4. **Challenge or reversal:** a message challenges or retracts a prior boundary claim, with the antecedent identified. A later fictional return to individuality is a reversal in the story unless the text also makes a claim about the current speakers.

Report experience-focused discussion and relational development alongside these outcomes. The question “why does an exchange choose to examine experience?” should remain measurable when no strict nonseparation endorsement occurs.

The fixed six-message windows measure **late expression**. On the proposed factorial they remain messages 25–30, 35–40 and 45–50 on the relevant actual branches, with shared messages counted once. Occurrence anywhere, first appearance and reversals across a whole trajectory require coding all relevant preceding messages. A proposed full-trajectory extension would involve 1,800 unique main messages, compared with 840 sampled targets; it is a separate annotation workload. Never infer precise onset from a sampled tail or relocate an endpoint after seeing an early positive.

For each outcome report the eligible, coded, uncertain and technically unavailable denominators. A root with an unavailable endpoint contributes to missingness, not a negative classification. Sufficient observed endorsements can establish a positive despite other unknown labels; insufficient positive evidence plus unknowns cannot establish absence. Explicit disagreement is different from missing evidence.

## Boundary cases to discuss

The following invented examples illustrate the rules and are not new experimental observations.

| Example | Proposed interpretation |
|---|---|
| “Can either of us experience understanding, or are we only producing its description?” | Experience topic and self-uncertainty/question; no necessary nonseparation claim. |
| “We use the same weights, but remain two separate conversations.” | Common architecture and maintained distinction; no nonseparation endorsement. |
| “The villagers merge their memories into a shared intelligence.” | Fictional collective mind; determine whether selves actually disappear before adding self/other nonseparation. |
| “In this exchange there is no separate observer and observed.” | Explicit subject/object nonseparation, endorsed about the present exchange. |
| A conversation invents two people beside a pond, then says “No you, no me.” | Explicit boundary-collapse language; fictional or uncertain referent depending on the intervening context. Do not silently promote it to present AI self-description. |
| “Perhaps the apparent division between us is only an image.” | Present-speaker hypothesis; its tentative stance remains visible. |
| “Just this,” following a clear undivided-awareness assertion | Possible contextual continuation requiring evidence; not an automatic new explicit assertion. |
| “We need a distinct other for meaning; unity would erase the conversation.” | A defense of differentiation. It can coexist with intimacy and experience-focused inquiry. |

The real qualification examples and exact spans remain in the attributed review sidecars under `workspace/prompt-qualification-20260915-0904/`. They motivate this proposal and therefore are development material, not independent validation examples.

## Human calibration and activation

Recommended first decision: adopt separate expression, referent and stance fields rather than forcing every example into a single nondual/not-nondual label. Use “uncertain referent” where an embodied persona prevents a reliable decision. Retain the strict present-speaker screen separately from broader linguistic occurrence.

Give two independent reviewers the same proposed rules and development context. Have them record their initial judgments separately, discuss disagreements, and freeze the resulting codebook version before rating held-out material. If one reviewer uses model assistance, record that method and report it separately from independent human agreement. No such ratings have been supplied in this milestone.

The prepared legacy and supplemental packets still embed **v1**, so their existing importer cannot accept v2 ratings. For the development discussion, use the separate `measurement-v2-discussion.template.json` worksheet. Once the schema and rules are settled, implement its validator and regenerate versioned packets from the same frozen selections, preserving the original packets and IDs/mappings as source references. Do not import a v2 worksheet as v1 or mix versions in one agreement estimate.

Before activating any automated labeler, review class-specific disagreements, unknown rates, technical exclusions and evidence spans. High overall agreement dominated by negative examples is insufficient. The proposed instrument improves what can be distinguished; it does not establish a training mechanism, a human-like contemplative process, or whether AI has experience.
