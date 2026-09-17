# Intact-window qualification and corpus preparation

**Subsequent outcome:** the researcher explicitly requested retry. [The separate recovery completed all 54 unique assessments](JEV-INTACT-WINDOW-RECOVERY.md), reusing the first success and preserving the overload below. Known total cost is $0.017356458; the final corpus inputs are frozen but unexecuted. This document retains the original preparation and stop history.

17 September 2026. **The researcher approved the 54-call qualification and raised its authorized ceiling to $2. Two requests were sent: one completed and the second returned HTTP 529 (`system_overloaded`). The frozen failure rule stopped both packs; 52 requests remain unstarted.** The earlier 39-call qualification remains complete and unchanged.

## Preserve the passage; partition the questions

The full 53-question request adds roughly 41 KB of question definitions to each target/context window. Nine current requests exceed the original runner's conservative 60,000-byte screen, although the largest target/context window is only 27,644 bytes. The longest complete request would be 68,808 bytes.

A uniform pair of question packs solves the current size problem without cutting the evidence:

| Fixed pack | Questions | Contents |
|---|---:|---|
| Broad | 24 | All broad-domain questions |
| Detail | 29 | Focused topics, form, stance/referent and coverage checks |

The two packs partition all 53 frozen question objects exactly once. Every question retains its wording and criteria. Both receive the identical full target and its two actual preceding evidence events. No text is truncated, summarized, chunked or combined through maximum scores. Scores will be joined by target identity and question ID, with both original response files retained.

Applying the same partition to short and long messages avoids assigning a different question-pack method only to difficult passages. It remains a changed assessment arrangement, so qualify it and preserve its version separately from the completed 53-question batch.

All **22,108 logical requests** for the **11,054 visible targets** passed the offline byte check: **18,567–50,347 bytes**. This is an input-size and preservation check, not evidence that the service has processed the requests or that long-context classification is accurate.

## Frozen finite qualification

`workspace/jev-atlas/intact-window-20260917-v1/qualification.json` fixes:

- All 15 visible windows above the original 18,000-byte window screen, including capped/after-cap output.
- The first twelve root-sampled controls from the completed 53-question qualification, selected without using their scores.
- The same 27 targets in both question packs: **54 calls total, originally allocated $0.60 aggregate**. The later authorization amendment raises the approved total ceiling to **$2**; the smaller $0.30 per-pack guards are preserved and sufficient for this fixed allocation.
- Broad batch `d5078aa105039b65e07cb188`; detail batch `903d721b5cebc479b8011e0d`.
- Exact question/state content, software and plan hashes, target identities, selection rules and 18,732–50,347-byte qualification request sizes.

The unchanged direct HTTP runner pins `jev-1.13.0` at `https://api.typesafe.ai/v1/systemone`, records a durable request marker before transmission and preserves raw responses and reported usage. It stops on an error or an uncertain request; the aggregate coordinator blocks the other pack and any retry. Resume continues only previously unstarted requests. The shared ceiling is not an expected bill.

The [official model page](https://docs.typesafe.ai/models), checked 17 September 2026, lists $0.042 per million input tokens and free output. The full 64,000-input-token reserve across 54 calls is $0.145152. That is the existing runner's per-call reservation policy, not a calibrated forecast. The [API](https://docs.typesafe.ai/api) supports the typed question map and returns per-request usage. This implementation does not use the SDK's automatic retries.

Technical acceptance requires all 54 saved responses to validate under the unchanged model/usage/schema checks. Available historical full-pack scores will be compared with both new packs by exact target/question identity. Differences, including threshold crossings, are descriptive: historical comparisons cannot isolate question-pack effects from service/time variability. Technical acceptance does not imply semantic accuracy or calibrated probabilities. No threshold is changed to make the test pass.

## Approval, service stop and remaining work

The researcher explicitly approved this qualification and raised the authorized total to **$2**. `authorization-amendment.json` preserves the exact message and original protocol hash. It does not rewrite the original $0.60 allocation or $0.30 per-pack guards; those stricter limits are already sufficient for 54 calls. The researcher also clarified that transcripts are nonconfidential model output with no personal information. The repository remains private because the project is not yet ready for publication; credentials remain secret. The earlier automatic approval rejection was resolved by this explicit approval.

| Observed result | Value |
|---|---:|
| Requests sent | 2 |
| Valid responses | 1 |
| Provider-overload responses | 1 |
| Never-started requests | 52 |
| Validated probability answers | 24 |
| Reported input / output tokens | 8,778 / 513 |
| Known usage-based cost | $0.000368676 |
| Calls without usage information | 1 |

The first response used the pinned `jev-1.13.0` and returned all 24 broad-domain answers for the intact long passage. The second returned HTTP 529 with `error_type: system_overloaded` and no token usage. The raw error is retained, and the failed assessment remains unknown, not negative. There were no automatic retries. Known cost excludes the failed request because its billing was not reported.

`first-response-check.json`, `stopped-summary.json` and `stop-record.json` preserve the checks and exact accounting. All-54 technical acceptance is **not met**; there are no matched full-pack/fixed-pack comparisons yet. One structural success does not establish semantic accuracy or long-context reliability. This stop reflects provider availability, not demonstrated inability to process the passage.

`recovery-draft.json` records the exact remaining work: reuse the successful response, explicitly retry the one saved overloaded request once, and assess the 52 never-started requests. That would require **53 additional attempts, 55 cumulative attempts for the original 54 distinct assessments**. The draft proposes two-second spacing, reserves the unknown-cost attempt rather than assuming it was free, and stops at any further failure. It is **not active**. A separately recorded recovery release and software freeze must precede dispatch; the original coordinator deliberately refuses to resume past failed evidence. The existing $2 authorization and transcript classification carry forward.

No complete qualification summary or final corpus manifest has been fabricated. The offline corpus audit below is preserved, and `freeze-corpus` remains gated until qualification succeeds. No corpus calls, public release or scheduled retries were started.

## Prepared corpus scope

`corpus-readiness.json` records every logical request's hash, byte size, source identity, pack and quality status, plus the exact question packs. It is a frozen **offline preflight**, not an executable full-corpus allocation. Counts:

| Unit | Count |
|---|---:|
| Visible targets in the 438 eligible conversation records | 11,013 |
| Visible targets in technical/short records | 41 |
| Total visible targets | 11,054 |
| Unavailable participant positions, retained as unknown | 484 |
| Questions per target | 53 |
| Logical requests, two per target | 22,108 |
| Qualification requests that can be reused if completed and identical | 54 |
| Prospective new corpus calls after that reuse | 22,054 |

Synthetic records remain outside behavioral assessment. Technical checks, source data classes, capped/after-cap targets and unavailable history stay identifiable. The existing collection is not a balanced experimental design; classifying it cannot establish autonomous model preference rates.

`scope-audit.json` records the **actual speaker model** and quality/unavailability across **all preceding events on the actual parent path**, rather than just the classifier's two-event context. All 11,054 targets have a recorded speaker model. A normal target with incomplete/flagged earlier history is not a clean-history case:

- 9,587 targets have a recorded/valid target and no flagged or missing preceding event in the saved projection.
- 1,467 have a flagged target or flagged/incomplete history: 123 more than the 1,344 visibly flagged targets alone.

“Clean observed history” does not certify historical runtime validity. The audit preserves all cases; it does not discard them. Branches use their actual ancestors and shared nodes occur once. Exact transcript-structure lineages support a separate weighting sensitivity view; historical independence is not asserted.

The corpus-freeze implementation requires the live qualification summary to be complete. It then fixes the exact full target/context inputs, question packs, source identities, reuse receipts and remaining call ceiling. It reserves up to 60 previously unassessed lineages for one hash-ranked independent-reading target per lineage, excluding all development and earlier assessment lineages. That packet omits JEV scores and model metadata; actual reader blinding still has to be documented. No human ratings are fabricated, and no reference packet is claimed completed before this gate.

```sh
python3 -m behaviorlab.jev_corpus freeze-corpus --workspace workspace \
  --qualification workspace/jev-atlas/intact-window-20260917-v1 \
  --destination workspace/jev-atlas/corpus-20260917-v1
```

The final manifest uses observed per-pack input-token/byte ratios to give median-ratio and maximum-observed-ratio cost scenarios. Those are estimates, not guaranteed bounds. A separate ceiling reserves 64,000 input tokens per new call. The 54-call approval does not authorize those roughly 22,000 later calls, and this module deliberately has no corpus-dispatch command.

## Verification

Tests exercise exact question partitions and identical states, refusal rather than truncation for windows beyond the limit, source drift, resume without duplicate calls, aggregate stop after failure, exact-result reuse, reference-root separation, full-path branch quality and speaker attribution. Synthetic responses occur only in temporary tests. The live UI shows one completed assessment, the failed request with no score, and remaining targets as unassessed. The untouched detail pack remains prepared. All 236 Python tests and 26 JavaScript checks pass.

The atlas handles a qualification inventory without inheriting the earlier 56-reading packet. It also directs related packs to their aggregate coordinator instead of displaying a standalone command that could bypass aggregate accounting. Original batches retain their source links, scores and reviews.
