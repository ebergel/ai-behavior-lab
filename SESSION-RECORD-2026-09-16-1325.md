# Session record — Conversation Finder

Timestamp: 2026-09-16T13:25:51.538788-03:00
Scope: user-approved setup-tag navigation, model visibility and separate external-intervention roles. Standalone laboratory repository; earlier reference repository untouched.

## Completed

- Added Conversation Finder with tag facets, role-aware exact model/developer/weight filters, any/all/every controls, cohort selection, search, sorting, counts, pagination, removable filters and named saved views.
- Added a reviewed model alias/family catalogue and derived `experiment-facets/1` metadata. Prompt identity disclosure is separate from actual model composition. Missing history/identity remains unknown; transcript claims do not set setup tags.
- Added consistent colored badges across views and a reader roster with opener, per-speaker thinking setting and full identity inspection. External events retain their own source model, style, insertion turns, exact text and transcript links; they never become ordinary third participants.
- Saved views use new SQLite tables with authorship, revision conflict checks, history and export. The browser persistence check used an isolated database copy, not the personal notebook.
- Fixed a rapid-selection race found during browser testing so pending model tags survive a subsequent match-rule change.
- Added documentation in `docs/CONVERSATION-FINDER.md`, updated the continuation guide and Explorer guide, and saved screenshots/validation under `docs/evidence/`.

## Verified

184 Python tests and 10 JavaScript tests pass. Browser checks verify combined Gemma/Haiku filters, distinct model badges in messages, intervention jump to `m-line-6`, return to the same Finder selection, saved-view creation/update/recall/full reload, and model visibility in collection cards and Topic atlas. The browser error log is empty.

Inventory checks: 472 default records; Google among regular participants 55, external interventions 40, anywhere 95; exact Gemma/Haiku contains-all 2; all-closed regular models 18 versus any closed model 20. All 40 external-intervention records retain two ordinary participants. No regular trios exist in this inventory. The metadata layer's trio support does not enable or qualify a new runner.

Preservation: 111 prior evidence files and 32 frozen mixed-pilot dependencies verify unchanged. All ten earlier SQLite tables compare exactly with `workspace/finder-20260916-1307/notes-before.sqlite`: five notes, five collections, 28 flags, 22 dictionary entries, four opening reviews and all histories. The main database has no test saved views. Pilot journal remains `3c7da636c58d0626a32ba6fa4770578dee4d73c522e92fe962a0cd759c8c8f90`.

Evidence directory: `workspace/finder-20260916-1307/`. Validation: `docs/evidence/conversation-finder-validation.json`. The temporary test server was stopped; the updated Explorer remains on port 8765. No inference, downloads, spending, semantic ratings or automation occurred.

## Next phase

Use the Finder to choose a manageable reading cohort, then review initial topics and trajectories in the existing collection/Topic atlas workflow. Keep inventory counts distinct from prevalence estimates. Repeated mixed pairings, matched-prefix interventions and trios remain separate future experimental freezes. Saved views are dynamic filter recipes, not immutable scientific cohorts.
