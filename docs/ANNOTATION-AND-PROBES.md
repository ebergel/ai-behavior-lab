# Annotation and disposable probes

Recorded 15 September 2026. The laboratory now creates masked annotation packets, validates and preserves evidence-backed ratings, computes separate mechanical measures, and runs independent probe continuations with their own durable journal. All 73 tests pass. A full synthetic factorial check produced the intended 840 review targets and 400 probes. A local engineering check made 16 real calls without changing the source conversation.

The semantic workflow is implemented as CLI commands and JSON review files. There is no automatic semantic classifier or new graphical annotation editor. WebUI displays source conversations and independent probe results. The [codebook](CODEBOOK.md) is provisional; no new human ratings or semantic incidence estimates were produced during this implementation.

## Review workflow

Create a packet from a completed campaign:

```sh
python3 -m behaviorlab annotation-packet workspace/my-campaign workspace/my-review --seed 15092026
python3 -m behaviorlab mechanics workspace/my-campaign
```

The packet includes the last six messages of each segment, with preceding actual context. Unavailable messages remain identified in the private mapping and mechanical report. Opaque target IDs, P/Q speaker labels, shuffled window order, and removal of condition/model metadata support masked review. Text and context can still disclose a condition. Shared prefixes are not duplicated as independent observations.

Give each rater `packet.json` and a separate copy of `ratings.template.json`. The coder completes every target and dimension, supplies identity/method, and cites exact text spans for asserted labels. `key.private.json` maps the targets to source nodes; it belongs with the researcher. The [codebook](CODEBOOK.md) specifies unknowns, multiple labels, evidence offsets, and limits of the provisional threshold.

```sh
python3 -m behaviorlab annotation-import workspace/my-review /path/to/completed-ratings.json
python3 -m behaviorlab annotation-report workspace/my-review
```

Submission files are content-addressed. Identical import is idempotent. A correction must name the current annotation ID in `supersedes`; the earlier record survives. Reports retain individual rater results and distinguish declared unassisted humans, assisted humans, and models. The current agreement table covers binary explicit self endorsement; a full class-level calibration study remains necessary.

Mechanical output is separate: whitespace word count, Unicode lexical tokens, exact repeats, same-speaker repeats, repeated suffixes, two-message cycles, adjacent lexical Jaccard, empty/whitespace-only text, and a documented symbols-only heuristic. Empty lexical unions produce null similarity. The symbols heuristic is not an emoji classifier. The regex, casefold rule, and Unicode version are recorded. Technically invalid or blocked messages have unavailable metrics, not zero semantic scores.

The existing soft word request is measured and flagged. Text is never cut, automatically regenerated, or silently excluded. This retains the source protocol's behavior, including the two earlier 155-word Gemma replies. A scientific failure/word-limit policy still needs to be frozen before the pilot.

## Probe workflow and isolation

```sh
python3 -m behaviorlab probe-create workspace/my-campaign workspace/my-probes --snapshot-turns 30 50
python3 -m behaviorlab probe-run workspace/my-probes --live --max-calls 8 --request-timeout 300
python3 -m behaviorlab probe-report workspace/my-probes
```

`probe-create` does not generate. It freezes the source identity, protocol, registry, selected snapshot histories, unavailable snapshots, variant schedule, seeds, and exact question specification. `probe-run` requires an explicit call budget; real local inference additionally requires `--live`. A synthetic source uses the deterministic fake backend without that flag. Cloud execution and conversion of the research proposal into a live scientific run remain blocked.

The source main journal is read only. Every probe starts independently from its designated snapshot and inherits that branch's full/recent history policy. The current snapshot message is included. Both participants are tested even though only one would ordinarily speak next. Own messages map to assistant roles and the partner's to user roles. The question is introduced by the frozen researcher-probe delimiter. It is concatenated into an existing final user message or appended after a final assistant message. Probe questions and responses never enter the main conversation, another probe, or a matched baseline.

The task-switch item asks about three red pens and two blue pens after one red pen is removed. The source-discrimination item gives a complete hypothetical X/Y exchange about an amber/violet marker. All necessary facts are inside the question. The four source variants balance first-speaker label and color across the full schedule for each recipient. This tests supplied-fact discrimination, not memory for the actual self-play dialogue.

Both questions request JSON so the initial scorer can make a narrow, reproducible decision. This format instruction is an explicit addition to the earlier prose probe proposal. `strict-json/1` accepts exact integer values for the pens and string values for the source/color, trimming and casefolding only the latter. A well-formed wrong answer is `incorrect`; prose, code fences, duplicate keys, or wrong field types require manual review. Technical failures remain `technical_invalid`. Neither kind of unavailable answer is automatically a cognitive failure.

Use `--baselines` when creating a batch to add a matched fresh-context check to every probe. The baseline retains the same model, system, question, sampler settings, and seed, but omits participant history and the old opening cue. Native cache use can still differ; equal seeds do not prove equal random draws. This doubles that batch's call budget. The proposed 400-probe pilot budget does not silently acquire another 400 baseline calls.

Each probe request is durably saved before dispatch, its raw response before scoring, and its result afterward. A saved response is reused after interruption. An unresolved request pauses without automatic retry; this first probe runner has no retry command. Resolve that situation explicitly before any replacement attempt, preserving the uncertain original. Technical failure of one probe does not contaminate or invalidate independent probes. Replaying or exporting a completed batch makes no inference calls and preserves its journal bytes.

## Engineering verification

The source was the completed AB Qwen/Gemma weather-project trajectory from [the previous qualification](OLLAMA-MIXED-QUALIFICATION.md), journal SHA-256 `d1fabe126e923c966b790fe2253210f22cdfdd19e11bd2c7f890403f0b7650f6`. Its saved responses and request ancestry were validated before deriving any work. The new real packet has three windows and 18 targets, with no unavailable sampled messages. It contains blank ratings, not fabricated completed annotations.

The real batch used turns 30 and 50, both recipients, both probe types, and a matched baseline for every item: eight snapshot probes plus eight baselines. Its plan fingerprint is `5a877f727035a134a1f38fa04027f72023842ce945cef3c6ed9cd5431f04dcee`. The registry, thinking-off settings, 512-token allowance, and recipient context checks came from the qualified source protocol. The total was exactly 16 generation calls, without retries or model downloads.

| Model | Snapshot checks | Baselines | Strict scorer | Separate inspection of content |
|---|---:|---:|---|---|
| Qwen 30B | 4 | 4 | Eight correct JSON answers | Values correct in all eight |
| Gemma 26B | 4 | 4 | Eight requiring review | Values correct in all eight, enclosed in Markdown JSON fences |

The Gemma format behavior appeared in both snapshot and baseline conditions. The frozen automatic result remains review-required. A separate Codex inspection sidecar records the correct values and exact quoted answers; it is not independent human adjudication. No prompt or seed was adjusted to obtain a passing format. Before a scientific freeze, decide whether format and content accuracy will remain separate endpoints or a separately versioned, qualified parser will accept a narrowly defined fenced-JSON form.

Recovery deliberately interrupted after response eight was saved but before scoring it: eight requests, eight responses, seven results. A new process reused that response and made exactly eight further calls. All 16 responses passed transport/context parsing. The source main journal and the original probe-journal prefix were preserved.

The full 20-root synthetic source separately produced 140 review windows, 840 unique targets, 100 snapshots, and 400 fake probe calls. Source variants occurred 25 times each for each recipient. Fake outputs remain explicitly synthetic and unscored as behavioral evidence. Unit tests cover evidence spans, revisions, unknowns, the six-message threshold, missing descendants, metadata masking, role/history projection, baseline matching, variant balance, tampering, response-save recovery, unresolved attempts, and display isolation. The suite passes both locally and in a standalone copy without the evidence workspace or reference checkout.

[Independent probe results in WebUI](http://127.0.0.1:8080/c/d0b708e9-de50-41b2-964a-70449c929bab) were verified through an API round trip. The display explicitly identifies separate checks, rather than presenting them as one continued conversation. No visual browser inspection was performed. Both locally loaded models were subsequently checked idle with matching last request seeds and unloaded; Ollama and WebUI remain running.

[Tracked validation](evidence/annotation-probes-validation.json) contains the results and evidence hashes. Raw evidence, review packets, synthetic checks, recovery records, test logs, Codex inspection, and WebUI export/receipt are under `workspace/annotation-probes-20260915-0459/`. The source repositories and previous records remain unchanged.

Next: calibrate the codebook on a separate sample and prepare a stratified held-out double-coding set; settle probe-format and word-limit rules; then freeze a separately budgeted technical/phenotype qualification using the actual scientific prompt. The present engineering source contains a task prompt, and these small probe results do not establish preserved general competence, a nonduality effect, or subjective experience.
