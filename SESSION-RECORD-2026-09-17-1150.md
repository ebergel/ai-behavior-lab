# Session record: JEV probability exploration

Recorded: 2026-09-17T11:50:19.739640-03:00 — America/Argentina/Cordoba.
Scope: Add lowest-probability sorting and an interactive probability distribution to JEV Topic Atlas.

## Completed

- Added **Lowest JEV probability**, keeping missing/failed assessments last in either direction and retaining sample order for tied scores.
- Added a ten-bin histogram of the selected topic across the entire scored batch, with counts, mean and median. Missing assessments are excluded rather than treated as zero.
- Clicking a bin opens its exact probability range, clearing queue/search and retaining sorting. The selection survives URLs and source/return navigation. Changing topic, batch or queue clears it.
- Hide judgments hides the chart/statistics and clears probability-driven navigation. Bars have accessible labels, selected-state indication and keyboard support; the chart scrolls inside narrow layouts.
- Updated the guide, continuation notes and validation evidence. No inference or research-data edits occurred.

## Verified

222 Python tests and 21 JavaScript tests passed. Targeted cases cover zero/one endpoints, bin edges, unassessed targets, empty distributions, stable ordering, bookmark persistence and hidden-judgment filters.

Live Emergence histogram counts: 102, 45, 11, 11, 6, 5, 4, 7, 5, 4. Mean 18.84%, median 9%. Its first bin opens 102 passages, beginning at 1% with ascending sort. The uncertain queue begins at 21%. Browser checks verified source-return selection and hidden-judgment behavior, and caught/fixed a global button layout style affecting bars.

All 403 original JEV request/response/plan/integration files checked remain byte-identical to the private research snapshot. Frozen inference software and the original notebook remain unchanged. The live batch contains nine reviews, including researcher additions; this UI-only session neither edits those reviews nor refreshes the research snapshot.

## Remaining

Probability values are model judgments, not validated accuracy. Independent human coding/calibration remains pending. No new experiment or scheduled continuation was started.

See [distribution guide](docs/JEV-TOPIC-ATLAS.md#exploring-the-probability-distribution) and [verification evidence](docs/evidence/jev-probability-distribution-validation.json).
