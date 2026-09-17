# Replication precision planning

17 September 2026 · planning sensitivity, not a frozen sample size or power analysis.

The original twenty fresh roots per cell is useful for a pilot, but it may be too small for precise **within-model differences between disclosure conditions**. Count fresh conversations as units. Eighteen replies from one conversation do not supply eighteen independent replicates.

The [reproducible calculation](../scripts/replication_precision.py) reads the saved matrix without transcript text. It excludes all 60 reserved validation conversations, uses same-model open-ended records with six complete, clean-recorded opening positions, and calculates one first-six mean per conversation for each proposed outcome. Exact transcript-structure duplicates would count once. This does not establish historical independence or common experimental conditions. The [full output](evidence/replication-precision-20260917.json) retains denominators, exclusions and matrix fingerprint.

| Historical configuration | Eligible records | Mind/cognition SD | Philosophy/knowledge SD |
|---|---:|---:|---:|
| Qwen3 Instruct | 108 | 13.53 | 16.19 |
| Gemma 4 26B | 42 | 22.13 | 15.04 |
| OLMo raw instruct alias | 37 | 22.85 | 18.18 |
| Haiku | 5 | 30.02 | 31.25 |
| GPT-4o mini | 2 | 26.99 | 28.64 |
| Nemotron | 2 | 35.71 | 31.47 |

These SDs mix historical conditions and can include between-condition variation. They are not estimates of a shared residual variance under the new protocol. The tiny hosted samples are especially unstable, and OLMo's newly proposed chat route is different from its historical raw alias. Use the table to explore plausible variance scenarios, not to select favourable outcomes or claim validated precision.

For illustration, a single approximate 95% confidence interval with planning SD 25 points gives:

| Desired interval half-width | Roots for one condition's mean | Roots **per condition** for a two-condition difference |
|---|---:|---:|
| ±10 score points | 25 | 49 |
| ±5 score points | 97 | 193 |

With SD 35, the ±10-point difference calculation becomes **95 roots per condition**. At n=20 and SD 25, the approximate half-width for a difference is **15.5 points**. These are normal-approximation sensitivity calculations, not power calculations; they hold SD fixed and omit small-sample, multiplicity, attrition and dependence adjustments. A confirmatory plan with two outcomes, two contrasts and six models requires an explicit multiplicity strategy. Its final allocation may need to be larger.

The formulas are `ceil((1.96 × SD / h)²)` for a mean and `ceil(2 × (1.96 × SD / h)²)` per cell for an independent equal-sized two-cell difference. They describe score means, not calibrated topic prevalence. Missing opening positions remain unknown and require the proposed availability/bounds analysis; increasing n alone cannot remove informative technical failure.

My planning recommendation is to choose the precision target for **disclosure contrasts** first, then use a conservative variance scenario and the chosen simultaneous-inference method. Keep twenty roots labelled as a pilot option. If the aim is roughly ±10 points for an individual difference, 50–100 roots per cell is the scale suggested by these scenarios **before multiplicity adjustment**. This is a planning range, not an allocation or authorization to collect 900–1,800 conversations.

No sample size, new inference budget, randomization schedule or stopping boundary was frozen in this milestone. The researcher can review the topic trajectories while we prepare the finite technical qualification and independent scoring validation.
