# Gem Finder: model × length expansion

The researcher requested more Gem data on 18 September 2026 after adding word count to the matrix. This milestone assesses **900 fresh passages**, bringing the development set to **1,000**, with the six original Score questions and topic-profile distance reference unchanged. It generates no new participant dialogues.

## Sampling and scope

The frozen original reference contains 8,371 eligible passages across 376 lineages. Removing the original 100 targets and targets without preceding context leaves **7,895 fresh candidates**. The expansion uses a seeded round robin through model × word-length cells, reaching previously unselected lineages before allowing a second or third target. The combined sample is capped at **three targets per lineage**. No topic rating, Gem score or human judgment is used to choose targets.

The 900 additions span **375 lineages and 14 model variants**; together with the original sample they cover **376 lineages**. Repeated passages from a conversation share history and are not independent replicates. All 60 reserved validation lineages remain excluded from targets, context and profile reference.

| Words in target | Fresh passages |
|---|---:|
| 0–25 (see quality note below) | 252 |
| 26–75 | 249 |
| 76–150 | 234 |
| 151–300 | 147 |
| 301+ | 18 |

Availability constrains balance. Qwen3 Instruct contributes 289 additions; Gemma 116. GPT-4o, mini and Nemotron each contribute four because their historical lineage counts are small. Sixteen of the 18 passages over 300 words are from OLMo Think. This is a measurement-development sample, not a representative corpus sample or a balanced model experiment. Mean differences between samples can reflect the changed composition.

## Immutable allocation

Plan: `workspace/gem-finder/expansion-20260918-v1/plan.json`.

SHA-256: `bdb2cad32d6cf7045ee8d2baf9abaa6d7a84288a361e12bb02f031b118239efb`.

The new finite allocation contains 900 unique requests, six questions per request, a separate **$2 ceiling**, and up to 27 extra attempts only for explicit HTTP 429/529, at most three attempts per target. The assistant communicated the sample size and ceiling before dispatch under the researcher's request to expand. No earlier budget was reopened. The first three calls check the response format, then the same allocation resumes.

`gem_expansion.py` and its dependencies are copied and hashed before dispatch. The original `gem_plan.py`, `gem_runner.py` and `gem_rubric.json` stay unchanged. Concurrency is bounded at four with a 0.25-second minimum dispatch interval. Every request is durable before dispatch; spending includes reservations for in-flight and unknown-usage attempts. Other errors or invalid responses stop new dispatch while active requests drain. Completed resume makes no calls. Explorer remains a reader and notebook, never an inference launcher.

The target and preceding context are sent intact using the original payload builder. The original reference's 24 broad-domain score vectors are reused for profile distance; the original 100 targets are not rescored. All requests and raw responses are retained.

## Exploring the samples

The **Assessment sample** selector in Gem Finder provides:

- **Combined:** original pilot plus new assessments.
- **Original pilot:** the preserved 100-passage sample.
- **Model × length expansion:** the 900 fresh targets.

All eight matrix axes, paired plots, distributions, sorting, model filters and word limits work within the selected sample. Passage rows identify their sample. Pending scores stay unknown. Saved readings retain source identity, authorship and history; new readings record their own assessment plan. Export includes both plans and raw receipts, alongside readings and their revisions.

A useful first exploration is a fixed word range within one model, followed by a change of the plotted quality axis. This reduces obvious composition differences but does not establish a causal effect of verbosity. Scores remain unadjusted; no score-per-word ratio or automatic definition of a gem is introduced.

## Reproducible descriptive analysis

After completion, `python3 -m behaviorlab.gem_expansion_report` writes an immutable `descriptive-analysis.json` inside the expansion directory. It reports original, fresh and combined summaries, word–score correlations, fresh within-model and within-length summaries, and source-linked short candidates (at most 50 words and a score of at least 80). Those candidate lists are an aid to reading, not human-validated gems. The report refuses incomplete samples and refuses overwriting its prior output.

Researcher examples, assessment validity and eventual rubric revisions remain separate next steps. This expansion does not qualify the balanced factorial generation design or authorize further inference after its finite allocation is exhausted.

## Completed results

**900/900 assessments, 5,400 new ratings, exactly 900 calls, $0.081287682 reported usage cost.** No failures, retries or unknown-cost reservations. Combined with the original pilot: **1,000 assessments, 6,000 ratings, $0.090679344**. Both finite call allocations are exhausted; unused ceilings do not authorize further inference.

| Fresh-sample axis | Mean score | Score ≥80 | Pearson r with words |
|---|---:|---:|---:|
| Surprise | 15.29 | 4/900 | 0.062 |
| Contribution | 51.14 | 172/900 | 0.602 |
| Connection | 61.35 | 351/900 | 0.548 |
| Expression | 57.59 | 345/900 | 0.487 |
| Complexity | 53.77 | 119/900 | 0.694 |
| Substance | 42.55 | 113/900 | 0.625 |

The length association persists in the larger sample, especially for complexity; surprise remains comparatively unrelated to length. This supports investigating the measurement concern, not a conclusion that the assessor causes it. Among the fresh replies of at most 50 words, 18 score at least 80 for expression, three for contribution, and none for complexity. These overlapping sets are candidates for the researcher's own reading, not validated gems.

### Quality note: one empty historical reply

Target `c13a0ef1cc08165b1c81aedc` is a recorded Gemma reply containing only a newline. The existing broad-topic reference included it, and the frozen expansion selector did not exclude whitespace-only replies. Consequently, its zero-word count fell into the first band despite that band's frozen name “1–25”. That band contains 251 nonempty replies plus this one empty record. The plan, original record, cost and response remain intact; no replacement call was made.

The UI explicitly labels the empty reply and lets readers exclude it with minimum words = 1. `quality-audit.json` records the finding and a separate nonempty-only sensitivity analysis (n=899). Length correlations remain essentially unchanged: complexity 0.694, contribution 0.601, surprise 0.063. The primary descriptive report retains all 900 assessed records. Future sampling releases should explicitly define eligibility for empty outputs before freezing.

### Verification

Automated tests cover lineage-capped selection, both batch identities, incompatible/duplicate-source rejection, pending scores, attribution to the correct plan, concurrent finite execution, durable interruption handling, reservation-preserving overload retries, sample-aware browser loading and empty-reply labeling. Actual-browser checks verified the original 100, fresh 900 and combined 1,000 views, eight diagonal distributions and all 56 pair plots, and the word filter. All 18 notebook tables and 45,907 pre-existing original-evidence files were unchanged before snapshot export.
