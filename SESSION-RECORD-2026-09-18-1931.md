# Session record · Laboratory summary

Recorded: 2026-09-18 19:31:01 -03:00, America/Argentina/Cordoba.

Scope: rename the first workspace section to **Goals, Ideas & Task** and add a summary of generation experiments, assessment experiments, real/synthetic composition and message coverage beside Ideas & tasks.

## Completed

- Added the **Lab summary** tab at `#view=purpose&section=summary`, with four headline counts, real/synthetic message proportions, sortable assessment and generation tables, a data-type filter and experiment search.
- Generation rows open their source runs. Readers opened from the summary offer **Back to Lab summary**. Available assessment viewers link to the relevant results. Counts and source metadata can be exported.
- Added a read-only summary service using the existing catalog and receipt validators. Count unique recorded participant messages, retain empty strings, exclude missing outputs and external events, and keep synthetic classifier controls separate from synthetic conversation fixtures.
- Assessment coverage requires complete planned packs/wordings and matching current source hash and text. Overlapping batches contribute a deduplicated union. Unassessed, partial, changed-source and unavailable states remain distinguishable.
- Summary loading does not block navigation to the other planning tabs. Current focus is collapsed on this tab to expose the inventory immediately. Existing planning data and source evidence remain unchanged.
- Updated laboratory and continuation documentation. No inference requests, new research labels or notebook writes were made.

## Verified inventory

- 41 source experiment groups; 532 started runs: 440 conversation runs, 32 technical runs and 60 synthetic fixture runs. Another 41 unstarted slots remain visible.
- 15,757 recorded participant messages: 11,245 real model messages (71.4%) and 4,512 synthetic fixture messages (28.6%).
- 13 registered assessment batches, including earlier unassessed and partial plans. Unique current-message coverage is 11,054 / 11,245 = 98.3%.
- The real corpus includes 191 empty strings and one nonempty whitespace-only string. Full-corpus JEV completed its 11,054-message frozen nonempty sample; the whitespace-only string is included there.
- Mind & discourse portraits contain 48 real messages and 12 synthetic controls: 80% / 20% of sample texts. Four assessment wordings do not multiply the number of texts.
- Four additional diagnostic probe batches are listed separately from generated conversations.

## Verification

- Python suite: 368 tests passed.
- JavaScript suite: 109 tests passed.
- `git diff --check` passed.
- Live browser checks covered the summary, real/synthetic filtering, assessment sorting, experiment/run navigation and the final dashboard layout. The App Hub restart returned RUNNING and the final page displayed current validated totals.
- Evidence receipt validation takes roughly eighteen seconds on the current corpus; the page displays a loading state and caches its result until reloaded. This is read-only validation, not inference.

## Future work and boundaries

The summary describes the current indexed inventory and registered assessment protocols. It does not establish representative sampling, independent message observations or classifier validity. Further experimental generation and validation retain their existing design requirements. No additional research run or scheduled task was started.

Implementation details and counting contract: `docs/LAB-SUMMARY.md`.
