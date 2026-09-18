# Session record · target-topic filtering

Recording timestamp: 2026-09-18T17:48:14-03:00, America/Argentina/Cordoba.

Scope: the researcher clarified that a topic filter should restrict the passages being analysed in Mind & discourse and Analysis, rather than only organize the topic selector.

## Completed

- Added an explicit target-topic filter to both views: tier, topic, inclusive score threshold 50/80/90, and clear.
- Mind & discourse reuses existing corpus JEV scores through a read-only exact join on conversation/message ID, source SHA-256 and target text. Both source records must be current; missing, changed, duplicate or reserved targets do not receive scores. Synthetic controls remain separate.
- Overview statistics, passage comparison and profile matrix use the same filtered targets, combined with existing model, length and text filters. Filter state travels in the URL.
- Analysis filters original topic scores before transformations and pivot restrictions. Coverage, pivots, charts, passage drill-through and filtered export share the population. Existing transformations and fitted quantiles remain unchanged. Saved recipes retain the filter; unknown/stale topics remain explicit.
- Restarted the local server through App Hub to load the backend join. No inference calls or additional provider cost.
- Updated the two feature guides and continuation record.

## Verified observations

All 48 real Mind & discourse targets matched current corpus scores. Consciousness selects 8 at ≥50, 3 at ≥80 and 1 at ≥90. These are subsets of the existing 48-target classifier sample, not corpus frequency estimates. All 12 synthetic controls remain separate.

In full-corpus Analysis, Consciousness ≥80 matches 2,112 of 11,054 source rows; existing default pivot filters leave 2,111 passages. At ≥90, 1,455 remain. Clearing restores 11,013 passages after the existing pivot filters. Browser checks confirmed threshold changes, shared table denominators and restored URL state.

The complete Python suite passed 358 tests. A subsequently added saved-filter validation test passed with the focused eight-test Analysis suite. The JavaScript suites passed 90 tests, including inclusive boundaries, raw-score filtering before binary transformation, unknowns and stale filters. The local Analysis bundle was rebuilt.

## Boundaries and next work

No classifier definition, frozen runner, assessment receipt, transcript, notebook row or research snapshot was changed. This is browsing of existing assessments; semantic validation and classifier review remain future research work. Further classifier sampling requires its own finite design and allocation. No remote-access setup or recurring schedule was created.
