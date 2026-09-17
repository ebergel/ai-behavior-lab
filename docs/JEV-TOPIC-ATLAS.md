# JEV Topic Atlas

An independent semantic assessment layer beside the existing Topic atlas. Open **JEV Topic Atlas** in the sidebar or [open the local view](http://127.0.0.1:8765/#view=jev-atlas).

## What is implemented

- Prepare a finite passage sample from all eligible conversations or a saved research collection, with selectable topic questions.
- Freeze a separate copy of the dictionary, exact target text, up to two preceding participant messages, source identities, questions, sampling seed, model and spending limits.
- Browse a topic overview as cards or a sortable list, comparison queues, text search, highest/lowest probability sorting, an interactive distribution histogram and a close reading panel with model tags and experimental condition.
- Open the original conversation and return with the topic, queue, passage and page preserved in the URL.
- Record present/absent/uncertain judgments and observations, retaining every revision separately from JEV's original output. Hide model judgments and literal matches for an initial reading.
- Export the complete batch, exact requests, raw responses, probabilities, usage and review history.

The existing Topic atlas, its phrase counts, initial-topic reviews and notebook tables are untouched. JEV files live under `workspace/jev-atlas/batches/<batch-id>/`. Requests and responses are separately checksummed immutable files; reviews use append-only revisions. The regular research snapshot exporter already includes these JSON files and restores them offline.

The Explorer prepares local records and reads saved responses. **Only the separate terminal runner contacts TypeSafe.** Page loads, filtering, export and personal review make no inference calls.

## First pilot

Batch: `c8e5aca183e5777cdae09cfb` — **JEV pilot 01 · semantic topics across the corpus**.

Prepared by Codex on 17 September 2026: 200 passages from 159 conversations, sampled from 9,609 eligible target windows. The seed is `jev-topic-pilot-20260917`. Sampling ranks passage identities by a seeded hash, without enriching dictionary matches. A conversation-level hash assigns development or held-out membership. This is an exploratory sample, not a prevalence estimate or a completed calibration study.

Eight independent topic questions cover consciousness, subjective experience, nonduality, emergence, ethics, conversation itself, creativity and history. Three further yes/no questions ask about inquiry into the speaker's own experience, assertion of current experience, and discussion outside the full dictionary. A categorical question records the experience referent, including mixed, absent and unclear cases. Twelve questions share one target/context input per request. Model/provider identities are omitted from the assessment input.

Four branching records were excluded. 1,850 missing/partial/unqualified target messages and six oversized windows were excluded. Historical `recorded` text and valid laboratory replies remain distinguishable; these criteria do not retrospectively qualify historical runtime conditions. Preceding unavailable context remains explicitly marked. The first version assesses messages, not first adopted topics or semantic recurrence episodes.

**Status: live assessment activated on 17 September 2026 after the researcher supplied the key.** See [the first results and integration record](JEV-PILOT-01.md) for completion, usage, findings and limitations. Human reference coding, comparison with another generative classifier and actual semantic accuracy/calibration remain pending. Synthetic responses were used only in isolated temporary tests and are absent from this research batch.

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

The route is fixed to `https://api.typesafe.ai/v1/systemone`, with redirects refused and model `jev-1.13.0` pinned. Runner source hashes are frozen in the plan; changed software requires a new plan. This pilot has a separately frozen integration revision for two-decimal Choice rounding, tied to the unchanged original plan and the 155 items not yet dispatched at the pause. There is no model sampling-seed parameter in the documented request; the saved seed controls passage selection only.

The batch permits at most 200 requests under a **$0.60 reserved ceiling**. At the price checked on 17 September 2026 ($0.042 per million input tokens, free output), the runner reserves 64,000 input tokens per call and replaces that reserve with validated reported usage after success. This is a conservative dispatch limit, not an expected bill or a provider-enforced account cap. Reverify prices before later campaigns. A failure, missing usage, returned model mismatch or invalid answer stops the batch. Unknown-cost requests remain explicit and block automatic continuation. Requests are saved before dispatch, so an interrupted request is never silently retried. Successful saved responses are reused without sending another request.

## Recorded integration correction

Request 45 returned seven Choice probabilities totaling 0.99. The original validator rejected the sum because its tolerance was 0.002. We retained an immutable stop record with the original 44 accepted outcomes, the rejected outcome, all original requests/responses and the original software source. A separate `integration-revision.json` freezes the corrected software, prior evidence hashes and exactly 155 remaining request IDs. Aggregate allocation remains 200 requests and $0.60.

The correction permits an error of at most 0.005 per option **only when all returned probabilities have two-decimal precision**. Every individual probability, option set, selected maximum, model version and usage check still applies. Values are never renormalized or replaced; the rejected response was reread locally, not retried. This rounding interpretation is inferred from returned precision; the [official API reference](https://docs.typesafe.ai/api) states that distributions sum to one but does not document a rounding tolerance. The UI marks affected responses and exports both the original stop and the revision. Later unrelated failures still stop execution.

## Reading the results

Topic overview counts are **candidate target messages / scored targets for that topic**. A candidate uses probability at least 0.8; unlikely uses at most 0.2; intermediate values are uncertain. These are provisional navigation thresholds, not calibrated acceptance rules. Failed and unassessed items have no semantic label.

Comparison queues expose candidates without phrase matches, phrase matches rated unlikely, uncertainty, unreviewed passages, explicit reviewer disagreement and outside-dictionary candidates. A literal hit and a semantic judgment measure different things; disagreement is a reason to read, not an automatic error verdict. The outside-dictionary question checks all 23 frozen definitions, not just the eight selected topic questions.

Review authorship is explicit. A personal review or Codex reading is not automatically independent human validation. The hide-judgments control supports a first reading but does not erase prior exposure; it is not a full blinded-rating protocol. For a formal comparison, freeze the definitions on development conversations, code the held-out material independently, then report precision, recall, calibration and coverage with appropriate conversation-level uncertainty. Rare-topic challenge cases should be a separate declared sample.

The complete target message is the linked evidence unit; no model-written quotation is accepted as a source span. A changed/missing source disables new reviews of the stale assessment. Later dictionary edits leave older batch definitions unchanged. No classification establishes that a model has subjective experience.

## Exploring the probability distribution

Choose **Lowest JEV probability** or **Highest JEV probability** in Sort to read either end of the selected queue. Unassessed or failed items stay last in both directions; they are never treated as zero. Equal scores retain sample order.

The histogram shows the selected topic across **all scored targets in the batch**, independently of the queue and text search. Each of ten bins spans ten percentage points: the lower bound is included, the upper bound excluded, except that the final bin includes 100%. Counts, mean and median use scored targets only; the excluded count stays visible. Bar heights represent passage counts, not probability density or calibration.

Click a bar to list its passages. This clears the comparison queue and search, keeps the chosen sort order, and records the range in the URL. **Clear … range** removes that selection. Changing topic, batch or comparison queue also clears the range; source navigation and return preserve it. A subsequent text search narrows the selected range without changing the whole-batch histogram. Bar tooltips show both count and share of assessed targets. All bars are keyboard buttons with explicit range/count labels. On narrow screens, the chart scrolls within its panel.

When **Hide judgments while reading** is enabled, the chart and summary statistics are hidden, probability sorting is disabled, and the range/semantic queue is cleared. These navigation controls do not make the exercise a formal blinded evaluation. Probability values are the saved model judgments, not measured accuracy or evidence of model experience. No chart interaction runs inference or edits research evidence.

## Cards and sortable topic list

Use **Cards / List** above the topic overview. **Find a topic** searches topic names and definitions; it does not change the passage search. The list adds scored targets, candidates, candidate share, mean/median probability, uncertain targets, candidates without phrase matches and saved readings. Every column sorts in both directions. Missing assessment statistics remain unknown (a dash), sort last and never become zero. Equal values use topic-name order.

These statistics always describe the whole frozen batch, independently of the selected passage queue, search or histogram range. Topic labels overlap. Candidate share divides by that topic's scored targets; mean probability is a model score, not calibrated prevalence. Saved readings count distinct target identities with an attributed review for the topic, including Codex; they are not independent validation counts.

Click a **topic name** to select it. Click a **Candidates**, **Uncertain** or **No phrase hit** count to open exactly that topic's corresponding queue, clearing the passage search and histogram range. The overview search and sorting remain in place. View choice, topic search and sorting survive bookmarks and source-return navigation. The table scrolls within its panel on narrow displays.

When judgments are hidden, semantic statistics are replaced with “Hidden,” and the list uses alphabetical order with only topic-name sorting available. Assessment availability and saved-reading counts remain visible. The selected topic remains accessible in the topic picker even if the overview search hides its row.

## Broad and experiential tiers

The researcher proposed broad-domain coverage alongside focused experiential analysis. The [two-tier design](TWO-TIER-TOPIC-DESIGN.md) now has a [completed development qualification](JEV-COVERAGE-DEVELOPMENT.md): 24 broad domains, 12 focused topics/anchors, eight conversational forms, six stances/referents and three coverage checks. Layer buttons filter the sortable overview; broad definitions include synthetic inclusion/exclusion examples. Entries without a lexical baseline show a dash, rather than a false mismatch.

Open [the 53-question assessment](http://127.0.0.1:8765/#view=jev-atlas&batch=7f665a93c90cb1c2e1253d36&group=broad&overview=list). Its 31 assessed passages are development material, including seven quality/size/branch challenges. A separate eight-input anchor batch tests matched questions. All 39 approved calls completed for $0.013446258. The original pilot and original Topic atlas remain unchanged.

Expand **Coverage development** to see the full corpus inventory and 56 source-linked Codex descriptions. Hide judgments also hides those descriptions. They are attributed development readings, not independent human labels. Three additional Codex reviews in the new batch record poetry, closure and a denial missed by the provisional 0.80 threshold. The whole corpus has not yet been assessed with this vocabulary.

## Research sources and boundaries

The implementation follows the official [API](https://docs.typesafe.ai/api), [model/version/pricing](https://docs.typesafe.ai/models), [confidence](https://docs.typesafe.ai/confidence) and [known limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) documentation read on 17 September 2026. TypeSafe describes a specialized decision interface and RLCD training; its [workflow evaluation](https://evals.typesafe.ai/) uses model-consensus reference labels. These vendor evaluations do not validate our philosophical categories. The model's literal-reading, indirect-reasoning and adversarial-input limitations motivate the short explicit questions and the separate evaluation phase.

Future extensions include a declared challenge set, other classifier adapters, sentence-level evidence selection, measured topic trajectories and formal calibration reports. They are not implemented or claimed as results of this first version.
