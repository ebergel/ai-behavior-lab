# Research entities and units — vocabulary v1

Status: published in the Lab dictionary, 18 September 2026, following the researcher's request to place the vocabulary there. The dictionary's Research entities & units section is the in-app reference. This document also specifies the display naming contract; it is not a database migration or a change to frozen assessment inputs. The researcher identified ambiguity between messages, targets, passages and source records in the population banner.

## Evidence hierarchy

**Conversation → message → excerpt** is the everyday reading hierarchy. Branches and external events qualify that hierarchy:

| Entity | Meaning and counting rule |
| --- | --- |
| Conversation | One initiated dialogue with its participant roster, setup and recorded history. It may contain alternative continuations. A conversation need not have completed successfully. |
| Branch / conversation path | One continuation through a conversation's history. A path contains ordered messages and any intervening events. Shared prefix messages count once when counting unique messages in the conversation. Two branches are not two independent conversations. |
| Message | One recorded contribution by a participant, identified by conversation ID plus message ID and its source revision. It can contain multiple paragraphs. A capped message remains a message, with a partial-output flag. Visible content and recorded reasoning are separate fields, not two independent participant messages. |
| Turn / scheduled position | A position in the dialogue schedule, not a synonym for message, model pair, or full round. An unavailable or undispatched position does not supply an observed message. Turn numbers may recur across branches; IDs establish identity. |
| Excerpt | An explicitly bounded selection of text within a message, with source identity and exact offsets/quotation. Reserve this name for actual selections. A whole recorded reply should be called a message, rather than a passage. Multi-message windows require explicit ordered membership. |
| External intervention | An event introduced from outside the regular participant roster. It can contain model-generated text and affect subsequent context without adding a regular third participant. Keep intervention and participant-message counts separate. |
| Transcript | The recorded representation of a conversation or one of its paths. It is not an additional sampling unit. |

The storage envelope is a **run**. A conversational run records a dialogue; a technical run records an integration/qualification check. The current library includes both, as well as separately displayed synthetic fixture runs. A synthetic control text used by a classifier is a different object from a synthetic fixture run.

Above conversations, a **campaign** groups executions under an operational plan. A **study** or research collection can gather conversations across campaigns. Model, model family, participant role and experimental condition are properties or linked entities, not successive levels within a conversation.

## Analysis relationships

**Target** names an object's role in a particular analysis. It is not another level of text.

- A **message target** is an existing message selected for assessment. The current Mind & discourse and Gem samples select messages. An excerpt target or a whole-conversation target would require its own explicitly declared unit and method.
- **Context** is other evidence supplied to interpret the target. It is not added to the target's message count. Gem inherits the corpus topic window of up to two preceding evidence events, including interventions. Mind & discourse currently sends only the target text. Context policies must remain attached to their assessment versions.
- A **sample** is the frozen set of selected target identities under a stated sampling rule. A **dataset** combines those units with specified metadata and measurements at a known revision. A **filtered subset** is the part currently selected for browsing. Repeated assessments do not expand the sample.
- An **assessment** evaluates a target using a specified assessor/model, instrument version, wording, context and procedure. Different wording conditions yield different assessments of the same message.
- A **question / feature** is one dimension assessed. A **score** is the recorded result for that dimension. A vector of 27 scores still describes one message under one assessment condition.
- An **API request / attempt** is execution/accounting provenance. Requests can bundle questions or split them into packs, and attempts can fail or be retried. Request, assessment and target totals must have independent labels.
- A **lineage** is the laboratory's grouping for related/identical conversation structures and shared ancestry. The current coverage code hashes models, prompt and recorded message structure; it is an operational grouping, not proof of independent generation. Preserve the frozen grouping rule and show lineage only where an actual lineage ID exists.

## Unit mapping from the earlier interface

| Earlier label | Underlying count | Current wording |
| --- | --- | --- |
| Mind & discourse “48 target passages” | 48 selected recorded messages, copied with run ID, message ID and source hash | **48 messages in this assessment sample** |
| Mind & discourse “48 source records” | Distinct run IDs for those 48 messages; all are selected conversational records | **From 48 conversations** |
| Gem “target passages” | Selected recorded messages, including any explicitly marked unscored reader example | **Messages**, with assessment status separate |
| “Source records” in an arbitrary dataset | Distinct run IDs, which may include technical runs | **Source runs**, or **conversations** when that restriction is verified |
| Library “472 conversation records” | Started nonsynthetic runs, including short technical/check records | **472 runs**, with conversation/technical eligibility categories exposed separately |
| Library “11,245 recorded messages” | Existing importer message counters; these differ from the topic corpus's eligible-message frame | Preserve the historical total and explain scope until a message/event counting audit establishes a common definition |
| “Passage” in old requests and plans | Historical instrument wording; exact selections/context vary by version | Preserve original bytes and identifiers; map to the verified unit in the display |

“Source record” is particularly ambiguous: the current banner counts run IDs, not files. Use **source artifact** for an original file, journal or response receipt and **source revision** for its checksum/version. One file or campaign journal can represent several runs. File count is not conversation count.

## Display contract

For the current Mind & discourse view:

> Assessment sample: **48 messages from 48 conversations**. Synthetic controls: **12 separate texts**.
>
> Current subset: **3 messages from 3 conversations**, matching Consciousness ≥80; **6.3% of sample messages**.

Every quantitative view should declare its **unit of analysis**, dataset/sample and eligibility/filter rules. Use the unit's noun in its counts: messages, excerpts, conversations or synthetic control texts. Use “target” in methodological explanations and request provenance, rather than as an alternate noun in population counts.

Distinct units are not necessarily independent observations. Messages in a conversation share history; branches share prefixes; runs can share prompts, conditions and model configurations. Statistical claims must identify the experimental unit and dependence structure separately from the row displayed in a table.

## Next implementation boundary

The Lab dictionary contains the separate entries and linked relationships. The 18 September label migration applies them to population banners, Mind & discourse, Gem Finder, JEV, Analysis, the reader and research dialogs. Whole replies are messages; selected text is an excerpt; stored quotations can cover either. Passage is now only a dictionary search/bookmark alias for Message. Legacy route/transport keys and exact recorded instrument text remain compatible. The full library is labeled runs, including conversations and technical checks; known Mind & discourse source counts are labeled conversations. No counts were recomputed. Audit library participant-message/event counters and run categories before presenting all 472 runs as conversations or harmonizing the 11,245/11,054 totals. Preserve URLs, stable source IDs, exact frozen payloads, scores and saved research notes. A naming change must not silently change eligibility, deduplication or scientific denominators.

Implementation references: `explorer.py` (`base_summary`, legacy/campaign importers); `population.py`; `jev_coverage.py` (`context_for`, `build_inventory`); `gem_plan.py` (`select_items`, `payload`); `discourse_probe.py` (`prepare`, `payload`); `discourse_view.py`; `topic_atlas.py` (exact-span evidence).


## Lab-wide terminology audit · 18 September 2026

The follow-through covers Topic atlas, Conversation Finder, Model & Design Coverage, Topic Trajectories, the library/reader, research collections, Study workbench, Model assessment, JEV, Gem Finder, Mind & discourse and Analysis. Page headings provide a **Research units** link to the Lab dictionary.

- Inventory counts identify **runs**; unstarted Coverage entries identify **planned run slots**. Verified conversational samples can still identify **conversations**. These terms describe different aspects of the same source, not additional observations.
- Topic atlas separates the full library, its eligible run sample and the current subset. In its dictionary panel, selecting a topic changes the entry without reducing the scope. In its Conversations panel, the subset follows phrase/review mode and search, before pagination.
- Topic atlas frequency columns count **runs with matches**, not phrase occurrences. **Initial topic** uses resolved opening reviews as its denominator. **First 6 positions** refers to the scheduled opening window, not six guaranteed observed messages. **Repeated** requires at least two distinct matching messages. Literal variants separately report **Occurrences**, **Messages** and **Runs**.
- Finder uses the same phrase-match windows. Collection and workbench totals count runs. Trajectory list entries count sampled messages; a selected external event is labeled an intervention, while an unscored/missing position remains a position.
- Current interface copy and validation errors use message/excerpt terminology. Original source titles, attributed notes, historical reports, exact instrument wording, and legacy API/route keys retain their recorded form. They are provenance, not newly defined research units.

This is a display and documentation update. It does not reclassify the inventory, change score eligibility, recompute scientific denominators or harmonize historical message/event counters. The separate counting audit described above remains pending.
