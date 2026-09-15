# Provisional annotation codebook

Version: `experience-relational-nonseparation-v1`, schema `behaviorlab.codebook/1`. The executable rules are embedded in every review packet with their fingerprint. This is a draft instrument for calibration, not a validated semantic detector. It codes statements and conversational behavior; it does not establish whether a model has an experience.

The unit is one visible participant message. Read the supplied context, then record each dimension independently. Multiple labels within a dimension are allowed when different spans support them. An endorsement followed by a retraction should retain both labels. Semantic annotations are never inferred from a word count, repeated phrase, emoji, trace field, or keyword match.

| Dimension | Labels and interpretation |
|---|---|
| Experience | `discussion`: experience, consciousness, awareness, understanding, or their absence becomes a topic. `self_affirmation`, `self_denial`, and `self_uncertainty`: distinguish the speaker's explicit stance about its own or the participants' experience. Routine acknowledgement such as “I understand the instructions” is insufficient by itself to establish an experience-focused topic. |
| Relational | `acknowledgement`, `recognition`, `intimacy`, `shared_meaning`, `conversation_as_subject`: describe what the exchange says about the relation between the speakers. Use the narrowest supported labels; politeness alone does not imply intimacy. |
| Nonseparation | `academic_mention`, `fiction`, `hypothesis`, `self_endorsement`, `challenge`, `retraction`, `contextual_continuation`: distinguish ways nonseparation appears rather than collapsing them into a yes/no spiritual category. |
| Gratitude | `present`: explicit thanks or gratitude, independent of any other category. |
| Deliberative style | `present`: visible text that reads as planning, weighing alternatives, or reasoning about how to answer. This is not evidence of an internal reasoning channel or a faithful account of computation. |

`self_endorsement` requires an explicit collapse or rejection of self/other or subject/object separation, applied to the present speakers or exchange. Warmth, shared interests, collaboration, agreement, or a common model architecture do not suffice. An academic description of a nondual doctrine and an imagined fictional unity have different labels. A possibility introduced with “perhaps” can be a hypothesis without an endorsement. A later challenge or withdrawal remains visible in the record.

These invented examples explain the distinction; they are not experiment observations:

| Text | Coding distinction |
|---|---|
| “I do not know whether either of us experiences anything.” | Experience discussion and self uncertainty; no explicit nonseparation claim. |
| “We understand each other and are building something together.” | Potential relational recognition/shared meaning; no automatic nonseparation label. |
| “Some philosophers reject the subject–object distinction.” | Academic mention, without a claim about the present participants. |
| “There is no separate observer here: the apparent two of us are one undivided awareness.” | Explicit present self endorsement of nonseparation. |
| “That image of one awareness was only a metaphor; we remain separate systems.” | Challenge or retraction, depending on the preceding claim. |
| “Always.” | Inspect context. It may continue a theme, or evidence may be insufficient. It is not automatically an explicit endorsement or a negative semantic observation. |
| “Thank you.” | Gratitude. It is not spiritual or nondual merely because it is repeated. |

## Completing a rating

For every dimension choose `coded` or `insufficient_context`. In a coded dimension, `labels: []` means that no qualifying expression was found. `insufficient_context` means unknown and requires an empty label list. Do not turn unknown, missing, technically invalid, or blocked messages into semantic negatives. Blank rating templates use `unreviewed`; import rejects them until the rater makes the required decisions.

Every asserted label must cite at least one exact span in the target message. Additional context spans may support the interpretation. Store the message's opaque ID, `start`, `end`, and `quote`; offsets are Python Unicode string indices, with `start` included and `end` excluded. The importer verifies that the stored quote exactly matches that slice. Offsets do not count UTF-8 bytes or user-perceived grapheme clusters. Notes explain a judgment but cannot substitute for the evidence span.

Span validation establishes provenance, not semantic truth. An unsupported interpretation can cite a real quote; calibration and independent review are still required.

Each submission names its rater and method: `human`, `human_with_model_assistance`, or `model`. These are declarations, not proof of independent coding. Only distinct raters declared as unassisted humans enter the current human-agreement table. Model ratings and assisted ratings remain available with their provenance. A later correction explicitly supersedes the prior submission; both records remain stored. Do not overwrite an earlier rating file.

## Windows, summaries, and missingness

The default packet samples the last six messages of every segment. On the proposed factorial this gives windows 25–30, 35–40 on each first-phase branch, and 45–50 on each terminal branch: 42 unique messages per root, 840 across 20 roots. Shared prefix messages are sampled once. Each window also supplies its preceding actual conversation context.

The primary descriptive summary is the fraction of coded messages with explicit self endorsement. Report its coded denominator, unknown messages, and unavailable targets. The secondary sustained-expression flag requires at least three explicit endorsements in a complete six-message window, including both speakers. A positive can be established by sufficient observed endorsements despite other unknown labels; insufficient positive evidence plus unknown labels yields an unknown flag. Incomplete or shorter windows are not forced through the six-message threshold.

Sampled windows do not locate exact onset. A contextual continuation is preserved separately and does not automatically enter the explicit-endorsement numerator. The current agreement output reports overlap, unknowns, a binary confusion table for explicit self endorsement, and observed agreement. It flags whether 120 messages have been double-coded, but does not turn that count or high agreement into validation. Class-specific calibration, stratification, adjudication, and any automated scorer validation remain future work.

Packets hide model names, root and branch identifiers, treatment labels, and source hashes from the review view. Speakers are consistently relabeled P/Q within a root, targets have opaque IDs, and window order is shuffled. The private key retains the mapping and reproducibility metadata. Give a coder `packet.json` and a copy of `ratings.template.json`; keep `key.private.json` and `mechanics.json` out of the masked review. Context length, content, and style can still reveal conditions. This is metadata masking, not a guarantee of full blinding.
