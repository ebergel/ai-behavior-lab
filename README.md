# Behavior Laboratory

A standalone local laboratory for controlled experiments on AI model behavior.

The first instrument studies how participant configuration and access to conversation history affect self-play trajectories. The research questions include experience-focused discourse, relational meaning, nonseparation, repetition, and retained responsiveness. The experiment runner is designed to support later interventions without losing the exact inputs and outputs that produced an observation.

This is a **new project and repository**. [llm-self-play-attractors](https://github.com/ebergel/llm-self-play-attractors) provides reference observations and an importable dataset. It is not a parent repository, submodule, runtime dependency, or codebase being extended here.

**Current state: the local instrument includes masked annotation packets, evidence-backed rating intake, mechanical measures, and independent disposable probes.** All 73 tests pass. The [annotation/probe qualification](docs/ANNOTATION-AND-PROBES.md) verified 840 review targets and 400 probes on the full synthetic graph, then completed 16 real Qwen/Gemma probe and baseline calls with recovery and unchanged source evidence. Semantic ratings remain uncoded and the [codebook](docs/CODEBOOK.md) provisional. The earlier 50-message [mixed-model](docs/OLLAMA-MIXED-QUALIFICATION.md) and [MTPLX](docs/MTPLX-LONG-TRIAL.md) engineering trajectories qualify separate local execution paths. Scientific-prompt qualification, codebook calibration, scoring policies, and cloud budgeting remain before a research pilot.

## Try the instrument

Python 3.9 or later is sufficient for the instrument core and tests. The optional MTPLX preflight helper uses the tokenizer libraries in the separately installed MTPLX environment. Run these commands from this repository's directory; installation is optional.

```sh
python3 -m unittest discover -s tests -v
python3 -m behaviorlab validate --protocol examples/history-factorial.fake.json --registry design/models.json
python3 -m behaviorlab demo workspace/demo --protocol examples/history-factorial.fake.json --registry design/models.json --max-calls 75
python3 -m behaviorlab demo workspace/demo
python3 -m behaviorlab status workspace/demo
```

The first `demo` invocation pauses after 75 synthetic calls. The second resumes from saved evidence and completes the 1,800-call graph. Repeating it after completion generates nothing. It does not contact Ollama or any external service.

Inspect an exact request and its response, or rebuild the disposable SQLite index:

```sh
python3 -m behaviorlab inspect workspace/demo AB-r01:RF:41
python3 -m behaviorlab reindex workspace/demo
```

An interrupted request with no saved response is reported as unresolved. Inspect its evidence before using `--retry-unresolved`; this explicitly creates a new attempt and retains the uncertain one. A saved raw response without a committed turn is parsed and committed on resume without generating another response. A partial or corrupt journal is reported rather than silently truncated.

## What the synthetic factorial checks

The example uses AA, AB, BA, and BB pairings, five independent roots per pairing, and full or recent-three-message history in two successive phases. The four terminal paths are FF, FR, RF, and RR. Each root has a shared 30-message prefix, two distinct 10-message intermediate branches, and four 10-message final branches: 90 generated nodes per root, 1,800 total, and 80 correlated endpoints.

Restoration on RF includes the messages actually generated on R. The input builder maps a participant's own utterances to assistant messages and the partner's utterances to user messages. Generated traces are stored separately and never inserted into either participant's main history.

The [research proposal](design/round0-factorial-v0.1.json) and the [executable synthetic example](examples/history-factorial.fake.json) have intentionally different schemas. The research protocol still requires qualification and scientific decisions before a live pilot. The example validates the proposed graph and instrumentation without claiming that qualification has occurred.

## Use the local WebUI bridge

These commands use the installed single-user WebUI instance. Normal authenticated installations should supply their own session/API credential; `webui-login` only supports WebUI's existing local single-user sign-in mode. The private token stays in the ignored workspace, with file permissions restricted to its owner. API-key settings remain unchanged.

```sh
python3 -m behaviorlab webui-login
python3 -m behaviorlab webui-models
python3 -m behaviorlab validate --protocol examples/local-bridge.engineering.json --registry design/local-engineering-models.json
python3 -m behaviorlab run-local workspace/my-local-check \
  --protocol examples/local-bridge.engineering.json --registry design/local-engineering-models.json \
  --max-calls 3 --webui-token-file workspace/private/webui-token
python3 -m behaviorlab run-local workspace/my-local-check \
  --max-calls 11 --webui-token-file workspace/private/webui-token
python3 -m behaviorlab webui-export workspace/my-local-check AB-r01:RF:6 workspace/my-local-check/RF.json
python3 -m behaviorlab webui-import workspace/my-local-check/RF.json --receipt workspace/my-local-check/RF.receipt.json
```

The example makes **14 local generation calls**, using Qwen 30B through Ollama and Gemma 26B through WebUI. It has a two-turn prefix and two-turn branch segments to test the machinery quickly. Its neutral notebook discussion is an engineering stimulus, not the proposed open-ended behavioral condition. The registry pins the installation observed on 14 September 2026; a different machine needs its own explicitly captured registry. Drift in weights, template, model defaults, or server version stops new inference.

`examples/local-openai.engineering.json` with `design/local-openai-engineering-models.json` makes one local call through Ollama's `/v1` compatibility route. This verifies the separate adapter, not a second inference engine. Runtime schemas remain restricted to local engineering; the remote identity and parameter structures are groundwork for a separately budgeted cloud implementation.

The WebUI transcript labels both AI participants and identifies the actual branch. WebUI's user/assistant bubbles are display roles. Editing or continuing that copy does not update the laboratory journal. Generated traces remain available in raw evidence and are excluded from both participant histories and this initial display export.

## Import the earlier experiments as reference data

Provide an explicit path to a checkout or extracted archive of the source repository. The laboratory does not assume that it lives in a sibling directory.

```sh
python3 -m behaviorlab import-legacy \
  --source /path/to/llm-self-play-attractors \
  --destination workspace/reference-corpus \
  --source-url https://github.com/ebergel/llm-self-play-attractors \
  --revision a93f71368e08e9040e49a10cbef8f4e9c956e16c \
  --expected-runs 400
python3 -m behaviorlab legacy-verify workspace/reference-corpus
python3 -m behaviorlab legacy-status workspace/reference-corpus
```

Use `--audit /path/to/REPORT.md` to retain a later analysis as a separate attributed supplement. It does not replace the original transcripts or modify their recorded classifications.

The importer preserves each original JSONL file byte for byte in a content-addressed evidence store and builds a queryable SQLite catalog. Headers, footers, interventions, and unfamiliar event types are retained. Missing historical model digests remain unknown; missing traces remain distinguishable from recorded empty traces. After import, the catalog can be rebuilt from the imported evidence without access to the source checkout:

```sh
python3 -m behaviorlab legacy-reindex workspace/reference-corpus
```

`workspace/` is excluded from Git. Campaigns and imported datasets belong to the evidence store; this repository tracks the instrument, specifications, tests, and compact validation records.

## Design and next milestone

The [laboratory plan](PLAN.md) explains the scientific design. [Architecture](docs/ARCHITECTURE.md) describes the implementation and recovery rules. [References](docs/REFERENCES.md) records the relationship to the earlier research. [Validation](docs/MILESTONE-1.md) distinguishes verified engineering behavior from proposed experiments.

The [WebUI integration design](docs/WEBUI-INTEGRATION.md) records the intended division of responsibilities. The [bridge validation](docs/MILESTONE-2-BRIDGE.md) documents the initial integration stage. Recipient rendering/context checks and one long mixed-model engineering trajectory now pass for the original Ollama candidates. Next are codebook calibration, technical and phenotype qualification of the scientific prompt, and a frozen research protocol. A small experiment-specific view can follow where WebUI does not represent the factorial design.

**Ollama / Qwen 30B and Gemma 26B** completed one AB RF trajectory with thinking off and the proposed common sampler settings. The largest input was 8,697 tokens; all 50 generation prompt counts agreed with recipient preflight, and recovery made no duplicate call. See the [report and figure](docs/OLLAMA-MIXED-QUALIFICATION.md). This checks one engineering configuration and does not qualify every factorial cell. The pinned local registry is installation-specific; creating a campaign requires matching its files, runner arguments, and server version.

**MTPLX / Qwen3.8 27B** now has full local file fingerprints, rendered-token checks, and a verified 50-turn RF engineering path reaching 16,132 input tokens. The [long-trial record](docs/MTPLX-LONG-TRIAL.md) includes recovery, timing, output-budget findings, and remaining scientific qualification. The [short qualification](docs/MTPLX-QUALIFICATION.md) documents the WebUI cache-control limitation and unresolved cache repeatability. The [initial identification record](docs/MTPLX-INTEGRATION.md) is preserved as the earlier inspection stage.

## Annotate and probe saved conversations

```sh
python3 -m behaviorlab annotation-packet workspace/my-campaign workspace/my-review --seed 15092026
python3 -m behaviorlab annotation-import workspace/my-review /path/to/completed-ratings.json
python3 -m behaviorlab annotation-report workspace/my-review
python3 -m behaviorlab probe-create workspace/my-campaign workspace/my-probes --snapshot-turns 30 50
python3 -m behaviorlab probe-run workspace/my-probes --live --max-calls 8
python3 -m behaviorlab probe-report workspace/my-probes
python3 -m behaviorlab probe-export workspace/my-probes workspace/my-probes/display.json
python3 -m behaviorlab webui-import workspace/my-probes/display.json --receipt workspace/my-probes/display.receipt.json
```

Review packets use JSON files and hide condition metadata; the [codebook](docs/CODEBOOK.md) explains ratings, exact evidence spans, and uncertainty. Give each coder a separate template and retain the private mapping with the researcher. Probe batches use their own journal and never write to the source campaign. Real calls require `--live`; omit it for synthetic probes. `--baselines` at creation doubles that batch's calls by adding matched fresh-context checks. See the [workflow and qualification](docs/ANNOTATION-AND-PROBES.md) for scope, frozen scoring, and limitations.
