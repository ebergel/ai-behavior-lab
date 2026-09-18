# Session record — dictionary research entities

Recorded: 2026-09-18T18:49:20.521589-03:00 · America/Argentina/Cordoba (UTC−03:00).
Scope: place the clarified research artifact vocabulary in the Lab dictionary.

## Completed

The in-app dictionary now has 40 entries, including a Research entities & units section with 24 linked entries. Twenty-two definitions are new; the existing passage and lineage entries are clarified and grouped into this section. The legacy passage entry retains its ID while linking to the distinct Message, Excerpt, Analysis target and Context definitions. Each entity has a plain definition, practical use, technical/counting rules, limitations and source references.

The dictionary introduction now describes its laboratory-wide scope. Linked visual relationships show Conversation → Message → Optional excerpt and Selected object → Assessment → Feature scores. Existing passage/lineage bookmarks with the former evidence category migrate to entities. Search, category filtering and Gem return state remain available. Guide version: dictionary-2026-09-18-v4.

Clarified that Gem inherits the corpus's two-event preceding context window, which can include external interventions; Mind & discourse sends only its selected message text. This edits explanatory guide text only. Exact frozen rubric/question wording is unchanged.

Updated LAB-DICTIONARY.md, RESEARCH-ENTITIES.md and the continuation milestone. The population-label migration and library message/event/run-category audit remain future work.

## Verification

Full Python suite: 362 passed. Full JavaScript suite: 100 passed, including legacy-bookmark migration and linked entity-map/Gem return-state checks. The dictionary contract tests were rerun after the context wording correction: 3 passed. All definition cross-references and implementation-source files resolve; canonical scoring rubrics still match their frozen source exactly. Syntax and git diff checks passed. Live browser inspection confirmed the 24/40 section count, entity map, searchable entries, and navigation to the Message definition. App Hub restarted the local server for the explanatory guide update.

## Boundaries

No inference calls, classifier changes, notebook or research-snapshot writes, source changes or denominator recalculations. Stable term IDs and historical assessment payloads are preserved. The dictionary is the current in-app vocabulary reference; broader UI label consistency is the next separate application of these definitions.
