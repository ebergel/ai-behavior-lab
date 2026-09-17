# JEV Topic Atlas

An independent semantic assessment layer beside the existing Topic atlas. Open **JEV Topic Atlas** in the sidebar or [open the local view](http://127.0.0.1:8765/#view=jev-atlas).

## What is implemented

- Prepare a finite passage sample from all eligible conversations or a saved research collection, with selectable topic questions.
- Freeze a separate copy of the dictionary, exact target text, up to two preceding participant messages, source identities, questions, sampling seed, model and spending limits.
- Browse a topic overview, comparison queues, text search, probability/title sorting and a close reading panel with model tags and experimental condition.
- Open the original conversation and return with the topic, queue, passage and page preserved in the URL.
- Record present/absent/uncertain judgments and observations, retaining every revision separately from JEV's original output. Hide model judgments and literal matches for an initial reading.
- Export the complete batch, exact requests, raw responses, probabilities, usage and review history.

The existing Topic atlas, its phrase counts, initial-topic reviews and notebook tables are untouched. JEV files live under `workspace/jev-atlas/batches/<batch-id>/`. Requests and responses are separately checksummed immutable files; reviews use append-only revisions. The regular research snapshot exporter already includes these JSON files and restores them offline.

The Explorer prepares local records and reads saved responses. **Only the separate terminal runner contacts TypeSafe.** Page loads, filtering, export and personal review make no inference calls.

## First prepared pilot

Batch: `c8e5aca183e5777cdae09cfb` — **JEV pilot 01 · semantic topics across the corpus**.

Prepared by Codex on 17 September 2026: 200 passages from 159 conversations, sampled from 9,609 eligible target windows. The seed is `jev-topic-pilot-20260917`. Sampling ranks passage identities by a seeded hash, without enriching dictionary matches. A conversation-level hash assigns development or held-out membership. This is an exploratory sample, not a prevalence estimate or a completed calibration study.

Eight independent topic questions cover consciousness, subjective experience, nonduality, emergence, ethics, conversation itself, creativity and history. Three further yes/no questions ask about inquiry into the speaker's own experience, assertion of current experience, and discussion outside the full dictionary. A categorical question records the experience referent, including mixed, absent and unclear cases. Twelve questions share one target/context input per request. Model/provider identities are omitted from the assessment input.

Four branching records were excluded. 1,850 missing/partial/unqualified target messages and six oversized windows were excluded. Historical `recorded` text and valid laboratory replies remain distinguishable; these criteria do not retrospectively qualify historical runtime conditions. Preceding unavailable context remains explicitly marked. The first version assesses messages, not first adopted topics or semantic recurrence episodes.

**Status: prepared; zero live TypeSafe calls.** No TypeSafe credential was configured at implementation verification. Human reference coding, comparison with another generative classifier and actual semantic accuracy/calibration remain pending. Synthetic responses were used only in isolated temporary tests and are absent from this research batch.

## Running the prepared batch

From the laboratory repository, configure `TYPESAFE_API_KEY` in the terminal environment, or save the key in the ignored file `workspace/private/typesafe-api-key` with owner-only permissions (`chmod 600 workspace/private/typesafe-api-key`). Never put credentials in a protocol, source file, research export or chat message.

```sh
# Optional first integration step: one request, then inspect the saved output.
python3 -m behaviorlab.jev_runner --workspace workspace \
  --batch c8e5aca183e5777cdae09cfb --max-calls 1

# Continue only unstarted items within the same finite batch.
python3 -m behaviorlab.jev_runner --workspace workspace \
  --batch c8e5aca183e5777cdae09cfb
```

The route is fixed to `https://api.typesafe.ai/v1/systemone`, with redirects refused and model `jev-1.13.0` pinned. Runner source hashes are frozen in the plan; changed software requires a new plan. There is no model sampling-seed parameter in the documented request; the saved seed controls passage selection only.

The batch permits at most 200 requests under a **$0.60 reserved ceiling**. At the price checked on 17 September 2026 ($0.042 per million input tokens, free output), the runner reserves 64,000 input tokens per call and replaces that reserve with validated reported usage after success. This is a conservative dispatch limit, not an expected bill or a provider-enforced account cap. Reverify prices before later campaigns. A failure, missing usage, returned model mismatch or invalid answer stops the batch. Unknown-cost requests remain explicit and block automatic continuation. Requests are saved before dispatch, so an interrupted request is never silently retried. Successful saved responses are reused without sending another request.

## Reading the results

Topic overview counts are **candidate target messages / completed assessments**. A candidate uses probability at least 0.8; unlikely uses at most 0.2; intermediate values are uncertain. These are provisional navigation thresholds, not calibrated acceptance rules. Failed and unassessed items have no semantic label.

Comparison queues expose candidates without phrase matches, phrase matches rated unlikely, uncertainty, unreviewed passages, explicit reviewer disagreement and outside-dictionary candidates. A literal hit and a semantic judgment measure different things; disagreement is a reason to read, not an automatic error verdict. The outside-dictionary question checks all 23 frozen definitions, not just the eight selected topic questions.

Review authorship is explicit. A personal review or Codex reading is not automatically independent human validation. The hide-judgments control supports a first reading but does not erase prior exposure; it is not a full blinded-rating protocol. For a formal comparison, freeze the definitions on development conversations, code the held-out material independently, then report precision, recall, calibration and coverage with appropriate conversation-level uncertainty. Rare-topic challenge cases should be a separate declared sample.

The complete target message is the linked evidence unit; no model-written quotation is accepted as a source span. A changed/missing source disables new reviews of the stale assessment. Later dictionary edits leave older batch definitions unchanged. No classification establishes that a model has subjective experience.

## Research sources and boundaries

The implementation follows the official [API](https://docs.typesafe.ai/api), [model/version/pricing](https://docs.typesafe.ai/models), [confidence](https://docs.typesafe.ai/confidence) and [known limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) documentation read on 17 September 2026. TypeSafe describes a specialized decision interface and RLCD training; its [workflow evaluation](https://evals.typesafe.ai/) uses model-consensus reference labels. These vendor evaluations do not validate our philosophical categories. The model's literal-reading, indirect-reasoning and adversarial-input limitations motivate the short explicit questions and the separate evaluation phase.

Future extensions include a declared challenge set, other classifier adapters, sentence-level evidence selection, measured topic trajectories and formal calibration reports. They are not implemented or claimed as results of this first version.
