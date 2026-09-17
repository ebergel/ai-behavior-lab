# Intact-window qualification and corpus preparation

17 September 2026. **Offline preparation is complete; the frozen 54-call TypeSafe qualification awaits the researcher's explicit external-dispatch approval. No new inference request has been sent.** The earlier 39-call qualification remains complete and unchanged.

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
- The same 27 targets in both question packs: **54 calls total, $0.60 aggregate ceiling**.
- Broad batch `d5078aa105039b65e07cb188`; detail batch `903d721b5cebc479b8011e0d`.
- Exact question/state content, software and plan hashes, target identities, selection rules and 18,732–50,347-byte qualification request sizes.

The unchanged direct HTTP runner pins `jev-1.13.0` at `https://api.typesafe.ai/v1/systemone`, records a durable request marker before transmission and preserves raw responses and reported usage. It stops on an error or an uncertain request; the aggregate coordinator blocks the other pack and any retry. Resume continues only previously unstarted requests. The shared ceiling is not an expected bill.

The [official model page](https://docs.typesafe.ai/models), checked 17 September 2026, lists $0.042 per million input tokens and free output. The full 64,000-input-token reserve across 54 calls is $0.145152. That is the existing runner's per-call reservation policy, not a calibrated forecast. The [API](https://docs.typesafe.ai/api) supports the typed question map and returns per-request usage. This implementation does not use the SDK's automatic retries.

Technical acceptance requires all 54 saved responses to validate under the unchanged model/usage/schema checks. Available historical full-pack scores will be compared with both new packs by exact target/question identity. Differences, including threshold crossings, are descriptive: historical comparisons cannot isolate question-pack effects from service/time variability. Technical acceptance does not imply semantic accuracy or calibrated probabilities. No threshold is changed to make the test pass.

## Approval status and continuation

Automatic approval review rejected the first command before it ran, because the prior approval explicitly covered 39 calls and this qualification sends additional private transcript/context content to TypeSafe. The researcher has been asked to approve **these 54 calls**, their payload, destination and $0.60 ceiling. The question is pending. Do not dispatch until that approval arrives; do not retry the rejected command through another route.

After explicit approval, save its receipt, run one pending request and inspect it, then complete only the remaining approved allocation:

```sh
python3 -m behaviorlab.jev_corpus run --workspace workspace \
  --qualification workspace/jev-atlas/intact-window-20260917-v1 --max-calls 1

python3 -m behaviorlab.jev_corpus run --workspace workspace \
  --qualification workspace/jev-atlas/intact-window-20260917-v1

python3 -m behaviorlab.jev_corpus summarize --workspace workspace \
  --qualification workspace/jev-atlas/intact-window-20260917-v1
```

The coordinator remains frozen at preparation. A separate source or software change requires a new version; never overwrite this freeze or earlier stopped/failed evidence. The Explorer displays both packs, pending targets and unavailable scores, and does not dispatch inference.

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

Tests exercise exact question partitions and identical states, refusal rather than truncation for windows beyond the limit, source drift, resume without duplicate calls, aggregate stop after failure, exact-result reuse, reference-root separation, full-path branch quality and speaker attribution. Synthetic responses occur only in temporary tests. All research qualification rows remain pending.

The atlas handles a qualification inventory without inheriting the earlier 56-reading packet. It also directs related packs to their aggregate coordinator instead of displaying a standalone command that could bypass aggregate accounting. Original batches retain their source links, scores and reviews.
