# Session record · Gem Finder word-count axis

Recorded: 2026-09-18T13:29:45-03:00
Timezone: America/Argentina/Cordoba (UTC−03:00)
Scope: add passage length as an axis for exploring possible length effects in Gem ratings.

## Completed

- Added **Word count** as the eighth Gem Finder axis: 56 ordered scatterplots and eight diagonal histograms. The six frozen JEV questions and profile-distance measure are unchanged.
- Focused plots accept words on either axis and show Pearson r/n. Counts use their own range, never a 0–100 quality scale or clipping at 100.
- Added **Explore length & scores**, shortest/longest ordering, inclusive minimum/maximum word filters, and length-histogram selection. Saved bin width and original axis preserve the exact interval when other filters or pairs change. Values outside a retained histogram range are reported explicitly.
- Expanded the Lab Dictionary to 18 terms. Word count documents the exact whitespace-count rule, visible-target scope, distinction from tokenizer tokens, language limitations and interpretation of possible confounding. The explanatory guide is version dictionary-2026-09-18-v2; scoring rubrics stay frozen.
- Updated the user guide and continuation notes.

## Verified results

- Full tests: 313 Python + 66 JavaScript = **379 passing**. Tests cover raw counts above 100, word-scale geometry on either axis, zero/missing/stale values, sorting, inclusive limits, bins at boundaries, and preserving a word interval when another matrix pair is opened.
- Live browser: eight diagonal cells, 56 paired cells, all seven word-versus-measure associations present, natural 0–600 word range, working length filters and Dictionary links.
- Pilot metadata: 100 passages, 1–599 words, mean 105.55. Word count already exists in frozen target records as len(target_text.split()); no new assessment is needed.
- Live matrix reproduced the existing descriptive length correlations: surprise 0.04, contribution 0.69, connection 0.67, expression 0.58, complexity 0.74, substance 0.71, profile distance 0.57 (rounded Pearson r, n=100).
- Exploratory UI check: maximum 80 words retained 55 passages; word count versus expressive force displayed r=0.57 for that selected subset. The 0–60 word bin, upper bound excluded, retained 51 passages and kept its width of 60 words. These are interface checks and post-hoc descriptions, not new confirmatory analyses.
- Frozen scoring software still matches its saved pilot hashes. GitHub repository visibility verified PRIVATE.

## Evidence and interpretation boundary

No model calls, extra spending, transcript changes, notebook writes, task revisions or research snapshot changes. Token counts were not estimated. Word count measures the target reply alone, excluding context, prompts and separately recorded reasoning.

Longer passages can develop more relationships, an assessor can favor elaboration, and model/topic composition can affect both. Correlation alone does not identify a causal confounder or prove verbosity bias. No scores were divided by words, residualized or otherwise adjusted.

## Next phase

Collect the researcher’s brief, valuable examples and compare judgments within similar length ranges and model configurations before revising or extending the rubric. Any new scoring requires its own frozen version and finite authorization.
