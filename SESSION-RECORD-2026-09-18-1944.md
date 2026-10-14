# Session record · Topic atlas in Lab summary

Timestamp: 2026-09-18T19:44:32.843917-03:00 · America/Argentina/Cordoba.

Scope: implement the user's accepted correction after screenshots showed the original Topic atlas missing from the Lab summary analysis table. This is the Behavior Laboratory UI task.

## Completed

- Added an original Topic atlas reading-instrument row before the 13 assessment batches, with cohort selection and a direct link to the same cohort in the atlas.
- Kept source runs, messages in scan scope, current reviewed opening outcomes and dictionary definitions distinct from message assessments. Unreviewed, stale and unavailable openings remain separate.
- Reused atlas eligibility, participant-message identity and current review checks. The summary calculates scope counts without running a phrase scan or inference. Both summary API routes expose all cohorts; the UI selector affects only the atlas row.
- Preserved existing assessed-message coverage and all research evidence. The atlas row remains first during assessment sorting. Its wrapped title has a continuous clickable area.
- Updated the counting guide and continuation notes; restarted only the existing Behavior Laboratory service through appHub.

## Verified

- Full Python suite: **370 passed**, 0 failed (36.384 seconds).
- Full JavaScript suite: **111 passed**, 0 failed.
- Live all-atlas scope: **438 runs / 11,204 recorded messages**, 12 current opening reviews, 426 unreviewed runs, 23 definitions.
- Opening & partner cohort: **12 runs / 168 messages / 12 reviewed opening outcomes**. Reviews retain their Codex attribution.
- Assessment union remains **11,054 / 11,245 real messages = 98.30146731880836%**, shown as 98.3%. The table has 14 rows: one reading instrument and 13 assessment batches.
- Browser checks: cohort switching, sorting with the atlas row fixed first, unchanged headline metrics, direct link to the original atlas with the selected cohort and Any model, and visual inspection at 1280 × 720.
- All rows in all **18 notebook tables**, including definition and opening-review histories, exactly match the pre-change snapshot. Logical snapshot SHA256: `a9ceef2a55081fc9057abd95bf4f1444d8ed7778aec044c58821628a4f4eb978`.
- Evidence: [validation JSON](docs/evidence/topic-atlas-summary-validation.json) and [rendered summary](docs/evidence/topic-atlas-summary.png). Full test logs remain under `/private/tmp/lab-atlas-summary-20260918/`.

## Pending and next

The requested summary correction is complete. Refresh an already-open laboratory browser tab to load the updated code. No additional inference or opening reviews were performed. The 426 unreviewed eligible runs remain future scientific reading work; this display change does not authorize or claim those reviews. No new automation, commit or push was created in this task.
