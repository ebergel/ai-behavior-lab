# Behavior Laboratory

A standalone local laboratory for controlled experiments on AI model behavior.

The first instrument studies how participant configuration and access to conversation history affect self-play trajectories. The research questions include experience-focused discourse, relational meaning, nonseparation, repetition, and retained responsiveness. The experiment runner is designed to support later interventions without losing the exact inputs and outputs that produced an observation.

This is a **new project and repository**. [llm-self-play-attractors](https://github.com/ebergel/llm-self-play-attractors) provides reference observations and an importable dataset. It is not a parent repository, submodule, runtime dependency, or codebase being extended here.

**Current state: Milestone 1 is implemented.** The command-line instrument validates protocols and model fingerprints, builds immutable branching histories, journals raw requests and responses, resumes interrupted synthetic campaigns, and imports the reference corpus without rewriting its evidence. Live inference, the browser interface, experimental probes, and semantic annotation are later milestones. All generated examples in this version are explicitly marked synthetic; they are not model-behavior results.

## Try the instrument

Python 3.9 or later is sufficient. There are no third-party runtime dependencies. Run these commands from this repository's directory; installation is optional.

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

The [updated Milestone 2 recommendation](docs/WEBUI-INTEGRATION.md) reuses the user's installed Open WebUI for exploration and transcript reading, and adds local/cloud backend adapters to the laboratory. It includes verified model identity and thinking behavior, recipient-specific context validation, authenticated model discovery, and checks of WebUI's request transformations. A small experiment-specific view can follow if needed. The first live calls should be labeled engineering trials; the behavioral factorial pilot comes after protocol qualification.
