# Mind & discourse · full eligible corpus

The researcher explicitly authorized the full JEV job on 18 September 2026, after reviewing the pilot and actual token costs. This is a new finite allocation under the standing **$10 ceiling**, separate from the completed $2 pilot. A detached Python worker runs it through **Lab Jobs**; no language model supervises dispatch or polling.

**Latest outcome, 19 September:** stopped at 18,309 / 19,316 verified assessments after bounded recovery. Five uncertain outcomes and 1,002 unstarted requests remain. See [the recovery audit and descriptive report](MIND-DISCOURSE-RECOVERY.md). The historical running snapshot below is preserved.

## Frozen scope

- **9,646 real messages:** 9,605 conversation messages and 41 technical/short-run messages, across 408 source runs and 406 lineages.
- The frame is the existing 11,054-message JEV topic-corpus manifest. Exclude all 1,407 messages in the 60 reserved validation lineages, plus one whitespace-only message. Empty strings were already absent from that frame. No selection by topic, Gem score, thinker score or researcher preference.
- **12 existing synthetic control texts**, shown separately and reused; synthetic conversation fixtures are excluded.
- Two unchanged wording packs: **names + definitions** and **names + portraits**, each with 27 independent Noul features (16 thinkers/writers and 11 discourse practices). State contains only the original whole message. No preceding context, participant-model identity or notebook is sent.
- **19,316 logical assessments**, of which 120 exactly reuse pilot request/response pairs (96 real-message assessments and 24 control assessments). **19,196 new unique calls**; 521,532 total probabilities when complete, including 648 control probabilities.
- Inputs stay intact. The largest serialized request is 39,452 bytes, within the pilot's 48,000-byte screen. The original pilot, questions, source bytes, scores and notebook rows are unchanged.

Plan: `workspace/mind-lenses/discourse-corpus-20260918-v1/plan.json`, SHA-256 `5f7bebae4472d6cab782364479b6999c120c472118c0e5e02ff0f208c71f60ac`.

Execution release: `execution-v1/release.json`, SHA-256 `9f849cabccd155bfe0752a4fb594eea0352562db337a88c557c178435319f168`.

The plan and execution software are frozen. The separately versioned coordinator adapts the existing qualified corpus coordinator; earlier runners remain unchanged. Source run hashes and exact text are checked before preparation and dispatch/resume. Reuse requires exact payload and response identity.

## Execution

One aggregate integer ledger reserves $0.002688 before each attempt and replaces the reservation only with validated input usage at the recorded rate of $0.042 per million tokens. Unknown usage stays reserved. The release allows at most 19,386 new attempts, including 190 overload retries; only explicit HTTP 429/529 is retryable, with at most three attempts per request and global 20/60-second backoff or longer Retry-After. Invalid, uncertain or other failed outcomes stop dispatch.

Concurrency warms through one and four workers, then up to sixteen; requests are paced at no more than ten starts and 180,000 serialized bytes per second. A separate worker lock and the frozen runner lock prevent duplicate execution. Pause drains in-flight work. Restarting Explorer or closing the browser does not stop the worker. The registered job cannot expand its allocation or bypass the $10 cap.

The first two requests succeeded for $0.000423654 and were included in the allocation. The detached job then resumed the remaining calls. **The campaign is running at this document's creation; this is not a completion report.** Lab Jobs and immutable receipts provide current progress. A completed job cannot dispatch again.

```sh
python3 -m behaviorlab.lab_jobs status --id mind-discourse-corpus-v1
```

## Exploration

Open **Mind & discourse → Assessment dataset → Full eligible corpus · two wordings**, or use the job's **Open results** link. The original four-wording pilot remains separately accessible; old bookmarks default to that pilot.

- Full-corpus browsing defaults to conversation messages; technical messages and controls remain separately selectable.
- Topic filters join the existing topic scores to exact current messages. Consciousness ≥80 selects 1,900 conversation messages in this frame; that is eligibility by topic, not a claim that all Mind & discourse assessments are already finished.
- Select a source run and **Conversation / turn order** to inspect the profile through its messages. Model, length, topic and family filters combine with this selection.
- Tables show at most 100 rows per page. Overview statistics, population counts and filtering use the entire subset. Missing scores remain unknown. The two family means use their existing full-family definitions.
- **Load latest scores** reads new saved receipts. Navigating and filtering reuse the loaded snapshot, so incoming results do not silently reorder a table during reading. Export includes the selected dataset.
- Lab summary includes this batch separately from the pilot. Its coverage requires both wordings; overlapping messages do not inflate the combined coverage total.

These are exploratory classifier responses. Portrait and procedural criteria operationalize different patterns; their differences are not an isolated wording effect or accuracy improvement. Message-weighted results need conversation/lineage-aware interpretation. Independent classifier review remains pending.

## Verification

387 Python tests and 114 JavaScript tests passed. New tests cover exact reuse, no re-dispatch after completion, durable unknown outcomes, source changes, aggregate budgets and overload retries, independent worker control, dataset filters and pagination. Live browser checks verified the two registered jobs, the new corpus selector, Consciousness filtering, and page two preserving the 1,900-message subset. No browser test paused or restarted the live inference worker.
