# Session record — Gem Finder expansion

Recorded: 2026-09-18T13:56:26.778480-03:00 · America/Argentina/Cordoba.
Scope: the researcher's request to expand the Gem pilot after adding length as an exploratory axis. This is a new session record; previous records remain intact.

## Completed and verified

- Froze a separate 900-target model × length expansion and a new finite $2 ceiling before inference. Original 100 targets, six Score questions, frozen software and 8,371-passage profile reference remain unchanged. Plan SHA-256: bdb2cad32d6cf7045ee8d2baf9abaa6d7a84288a361e12bb02f031b118239efb.
- All 900 assessments completed in exactly 900 calls, with 5,400 new ratings, $0.081287682 reported usage cost, no failures/retries and no unknown-cost reservations. Three initial requests checked the response shape; 897 completed the same allocation. Combined total: 1,000 assessed replies, 6,000 ratings, $0.090679344.
- Selected 900 fresh targets from 7,895 candidates across 14 model variants and 375 lineages. Combined coverage is 376 lineages, capped at three targets per lineage including the pilot. All 60 reserved validation lineages are excluded. Availability limits model/length balance; this is neither a prevalence sample nor 1,000 independent conversation replicates.
- Added Original pilot / Model × length expansion / Combined sample selection throughout Gem Finder, with source sample labels, per-plan reading provenance and both samples in exports. The web app dispatches no inference.
- Actual browser verified 100, 900 and 1,000 rows in the respective views; the combined matrix renders eight diagonal distributions, 56 pair plots and 56,000 points. Length filters and enlarged paired plots work. Existing notes and readings were not edited.
- Saved reproducible descriptive-analysis.json and a separate quality-audit.json. Fresh-sample length correlations: complexity 0.694, contribution 0.602, substance 0.625, expression 0.487, connection 0.548, surprise 0.062. Eighteen fresh replies of at most 50 words score ≥80 for expression; these are model-selected reading candidates, not researcher-validated gems.
- Found one newline-only historical Gemma target (c13a0ef1cc08165b1c81aedc, zero words), included by the frozen selector. Preserved its record, score and cost; no replacement call. Explicit UI label and minimum-words filter expose the case. Separate n=899 nonempty sensitivity leaves correlations essentially unchanged. The frozen first band named 1–25 actually contains 251 nonempty replies and this empty record; documented without rewriting the freeze.
- Validation: 324 Python tests and 68 JavaScript tests passed across the full suite and focused final checks; JavaScript syntax and git whitespace checks passed. The final descriptive-correlation optimization passed its focused test. No human ratings were fabricated.
- Research bundle export performed credential exclusion checks, hash verification and full restoration/reindexing into a separate temporary workspace. New bundle: 48,313 files, 972,744,545 bytes; SHA-256 7590c7a604596e704376862b622651d4a134c3abbd047fb97944e3a79188fea8. All 46,501 prior snapshot files remain byte-identical, including all 18 notebook tables; 1,812 evidence files added. The live workspace was never restored over.
- GitHub target verified private: ebergel/ai-behavior-lab. The verified snapshot is copied into research/. The commit and push follow this record's creation; their outcome is reported in the task response.

## Interpretation and next phase

The larger sample reinforces the need to investigate length-related scoring, without establishing whether length, model, topic or assessor behavior causes the association. Very long replies are mostly OLMo Think; compare within models and word ranges. Original and expansion results have different sample compositions and remain separately selectable.

Collect researcher examples of short insights, detailed high-score passages, ordinary cases and unsupported claims before changing the rubric. Future sampling releases should explicitly decide how to handle empty outputs. Preserve all evidence, the two reports and both frozen plans. This new finite allocation is exhausted; unused ceiling does not authorize further inference. No new model dialogues, reserved-set review, public release, remote-access installation or scheduled continuation occurred.

Implementation and detailed results: docs/GEM-EXPANSION.md. Earlier session records retain their historical scope.
