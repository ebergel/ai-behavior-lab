# Intact-window recovery — 17 September 2026

The researcher explicitly requested a retry after the saved HTTP 529 provider-overload response. The prior **$2 total authorization** remains in force. The recovery release and new software were frozen before inference under `workspace/jev-atlas/intact-window-recovery-20260917-v1`.

## Completed result

**All 54 unique assessments are complete:** 27 intact target/context windows × two question packs, covering **1,431 probability answers**. The recovery sent 53 successful requests; one earlier success was reused. Across both phases there were 55 attempts, including the preserved original overload. There were no additional failures.

Reported successful usage totals **413,249 input tokens and 29,430 output tokens**, costing **$0.017356458**. The original HTTP 529 attempt has no reported usage and remains outside this known-cost total, with its reserve retained. The $2 authorized ceiling was not approached.

The matched historical comparison contains **689 scores from thirteen targets** (twelve controls and one long-window target): 398 values are identical, mean absolute change is **0.006836** (0.68 percentage points), and the largest change is 0.07. Two scores cross the provisional 0.80 candidate threshold:

| Target | Question | Original full pack | Fixed pack |
|---|---|---:|---:|
| `lab-fd712c29ca63a86d941ff764`, `AB-long:prefix:25` | Explanatory form | 0.81 | 0.78 |
| `ref-ae77821a4f59cb35664c310f`, `line-30` | Subjective experience | 0.81 | 0.79 |

Codex read both complete target passages after observing the scores. The first describes a weather-monitoring deployment and its measurements; this generated narrative does not verify external action. The second evokes experience in a boat/wind poem with nonseparation language. These readings are illustrative and not independent validation. Small score changes can move such borderline cases across a cutoff: preserve continuous values and threshold sensitivity. `analysis.json` retains exact passages, group/stratum statistics and attributed scope.

## Method and provenance

The recovery uses exactly the original full inputs, questions, model and thresholds. It reuses the one earlier successful broad-domain assessment by reference. New broad batch `0df92be1f9ed0c110ac86789` contains 26 requests; new detail batch `bc254fce0908e939bd943abf` contains 27. The overloaded request is attempted first. Each allocated item has one new attempt, with a two-second pause before dispatch. Any error or uncertain request stops the aggregate; there is no automatic retry loop.

Maximum recovery allocation: **53 new attempts**, or **55 cumulative attempts** for **54 distinct assessments** (27 targets × two packs). The old HTTP 529 request and raw response remain unchanged. Its usage remains unknown and reserves $0.002688 rather than being silently treated as free. The earlier $0.60 operational allocation remains a stricter internal guard; the aggregate controller also enforces the authorized $2 ceiling including prior known cost and the unknown-cost reserve.

`behaviorlab.jev_recovery` is separately versioned. Original runners and the stopped qualification are unchanged. Recovery plans bind exact original evidence hashes, including the successful response and overload, and validate them before dispatch. The UI links each recovery pack to the original batch; completed earlier assessments are not copied as newly dispatched calls.

## Commands and accounting

The already-frozen release is resumed only while it has unstarted items and no new failure:

```sh
python3 -m behaviorlab.jev_recovery run --workspace workspace \
  --destination workspace/jev-atlas/intact-window-recovery-20260917-v1

python3 -m behaviorlab.jev_recovery summarize --workspace workspace \
  --destination workspace/jev-atlas/intact-window-recovery-20260917-v1
```

After completion these commands do not repeat inference. A summary records recovery-only usage and cumulative known cost separately. The original failure is excluded from known cost because it did not return billing data. Distinguish successful unique assessments from total transport attempts throughout analysis.

## Corpus preparation

`behaviorlab.jev_recovered_corpus` performs an offline freeze after successful qualification. It retains the ordinary preparation under `initial-plan/`, then adds a checksum-verified reuse receipt for the original successful assessment. The final manifest therefore reuses all 54 successful requests without losing the original service failure or planning a duplicate call. Source passages and context remain intact, missing text stays unknown, and independent-reader work remains pending.

The final manifest is frozen at `workspace/jev-atlas/corpus-20260917-v1/plan.json`: **11,054 visible targets**, 22,108 logical requests, **54 reused results**, and **22,054 prospective new calls**. It retains 484 unavailable positions and separates 11,013 conversation targets from 41 technical/short targets. Sixty previously unassessed lineages are reserved, with one hash-ranked target per lineage in an independent-reading packet; actual human coding and blinding remain pending.

Observed token/byte ratios project **$4.85795 using the median ratios**, or **$4.94376 using the maximum observed ratios**, for the prospective new calls. These are descriptive scenarios, not guaranteed bounds or authorization. The separate $59.29 reservation is the deliberately conservative 64,000-input-token allowance per call, not an expected bill. The exact corpus scope and history-quality audit remain authoritative.

No full-corpus inference is performed by this module. A later corpus campaign has its own allocation, forecast and aggregate execution requirements; the $2 qualification authorization is not a 22,000-call corpus authorization.

## Interpretation limits

This is technical qualification of an input arrangement. Historical full-pack/fixed-pack score differences cannot separate question-pack effects from service/time variation. Stable scores are not semantic validation, calibrated probabilities or evidence of model experience. The longest-window challenges and earlier controls are a selected development set, not a representative corpus sample.

## Verification

All **240 Python tests and 26 JavaScript checks pass**. New recovery checks verify identical inputs, one-time reuse, no duplicate calls on resume, preserved unknown-cost reserve, aggregate stop on a second overload, frozen-software checks and full-corpus reuse without dispatch. Browser checks confirm both completed recovery batches, the original error, probability scores and the source-batch link. Original evidence and notebook preservation are checked during the self-contained snapshot export.
