# Session record — population context

Recorded: 2026-09-18T18:19:04.065044-03:00 · America/Argentina/Cordoba (UTC−03:00).
Scope: distinguish the laboratory inventory, each view's assessment sample, and its current filtered subset.

## Completed

- Added read-only catalog population metadata with separate reference/laboratory, synthetic fixture, and unstarted-slot counts. Missing message totals remain unknown.
- Added a common three-stage banner to the Library (also Run atlas and Results), Mind & discourse, Gem Finder, JEV Topic Atlas and Analysis. Active population filters, named datasets, explicit units and source record counts are visible.
- Mind & discourse separates its 48 real targets from 12 synthetic controls. Request totals and cost remain available under Assessment details.
- Gem banners follow selected samples and actual filters including bin/hidden-mode behavior. JEV banners count full queues before pagination and explicitly distinguish full-batch overview/distributions. Analysis applies topic plus pivot restrictions and reports close-reading selections separately.
- Documented semantics in docs/POPULATION-CONTEXT.md and updated continuation notes.
- Used the existing bounded Luna workers for Analysis and Gem/JEV UI work, followed by root review, direct template integration, corrections and additional tests.

## Verified

- Python suite: 362 tests passed. JavaScript suite: 98 tests passed. Updated shared population tests and API contract checks cover true zero versus unknown, separate synthetic populations, sample/filter intersections, bin bypass and pre-pagination counts.
- Rebuilt the local Analysis bundle; syntax checks and git diff checks passed. App Hub restarted the lab server.
- Live library: 472 records, 11,245 recorded participant messages, 60 separate synthetic fixture records, 41 unstarted assessment slots excluded.
- Mind & discourse: Consciousness ≥80 gives 3/48; ≥90 gives 1/48. Switching to controls gives 12/12 independently of the stored topic filter.
- Analysis: 11,054 targets from 468 source records; default pivot exclusions give 11,013 from 437; Consciousness ≥80 plus default exclusions gives 2,111 from 272.
- Gem Finder: combined 1,000 targets / 376 source records; original pilot 100 targets; Claude Haiku filter selects 7/100.
- JEV detailed recovery batch: 27 targets / 17 records; Consciousness candidates select 9 targets / 5 records. Counts reflect the whole queue rather than 12-row pages.

## Boundaries and next work

No live inference, source transcript, frozen classifier, assessment receipt, research snapshot or notebook content was changed. Counts describe records and passages, not independent replicates or behavioral prevalence. Dataset target counts can overlap and must not be added together. Scientific review of classifier distinctions remains pending; this session adds navigation context, not new findings or experimental authorization.
