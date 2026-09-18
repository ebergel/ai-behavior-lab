# Lab summary

**Goals, Ideas & Task** is the first workspace section. Its fourth tab, **Lab summary**, sits next to Ideas & tasks and opens at `#view=purpose&section=summary`.

The page separates two kinds of experiments:

- **Data-generation experiments:** one row per indexed source directory and collection. Historical imports are split by stage; separate campaign directories stay separate, even if their final folder names match. Each row exposes its models, conditions, started runs, unstarted slots, messages, share of all messages and share within its real/synthetic data type. Open the experiment to browse its exact runs. Type/search filters and numeric column sorting change the displayed rows, not the percentage denominators.
- **Analysis experiments:** the full-corpus JEV campaign, all registered JEV batches, Gem pilot/expansions and the three registered Mind classifier protocols. Rows distinguish completed versus sampled real messages, synthetic control texts, source-current real-corpus coverage, question counts and wordings/packs. Columns are sortable. Available viewers open the exact batch; historical Mind plans without a dedicated viewer remain labeled by their exact source path.

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
- Four additional diagnostic probe batches are listed separately. Their jobs do not become new conversation messages.

This tab does not change any earlier library counters or eligibility rules. It makes its own explicit counting contract inspectable alongside the previous totals. It adds no notebook writes, new scientific labels, planned execution or inference authorization.

The summary uses the available content width for its tables. Current focus is collapsible on this tab; the purpose, journal and board retain their existing focus strip.
