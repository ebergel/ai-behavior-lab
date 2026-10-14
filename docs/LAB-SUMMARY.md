# Lab summary

**Goals, Ideas & Task** is the first workspace section. Its fourth tab, **Lab summary**, sits next to Ideas & tasks and opens at `#view=purpose&section=summary`.

The page separates data generation from analysis:

- **Data-generation experiments:** one row per indexed source directory and collection. Historical imports are split by stage; separate campaign directories stay separate, even if their final folder names match. Each row exposes its models, conditions, started runs, unstarted slots, messages, share of all messages and share within its real/synthetic data type. Open the experiment to browse its exact runs. Type/search filters and numeric column sorting change the displayed rows, not the percentage denominators.
- **Analysis experiments:** the original Topic atlas reading instrument, followed by the full-corpus JEV campaign, all registered JEV batches, Gem pilot/expansions and the three registered Mind classifier protocols. Assessment rows distinguish completed versus sampled real messages, synthetic control texts, source-current real-corpus coverage, question counts and wordings/packs. Assessment columns are sortable; the Topic atlas row stays first. Available viewers open the exact batch; historical Mind plans without a dedicated viewer remain labeled by their exact source path.

## Topic atlas in the analysis table

The original **Topic atlas · dictionary matching & opening reviews** has its own row, separate from JEV Topic Atlas assessment batches. Its reading-cohort selector offers all atlas-eligible runs and saved research collections. It initially follows the atlas cohort already selected in this browser session, otherwise the latest saved collection, otherwise all eligible runs. The selector changes only the atlas row; the other analysis batches and headline coverage keep their full scopes. The row links to the original Topic atlas with the same cohort. Counts include all participant models within that cohort.

The row displays messages in literal-scan scope, source runs, current reviewed opening outcomes, and versioned topic definitions. An eligible run has at least six participant positions and some recorded text; synthetic fixtures and unstarted slots are excluded. Message counting reuses the atlas participant-message identity rules and counts recorded strings, including empty strings. Reading the summary calculates these counts without rerunning the phrase scan.

Reviewed outcomes are attributed run-level readings, including a reviewed no-selection outcome. A review must match both the current source and referenced dictionary revisions. Unreviewed runs, stale reviews and unavailable openings appear separately. Literal scan scope does not imply semantic assessment, and opening reviews are not assessments of every message in a run. These metrics therefore show **Not comparable / Excluded from assessment coverage**, and never enter the assessed-message union. Atlas read failures remain visible as **Unavailable**, with unknown counts.

Both summary API routes include the atlas counts for every available cohort. Export is a full summary, independent of which cohort is selected on screen. Opening the summary or changing its selector does not modify research collections, topic definitions, opening reviews or their histories.

## Counting contract

The summary counts unique `(run ID, message ID)` participant messages with a recorded string. It includes X, Y and Z, empty strings and whitespace-only strings; it excludes missing outputs and external interventions. Shared branch nodes count once within a run. Synthetic engineering fixtures remain separate from model-output evidence. **Real** means recorded model output; it does not mean human authorship, verified scientific validity, or a particular experimental qualification.

Generation proportions divide by all recorded messages, or by all messages within the row's data type. Synthetic classifier controls are separate authored test texts and are not added to the conversation corpus. Technical runs and unstarted slots retain their own classifications.

Assessment coverage requires all planned question packs or wording conditions for a message to be complete. It also requires an exact current source hash and text match. The denominator is all real recorded messages. Duplicate sample occurrences, scores, retries and wordings do not add messages. The headline coverage counts a union across readable assessment batches; row percentages overlap and must not be added. Unavailable or unverifiable sources display **Unavailable / —**, not zero. Changed/missing sources can retain a historical completion count while contributing nothing to current coverage.

The endpoint reuses the existing receipt validators and never dispatches inference. `/api/lab-summary` and `/api/lab-summary/export` are read-only and retain the local-origin boundary. The payload is an inventory of counts and source identities, not transcript text or API credentials. Corpus receipt verification can take around twenty seconds on a cold load; the page shows a loading state and other workspace tabs remain usable. **Reload summary** rechecks current assessment receipts; **Refresh evidence** first reindexes newly added source experiments.

## Verified local inventory · 18 September 2026

- 41 source experiments; 532 started runs: 440 conversation runs, 32 technical runs and 60 synthetic fixture runs. A further 41 unstarted slots remain visible.
- 15,757 recorded participant messages: 11,245 real (71.4%) and 4,512 synthetic fixtures (28.6%).
- Real messages include 191 empty strings and one nonempty whitespace-only string. The JEV full-corpus sample has 11,054 nonempty strings, including that whitespace-only message. Its coverage is 98.3% of all recorded real messages and 100% of its frozen eligible sample.
- 13 registered assessment batches, including earlier unassessed/partial protocols. The current Mind portrait experiment has 48 real messages and 12 synthetic control texts: 80% / 20% of that sample. Four wordings do not turn those 60 texts into 240 texts.
- Original Topic atlas: 438 eligible runs and 11,204 messages in scan scope, with 23 topic definitions and 12 current opening reviews. The Opening & partner cohort contains 12 runs / 168 messages, with 12 of 12 opening outcomes reviewed. These existing reviews are attributed to Codex. The other 426 eligible runs remain unreviewed; scans do not add assessed messages.
- Four additional diagnostic probe batches are listed separately. Their jobs do not become new conversation messages.

This tab does not change any earlier library counters or eligibility rules. It makes its own explicit counting contract inspectable alongside the previous totals. It adds no notebook writes, new scientific labels, planned execution or inference authorization.

The summary uses the available content width for its tables. Current focus is collapsible on this tab; the purpose, journal and board retain their existing focus strip.
