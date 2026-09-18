# Session record · passage family means

Recording timestamp: 2026-09-18T17:59:30-03:00, America/Argentina/Cordoba.

Scope: add two sortable overall matching-pattern means per passage in Mind & discourse.

## Completed

- Thinkers mean averages the full 16 thinker/writer feature probabilities. Discourse mean averages the full 11 discourse-practice probabilities. Each uses the selected assessment wording with equal feature weights, displayed on the 0–100 percentage scale.
- Zero stays observed; missing/nonfinite scores are excluded. Coverage n/total accompanies observed means; fully unknown means remain dashes and sort last. Visible feature-family selection does not change the full-family calculation.
- Both summary columns appear in the profile matrix and passage comparison. Clickable headers toggle descending/ascending; the Sort passages menu supports both families in either direction. URL state, target/model/length filters, scroll and originating-control focus are preserved.
- Updated the feature guide and continuation record. Computation is local over existing probabilities; no new TypeSafe calls or cost.

## Verification

359 Python tests and 93 JavaScript tests passed. Regression checks cover separate families/wordings, observed zero, partial and all-missing scores, both sort directions, stable ties, full-family independence, URL/filter retention, and focus restoration. JavaScript syntax and git diff whitespace checks passed.

Live browser checks confirmed the two columns, matching header/body alignment, sorting both ways, and unchanged family means when only discourse columns are visible. An independent calculation over the three Consciousness ≥80 targets under Names + portraits matched the display: thinkers 29.3%, 25.8%, 15.1%; discourse 14.3%, 12.5%, 8.1% in that thinker ordering. Each had all 16 and 11 features observed.

## Interpretation and next work

These arithmetic means summarize matching across overlapping feature questions. They do not measure the probability of any match or passage quality. Their usefulness for discovering passages remains for researcher review. Frozen classifiers, assessment receipts, source transcripts, notebook rows and the research snapshot are unchanged. No new experiment or scheduled task was created.
