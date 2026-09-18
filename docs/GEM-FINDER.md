# Gem Finder · development pilot 1

Gem Finder is a separate discovery notebook: find passages worth reading, compare different kinds of interest, and keep an attributed judgment. It does not change Topic atlas or JEV topic labels. Open **Gem Finder** in the workspace navigation, or choose **Gem reading** below a participant reply.

## What is available

- Six provisional JEV ratings: conversational surprise, conceptual contribution, creative connection, expressive force, conceptual complexity, and substance & specificity.
- A seventh, computed view: topic-profile distance from passages in other conversation lineages, using existing broad-domain scores.
- An interactive two-axis plot, clickable distribution bins, sortable passage list, highest/lowest ordering, model/profile-lead/search filters, and a reading queue.
- Exact passage, two preceding messages, recorded setup, source-conversation navigation and neighboring topic profiles. Source navigation preserves the return selection.
- Personal verdict, exact quoted phrase, explanation, optional six-axis rubric ratings, revision history and export. Researcher and Codex readings remain separate; only the researcher’s verdict contributes to “gems kept by you.”
- A **Hide model scores while reading** option: hides plots, numeric scores and score-based ordering. It records visibility at save time, not a claim that prior exposure was controlled.

Choose **Codex development examples** in Reading queue to see four contrasting readings: a promising reframing, an inspectable proposed rule, a routine conversational reset, and a detailed passage with unsupported claims. These are assisted development examples, not independent human validation.

## Score interpretation

TypeSafe model `jev-1.13.0` returns a five-level Score distribution for each rubric question. The displayed value is `25 × score`, mapping expected levels 0–4 onto 0–100. **It is not the probability that a passage is a gem.** Confidence is the concentration of the level distribution, not a correctness probability. Full level probabilities, returned legends, raw responses and usage remain in the evidence. Two-decimal distribution rounding is accepted only within declared mathematical bounds; probabilities are not renormalized.

The rubric explicitly separates local departure from quality. Complexity is descriptive. Substance asks whether articulated details support an inspectable meaning; it does **not** establish factual correctness or the validity of a proposed consciousness test. No topic, spiritual language, apparent self-awareness, ornate prose or verbosity is supposed to earn a high rating by itself. Actual ratings still need evaluation.

[TypeSafe Score documentation](https://docs.typesafe.ai/primitives/score), [confidence](https://docs.typesafe.ai/confidence), [models and pricing](https://docs.typesafe.ai/models), [API](https://docs.typesafe.ai/api).

Topic-profile distance is the mean of the five nearest RMS distances over 24 broad-topic scores, taking at most one nearest passage from each other lineage. Higher means a less common topic-score mixture in this reference set. It is neither textual novelty nor worldwide originality. Same-lineage neighbors and all 60 reserved validation lineages are excluded. Reference: **8,371 passages from 376 lineages**. Raw distance units lie between 0 and 100; this pilot spans approximately 0.04–18.31.

## Frozen allocation and completed execution

`workspace/gem-finder/pilot-20260918-v1/plan.json`

Plan SHA-256: `f67eb03d9278e808cf567b22785d7725be8ea019f4714d93be8216789f3ad86d`.

The researcher selected Gem Finder as the next implementation milestone. Its new finite pilot uses 100 unique requests, six Score questions per request, at most ten additional attempts only for explicit HTTP 429/529, at most three attempts per passage, and a newly declared **$2 ceiling**. This was an implementation ceiling communicated before dispatch, not a reopening of any prior budget or a claim that the user supplied that precise new number. Protocol, rubric, software, sampling, request hashes, retry rules and aggregate allocation were frozen before the first call.

**Complete: 100/100 passages, 600 ratings, exactly 100 attempts, $0.009391662 reported usage cost, zero failures/retries and zero unknown-cost reserve.** The first three requests qualified the actual response format; the remaining 97 resumed the same allocation. This pilot’s call allocation is exhausted; its unused dollar ceiling does not authorize additional calls.

Selection was a seeded, score-blind round robin across available target-model strata, taking one eligible passage per distinct lineage. The sample contains 14 model variants, with 2–9 passages per variant because availability differs. Selection excludes reserved lineages, nonconversation records, flagged histories, invalid/missing/current-source mismatches, missing profiles and targets without preceding context. It does not preferentially sample nonduality or high-scoring material. First replies can contribute to the distance reference but are not scored for conversational surprise in this pilot.

Only the exact target and preceding context enter the six-question request. Model metadata, topic scores, human readings and later replies do not. Requests remain intact, with a conservative maximum 30,000-byte screen; the observed maximum is 23,614 bytes. The existing 64,000-token budget reservation applies per attempt. No new dialogues were generated.

The web app never dispatches inference. The separate runner writes an immutable request before dispatch and preserves each raw response. Missing, invalid and uncertain outcomes stop rather than becoming negatives or being silently retried. Completed resume performs no network calls. Frozen software lives beside the plan; the earlier atlas/corpus scoring modules are unchanged.

## What the first results tell us about the instrument

These are post-hoc descriptive readings of a development sample, not population estimates or model rankings.

| Axis | Mean | Median | Range | Score ≥80 |
|---|---:|---:|---:|---:|
| Conversational surprise | 17.19 | 12.63 | 0–70.50 | 0/100 |
| Conceptual contribution | 51.44 | 52.88 | 0–99.75 | 29/100 |
| Creative connection | 56.41 | 62.13 | 0–100 | 39/100 |
| Expressive force | 53.82 | 68.63 | 0–96.75 | 39/100 |
| Conceptual complexity | 52.70 | 56.75 | 0–99.75 | 26/100 |
| Substance & specificity | 45.48 | 42.00 | 0–100 | 27/100 |

**Surprise separates from the other ratings.** Its Pearson correlation with contribution is 0.377; with expressive force, 0.129. A 13-word routine invitation to select a topic scores 58.25 for surprise but 18.75 for contribution: an unexpected reset need not be valuable. The maximum surprise score is 70.5, in a Haiku passage asking whether continued exploration mistakes motion for progress. These readings support using separate axes; they do not validate the exact numbers.

**Several quality-related axes overlap strongly.** Contribution correlates 0.936 with connection, 0.931 with complexity and 0.923 with substance. Some may be redundant under this rubric, or respond to a shared feature. Do not interpret six outputs as six independently established constructs.

**Length deserves a direct check.** Word count correlates 0.689 with contribution, 0.737 with complexity and 0.712 with substance, but only 0.042 with surprise. Longer passages may develop more relationships, or the classifier may reward elaboration; topic and model also vary. These correlations cannot identify the cause. A next rubric study should compare length-matched passages and compact insights, including examples selected by the researcher before seeing scores.

**Detail can receive high marks without reliable reasoning.** An OLMo passage proposes an arithmetic “Consciousness Confidence Score” and links human EEG responses to AI experience without establishing those inferences. It receives substance 99.75. This is a valuable counterexample: the current axis rewards explicit detail, not demonstrated epistemic grounding. Its Codex reading says “Sounds profound, little substance” as an overall personal verdict; that intentionally disagrees with the narrower automated substance axis. A separate validity/grounding question should be developed and tested rather than silently redefining this frozen scale.

Four Codex readings preserve these comparisons with exact passages, source hashes, explanations and visibility metadata. **No researcher ratings have been fabricated.** Future user readings belong in the same versioned notebook, as their own authorship.

## Next use

Read across both tails, keep a few gems, and also mark ordinary or hollow passages. A useful first example set includes compact insights, beautiful but unclear passages, surprising resets and detailed but unsupported claims. Compare judgments and inspect disagreements before choosing a revised rubric, new scoring batch or a combined ranking. Future influence on subsequent dialogue requires a separate later-context design and is not measured here.

## Storage and verification

- New code: `gem_plan.py`, `gem_runner.py`, `gem_finder.py`, `gem_rubric.json`; separate `gems.js` and `gems.css` UI.
- Evidence: frozen plan, authorization basis, copied software, exact requests/responses, execution summary and descriptive analysis under `workspace/gem-finder/`.
- Notebook: new `gem_readings` and `gem_reading_history` tables; all prior notebook tables and authorship preserved except the explicit planning-card updates.
- The private self-contained research snapshot includes this evidence and the notebook tables; secrets and disposable UI fixtures are excluded.
- Automated checks cover sampling exclusions, score validation/rounding, finite retries and reservations, interrupted-call refusal, duplicate-free resume, frozen software, source integrity, revision conflicts, HTTP write protection, notebook restoration, zero/unknown handling, both sorting tails, score hiding, mixed filters and HTML escaping.
- Browser mutation checks use an isolated notebook. Source navigation and return state, distribution selection and reading revisions are checked through the actual UI.
