# Session record — lab-wide naming consistency

Recorded: 2026-09-18T19:12:52-03:00
Timezone: America/Argentina/Cordoba
Scope: extend the agreed research-entity vocabulary across the laboratory interface, especially Topic atlas.

## Completed

- Audited Topic atlas, Conversation Finder, Model & Design Coverage, Topic Trajectories, library and reader, research collections, Study workbench, Model assessment, JEV, Gem Finder, Mind & discourse and Analysis.
- Whole recorded contributions are messages; selected spans are excerpts; stored inventory counts are runs. Unstarted Coverage entries are planned run slots. Synthetic control texts and external interventions keep distinct labels.
- Added a Topic atlas population banner separating library inventory, all eligible runs, and the current reading scope or matching subset. Topic selection in the dictionary panel does not falsely reduce the scope. Conversation-mode counts follow phrase/review criteria and search before pagination.
- Clarified run-level frequency columns, first-six-position opening windows, resolved-opening-review denominators, and separate phrase occurrence / message / run counts.
- Added a Research units link in common page headings. Updated current help/error copy and rebuilt the Analysis browser bundle. Stable API keys, routes and saved recipes remain compatible.
- Updated the research-entity, population and continuation documentation.

## Verified

- Full Python suite: 362 tests passed.
- JavaScript suite: 104 tests passed, including added coverage for atlas population/filter/page semantics and unstarted-slot labels.
- Analysis bundle rebuilt successfully; git diff whitespace check passed.
- Restarted the local server through App Hub and inspected the live interface.
- Topic atlas: 472 library runs; 438 atlas-eligible runs; 11,204 messages scanned in that scope; 12 resolved initial-topic reviews. Consciousness phrase-match list: 204 matching runs with 12 on the first page; the population banner reports all 204.
- Coverage: 440 conversation runs and 32 technical checks; separate unstarted scope has 41 planned run slots and zero recorded messages. Coverage's text-present atlas scope remains 437, preserving its pre-existing nonempty-text rule rather than silently harmonizing it with Topic atlas's 438.
- Common Research units link opens the Lab dictionary.

## Preserved and next work

No inference, scientific recoding, source-text edits, notebook changes or new research snapshot. Frozen request wording, original titles, attributed research text and historical reports retain their original terminology. Validation errors and interface labels are presentation changes only.

The deeper audit of historical participant-message/event counters and eligibility remains a separate task. This session does not assert that all library runs are conversations, that every recorded position contains a message, or that stored runs are independent experimental replicates.
