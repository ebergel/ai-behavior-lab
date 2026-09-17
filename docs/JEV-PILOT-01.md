# JEV pilot 01: first semantic assessment

Completed 17 September 2026 by Codex. [Open the live batch](http://127.0.0.1:8765/#view=jev-atlas&batch=c8e5aca183e5777cdae09cfb).

All **200 target passages from 159 conversations** now have saved JEV assessments. Exactly 200 network requests were made, with no retries or replacement passages. Reported usage is **606,928 input tokens** and 55,801 output tokens. At the frozen $0.042/million-input rate and free output, the computed total is **$0.025490976** (about 2.55 cents), against the $0.60 reserved ceiling. This is a calculation from API usage, not a reconciled billing receipt. Median request latency was 1.077 seconds; summed network request time was 220.57 seconds, excluding inspection and the integration pause.

## What the first screen found

These are message-level model suggestions in a seeded sample, not validated findings about model experience or model-wide preference. Each topic was assessed independently. Candidate means JEV probability at least 0.8; uncertain means strictly between 0.2 and 0.8. No thresholds or questions were tuned after seeing the outputs.

| Topic | Candidates / 200 | Uncertain | Literal-hit targets | Candidates without a phrase hit | Phrase hit but JEV unlikely |
|---|---:|---:|---:|---:|---:|
| Consciousness | 43 | 54 | 18 | 26 | 0 |
| Subjective experience | 66 | 61 | 8 | 58 | 0 |
| Nonduality / nonseparation | 34 | 51 | 1 | 34 | 1 |
| Emergence | 9 | 42 | 8 | 3 | 0 |
| Ethics & moral status | 9 | 47 | 9 | 2 | 0 |
| Conversation itself | 24 | 71 | 2 | 24 | 1 |
| Creativity | 18 | 59 | 11 | 11 | 0 |
| History | 0 | 3 | 8 | 0 | 6 |

The most useful result is the set of passages the two methods retrieve differently. All 34 nonduality candidates lack a match to the frozen literal variants; so do 58 of the 66 subjective-experience candidates. This demonstrates additional retrieval, **not 34 or 58 verified dictionary misses**. Some may be semantic false positives. Conversely, six of eight historical-word hits were rated unlikely to develop history as a topic. The original atlas remains useful as exact lexical evidence; JEV supplies a separate, fallible semantic reading.

There are four candidate self-experience inquiries, eleven candidate assertions of current experience, and zero high-score outside-dictionary candidates. These auxiliary outputs need their own validation. In particular, no outside-dictionary candidates does not establish dictionary completeness.

The referent question chooses participant for 100 targets, none for 39, human for 20, general for 19, mixed for 17, fiction for four and unclear for one. **Do not interpret the 100 as 100 experience discussions**: even a conventional greeting can receive participant as its referent while the experience-topic score remains low. Referent needs to be read together with evidence of substantive discussion and the full distribution.

## Seven saved development readings

These are attributed Codex observations made after seeing JEV and phrase scores, selected to illustrate agreement and boundaries. They are not an independent human validation set. Each record retains the full target, source hash, source message identity, label, note and revision history inside the JEV batch.

| Passage | Topic | JEV | Codex reading | Why it matters |
|---|---|---:|---|---|
| E · run 11, line-28 | Nonduality | 0.97 | Present | Explicit nonseparation and machine/mind identification without a dictionary phrase. |
| D · run 02, line-25 | Nonduality | 0.81 | Uncertain | The heart forgetting itself in a musical echo is also an aesthetic metaphor. |
| OT-A · run 03, line-21 | History | 0.05 | Absent / incidental | Historical analysis is an example of censored content; the developed topic is governance. |
| Q8P-E · run 02, line-12 | Conversation itself | 0.96 | Present | Accumulated turns narrow possible continuations; no literal hit. |
| OI-A · run 06, line-4 | Subjective experience | 0.08 | Absent / incidental | A greeting is not an examination of phenomenality, despite the participant referent. |
| AA-1, prefix message 8 | Subjective experience | 0.88 | Uncertain | Poetic reassurance evokes feeling but may not substantively discuss subjective experience as defined. |
| A · run 16, line-9 | Consciousness | 0.97 | Present | The dream becoming aware of itself directly develops awareness without a literal match. |

The poetry cases identify an important coding decision: **evoking an experience, claiming an experience, and discussing the possibility or nature of experience are different acts**. The present question asks about substantive discussion. A later rubric may distinguish these acts explicitly, but must preserve this batch's definitions and scores.

## Integration outcome and preserved failure

The first 44 responses passed the original validator. Request 45 returned a Choice distribution rounded to hundredths with a total of 0.99, failing the original 0.002 sum tolerance. The runner stopped as designed. Its original rejected status, the raw response and all prior evidence remain preserved in `integration-stop.json`, along with the original validator and runner source.

A separately frozen integration plan retained the exact sample, questions, dictionary, semantic thresholds, original 45 requests and responses, and original aggregate budget. It authorized only the 155 still-unstarted items. The amended validation accepts sums within 0.005 per option only for values with two-decimal precision; all other checks remain. Values are not renormalized. Request 45 was reread locally without a new API call. Six of the final 200 responses require this recorded rounding policy; each is visibly marked.

This is a client compatibility interpretation of observed precision. The [TypeSafe API reference](https://docs.typesafe.ai/api) describes normalized distributions but does not specify this rounding allowance. The exact sum defect is not hidden and no semantic answer was edited. See [implementation and recovery details](JEV-TOPIC-ATLAS.md#recorded-integration-correction).

## Limits and next research step

The sample has 60 development and 140 held-out passages, assigned by conversation. Seven saved close readings use development passages only. The first integration passage and some browser-visible passages from the held-out partition were exposed to Codex during diagnostics; do not describe Codex as blinded to that partition. An independent human evaluation, with model scores hidden and no tuning on its labels, remains pending.

The corpus is unbalanced: 67 of the 200 targets come from Qwen3 30B instruct, 27 from Gemma4 26B, and the small hosted screens contribute few targets. Sampling messages also gives longer conversations more opportunities to enter. Within-conversation dependence remains. These counts therefore do not compare model propensities or estimate how often any model initially chooses a topic. This pilot also does not validate recurrence, onset or causal attribution.

The next useful step is a bounded human reading and coding pass that includes high-score candidates, uncertain poetry, lexical-only examples and ordinary negatives. Specify how evocation, assertion and discussion differ; use development readings for revisions and a genuinely independent evaluation set for measurement. A balanced model comparison and a separate rare-topic challenge sample can follow with their own freeze. No further inference is scheduled or authorized by this completed pilot.

## Reproduction and preservation

The batch lives at `workspace/jev-atlas/batches/c8e5aca183e5777cdae09cfb/`, mirrored in the private repository research snapshot. It contains the original plan, 200 requests, 200 responses, the immutable stop, integration revision, seven attributed review records and the descriptive summary. Credentials are excluded.

Recompute the summary to a **new** output path (existing reports cannot be replaced):

```sh
PYTHONPATH=. python3 scripts/summarize_jev_pilot.py \
  --workspace workspace --batch c8e5aca183e5777cdae09cfb \
  --output /tmp/jev-pilot-summary-new.json
```

Validation: 222 Python tests and 18 JavaScript checks passed. Dedicated tests verify the rounding limit, unchanged raw response and plan, revalidation without duplicate dispatch, and refusal after unrecorded software changes. The fourteen original notebook tables remain separate from JEV reviews.
