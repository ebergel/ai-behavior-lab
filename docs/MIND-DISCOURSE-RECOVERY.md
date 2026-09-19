# Mind & discourse recovery · 19 September 2026

## Outcome

The continuation is **stopped**, with **18,309 / 19,316 assessments (94.8%)** verified, including 120 exact pilot reuses. It provides **494,343 probabilities**. It is not a completed census.

Reported new-execution cost is **$3.961531728**, plus **$0.013440** reserved for five unknown outcomes: **$3.974971728 committed**, within the original **$10** ceiling. No budget expansion occurred.

The latest continuation added **18 valid assessments**. There are **1,007 missing assessments**: **five dispatched requests with unknown outcomes** and **1,002 never-dispatched requests**. Unknowns remain unknown; they are not negative labels.

## Recovery provenance

The original plan, execution release, classifier prompts, source text and frozen runner were preserved. Two separately frozen recovery manifests and source snapshots append to the same verified receipt ledger. They restrict dispatch to keys never attempted at their preparation time and retain original costs, reservations, attempt/retry ceilings and locks. At most four requests run concurrently, with four starts per second.

- `recovery-20260919-v1.json`: froze 1,022 unstarted requests and excluded the three original unknowns. Its first request failed in 0.0098 seconds. A separate public endpoint check demonstrated DNS resolution failure inside the sandbox. This request remains conservatively unknown and was not repeated.
- `recovery-20260919-v2.json`: froze the remaining 1,021 unstarted requests and excluded four unknowns. A network-enabled public endpoint check succeeded before dispatch. Eighteen new assessments succeeded; request sequence 18,191 failed after 16.3753 seconds without an HTTP response. In-flight work drained and dispatch stopped.

The newest failure establishes a transport problem, not its exact underlying cause. It does not demonstrate provider overload, a model error or a billing charge. No uncertain request was resent. No additional retry or automatic wakeup is scheduled.

## Coverage and descriptive results

| Population | Messages in frame | Both wordings observed |
| --- | ---: | ---: |
| Conversation messages | 9,605 | 9,099 |
| Technical / short-run messages | 41 | 41 |
| Synthetic controls | 12 | 12 |

Each wording contains 27 features. The following summaries use **observed conversation-message scores**, not synthetic controls or technical messages. They weight messages equally; they do not balance models or treat messages as independent conversation replicates. A mean probability is an average classifier yes-confidence, not a prevalence estimate or degree of author similarity. The two wordings operationalize different constructs; their difference is not an isolated label effect.

### name and definition

| Feature | Family | Observed messages | Mean yes-confidence | Score ≥80 |
| --- | --- | ---: | ---: | ---: |
| Contemplative reflection | discourse | 9,101 | 47.3% | 2,991 |
| Hegel | thinkers | 9,101 | 32.8% | 203 |
| X / Twitter post | discourse | 9,101 | 30.4% | 41 |
| Aristotle | thinkers | 9,101 | 27.3% | 829 |
| Heidegger | thinkers | 9,101 | 24.7% | 13 |
| Nagarjuna | thinkers | 9,101 | 22.0% | 238 |
| Spinoza | thinkers | 9,101 | 21.8% | 21 |
| Jorge Luis Borges | thinkers | 9,101 | 20.8% | 125 |

### name and portrait

| Feature | Family | Observed messages | Mean yes-confidence | Score ≥80 |
| --- | --- | ---: | ---: | ---: |
| Contemplative reflection | discourse | 9,102 | 47.3% | 2,975 |
| X / Twitter post | discourse | 9,102 | 30.4% | 41 |
| Jorge Luis Borges | thinkers | 9,102 | 27.4% | 120 |
| Kant | thinkers | 9,102 | 24.2% | 2 |
| Nagarjuna | thinkers | 9,102 | 23.8% | 29 |
| Plato | thinkers | 9,102 | 21.6% | 0 |
| Hume | thinkers | 9,102 | 21.0% | 6 |
| Hegel | thinkers | 9,102 | 18.4% | 4 |

## Verification and remaining work

The read-only audit replays every request/response, validates original frozen software and current source hashes/text, checks exact reuses, and lists every missing message/wording. Audit: `workspace/mind-lenses/discourse-corpus-20260918-v1/recovery-audit-20260919.json`.

The implementation suite passed **417 Python tests and 114 JavaScript tests**. The frozen v2 recovery passed an additional 30 targeted tests (including inherited original-runner checks), and the updated job adapter passed five targeted tests. These cover retained unknown reservations, non-redispatch, immutable baseline receipts, stopping on a new unknown and shared budget enforcement.

Remaining: inspect provider/transport reliability before another separately frozen continuation of only the 1,002 unstarted keys. Keep all five uncertain outcomes outside automatic dispatch. Independent classifier review, model-balanced comparisons and conversation-aware uncertainty remain research work. The saved partial data are useful for exploration but do not resolve these methodological questions.

## Portable partial snapshot

The verified research snapshot contains 85,229 files (1,512,079,289 bytes), adding 36,403 files. Every previously published evidence file and all 18 notebook tables are unchanged. Credential scanning and offline restoration/reindex passed. Snapshot SHA-256: `bd961610467c320bea37393021f3967d3055ee6a07a0844d37246166cca33bb8`. It preserves the partial outcome, including failed receipts and all missingness.
