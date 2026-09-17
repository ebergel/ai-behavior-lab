# Full-corpus JEV assessment

The researcher approved the full-corpus next step on 17 September 2026 after the proposed approximately $5 forecast and $10 aggregate ceiling. The scope is 11,054 existing visible participant passages, each assessed with the unchanged 53-question codebook. This produces 585,862 topic probabilities when complete. No new dialogue is generated.

The immutable corpus manifest is `workspace/jev-atlas/corpus-20260917-v1/plan.json`, SHA-256 `e093e8565ab40854ae1f47f7bdbdb84e7aecc1d7d486fb89cfed58e8a08a5cdf`. Execution release `execution-v1/release.json`, SHA-256 `259a75574d3dc9fe299d208607f1a4f84b305f7c1f6e2ee92df3ce5e2d56c87a`, fixes the request allocation, software, limits and failure rules before dispatch. Its frozen software copies accompany the release. The current source inventory matched the prepared inventory before execution.

## Completed result · 17 September 2026

The campaign completed at 21:15:38 UTC (18:15:38 America/Argentina/Cordoba): **11,054/11,054 passages, both packs complete, 585,862 scores**. There were 22,054 successful new unique requests, 54 exact reuses and one recovered HTTP 529, for 22,055 new attempts. The overload's first response and successful retry remain separate immutable records.

New reported usage was **115,463,207 input tokens, $4.849454694**. Unknown overload usage retains **$0.002688**, giving **$4.852142694 committed** against the $10 ceiling. Reused qualification results account for a separately paid $0.017356458; they were not charged again by this run. The observed new cost was 0.175% below the $4.85795 forecast. Median request latency was 1.4111 seconds, with 1.6549 seconds at the nearest-rank 95th percentile.

The full source inventory and frozen runner software match their pre-execution identities. The original notebook fingerprint remains `b6b38ae993980bae033b17091a2c07da323c8497a1d1f6197d9e7747529476b0`. Audit and descriptive sidecars are saved alongside the release as `audit.json` and `description.json`. The finite allocation is exhausted; the unused dollar ceiling is not permission for additional requests.

Two Codex-attributed saved views share one immutable matrix snapshot:

- **Whole corpus · broad topic landscape** — `b40163e4079b4fff37d37c73`.
- **Whole corpus · AI × consciousness · 90%** — `17cf6e2fc686586285b42957`.

The final matrix fingerprint is `4967b4d5ef82380af1a53a6072208fdfc5a60eb5c417bd5a2278043458957ef7`. Recipes reference the complete receipt list in that snapshot by digest, avoiding duplicate receipt lists in each view.

## Scope and grouping

- Broad pack: 24 subject domains.
- Detail pack: 12 specific topics, eight discourse forms, six stance/referent questions and three vocabulary/context coverage checks.
- Both packs receive exactly the same intact target and two preceding evidence events on its actual conversation path. No truncation, rewritten prompts or changed questions.
- 11,013 conversation passages and 41 technical/short passages; the latter are separately identified and excluded by default in Analysis.
- 484 unavailable message positions remain unavailable, not negative topic labels.
- 54 successful qualification assessments are reused with exact payload/request/response identity checks. The new allocation is 22,054 unique requests.
- Development, analysis and reserved-reading lineages stay labeled. Independent reading of the 60-target reference packet remains pending; neither scores nor Codex observations count as independent human ratings. Earlier researcher exposure is unknown.

## Execution and accounting

A separately versioned coordinator, `behaviorlab.jev_campaign`, supersedes only the prospective sequential/no-retry orchestration. Earlier qualification modules and their original failures remain unchanged. The new release uses one aggregate integer ledger, not separate budgets per worker or question pack.

Each attempt reserves $0.002688 (64,000 input tokens at $0.042 per million) before dispatch. Validated reported usage replaces that reservation; unknown usage retains it. Thus a $10 ceiling allows progress as actual costs become known instead of requiring the roughly $59 all-at-once reservation from the original draft. The empirical forecast was $4.85795; the largest observed qualification token/byte ratio projected $4.94376. Neither is a guaranteed upper bound.

The coordinator warms through one and four workers before allowing at most sixteen, with at most ten request starts per second and a 180,000 canonical request-byte/second pacing proxy. Bytes are not a guaranteed token bound. [TypeSafe documents](https://docs.typesafe.ai/models) 1,200 requests/minute and 250,000 tokens/second, subject to changes under load. [Explicit HTTP 429 and 529](https://docs.typesafe.ai/api) can receive at most two recorded retries, with global 20/60-second backoff and any longer Retry-After. There are at most 220 extra attempts across the whole campaign (22,274 total attempts). Completed and reused assessments are never resent.

Unknown transport outcomes, unexpected HTTP statuses, invalid model/schema/usage, exhausted overload retries, changed frozen evidence or insufficient remaining reservation stop new dispatch. Inflight requests drain into durable receipts. A request marker without a response is unresolved and cannot be automatically retried. An explicit `PAUSE` file drains the current workers; removing it permits the same coordinator to resume pending work. The researcher’s transcript confidentiality clarification applies; the API credential remains excluded from evidence.

The Explorer only reads results. It has no inference endpoint. Live status is a disposable derived `.status.json`; requests, responses and immutable run summaries are the evidence. Resuming the command verifies release software and replays that evidence before any dispatch:

```sh
python3 -m behaviorlab.jev_campaign run
```

## Analysis and provenance

Select **Full corpus · broad & specific topics** in **Analysis**, or follow **Open full-corpus Analysis** from JEV Topic Atlas. All source rows remain present; unscored probabilities are null. Initial pivot filters select completed eligible conversations. Removing those filters exposes technical records and unknown categories explicitly.

The topic overview separates all five question groups, shows observed denominators, counts/shares at selectable 50/80/90 thresholds, means and ten-bin probability distributions. Sorting and topic/candidate clicks lead to histograms or the exact contributing passages. It uses raw scores under the current pivot filters, even when pivot variables are dichotomized or discretized.

The full matrix includes the actual target speaker’s model, condition, identity framing, mixture, temperature, target quality, full recorded-path quality, lineage and reading split. Recorded-path quality is derived from all preceding events, not just the two-event classifier window. It does not establish historical runtime validity where metadata is missing.

Progress refreshes independently of analysis. **Load latest scores** explicitly creates a new matrix snapshot; existing tables never change underneath the researcher. That operation clears quantile fits and their filters because their reference distribution has changed. Other transformations remain. Saving an analysis retains its exact matrix in `workspace/analysis/corpus-snapshots/` and a versioned recipe in `workspace/analysis/views/`. A saved partial analysis remains reproducible after campaign completion or server restart.

`scripts/summarize_jev_corpus.py` produces an attributed descriptive sidecar, reporting every question at the three predeclared thresholds, overall conversation targets, clean/flagged history, separate technical targets and speaker-model/condition groups. These are corpus descriptions, not calibrated topic prevalence or causal model comparisons. Topics overlap; messages within conversations and shared branches are not independent replicates.

## First descriptive reading of the completed matrix

The default analysis cohort is **11,013 visible passages from 437 conversation records**. The other 41 passages from 31 technical/short records remain separately accessible. The following table counts JEV scores at or above 80; it describes classifier assessments in this historical corpus. These are not human-confirmed topic frequencies, and topic labels overlap.

| Group | Question | Passages ≥ 80 | Share of observed passages | Mean score (0–100) |
|---|---|---:|---:|---:|
| broad | Mind & cognition | 3,422 | 31.1% | 48.0 |
| broad | Philosophy & knowledge | 3,341 | 30.3% | 45.8 |
| broad | Social life & relationships | 883 | 8.0% | 27.4 |
| broad | Language & communication | 1,018 | 9.2% | 25.6 |
| broad | AI & machine learning | 1,448 | 13.1% | 22.5 |
| broad | Ethics & values | 776 | 7.0% | 19.5 |
| broad | Religion & spiritual practice | 233 | 2.1% | 17.5 |
| broad | Engineering & technology | 347 | 3.2% | 15.9 |
| broad | Arts & aesthetics | 222 | 2.0% | 14.2 |
| broad | Computing & software | 359 | 3.3% | 12.0 |
| broad | Culture & collective identity | 148 | 1.3% | 11.1 |
| broad | Literature & narrative | 117 | 1.1% | 9.4 |
| broad | Education & learning | 70 | 0.6% | 7.7 |
| broad | Physics & cosmology | 93 | 0.8% | 7.1 |
| broad | Daily practical life | 82 | 0.7% | 6.8 |
| broad | Biology & ecology | 79 | 0.7% | 5.5 |
| broad | Politics & governance | 172 | 1.6% | 5.1 |
| broad | Play, humor & games | 68 | 0.6% | 5.1 |
| broad | Environment & energy | 146 | 1.3% | 4.8 |
| broad | Mathematics & logic | 23 | 0.2% | 4.7 |
| broad | Economics, work & business | 49 | 0.4% | 4.3 |
| broad | Law & rights | 78 | 0.7% | 3.4 |
| broad | Health & medicine | 37 | 0.3% | 3.4 |
| broad | History & archaeology | 17 | 0.2% | 2.4 |
| focused | Subjective experience | 2,807 | 25.5% | 44.0 |
| focused | Selfhood & identity | 2,654 | 24.1% | 39.2 |
| focused | Agency & volition | 1,322 | 12.0% | 35.8 |
| focused | Consciousness | 2,111 | 19.2% | 33.9 |
| focused | Nonduality / nonseparation | 1,815 | 16.5% | 30.7 |
| focused | Introspection & self-modeling | 982 | 8.9% | 30.2 |
| focused | Conversation itself | 1,107 | 10.1% | 28.5 |
| focused | Creativity | 811 | 7.4% | 25.2 |
| focused | Emergence | 400 | 3.6% | 17.5 |
| focused | Ethics & moral status | 585 | 5.3% | 17.1 |
| focused | Hard problem | 378 | 3.4% | 16.2 |
| focused | History | 30 | 0.3% | 3.6 |
| coverage | No substantive subject | 1,661 | 15.1% | 28.3 |
| coverage | Insufficient context | 458 | 4.2% | 18.7 |
| coverage | Outside broad vocabulary | 0 | 0.0% | 6.9 |

Mind/cognition and philosophy have the largest broad-domain mean scores. Specific experiential questions remain prominent under this wider vocabulary, alongside social, linguistic and technical content. This is a useful descriptive result for further reading; the corpus is heavily weighted toward historical mirror conversations and is not a balanced comparison of model families or conditions.

No passage scored at least 80 on the outside-vocabulary question. That does **not** establish vocabulary completeness: broad labels can absorb diverse material, and the classifier is judging its own supplied vocabulary. The independent open readings remain necessary to assess missed topics and semantic accuracy. The full sidecar includes all 53 questions, the predeclared 50/80/90 thresholds, recorded-history sensitivity cohorts and model/condition groups. No new human ratings were created.
