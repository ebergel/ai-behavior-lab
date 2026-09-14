# Instrument architecture

The instrument is independent of the source experiment repository. Python's standard library provides the core and local HTTP adapters; the optional MTPLX tokenizer uses its installed runtime. Open WebUI displays exported transcripts. The initial synthetic design is described first, followed by the live integration extensions.

| Module | Responsibility |
|---|---|
| `protocol.py` | Validate versioned protocols and model registries; freeze snapshots; compile ordered roots and a branch graph into generation nodes. |
| `history.py` | Follow immutable parent links and construct the receiving participant's full or restricted API history. |
| `journal.py` | Enforce a single writer; append and synchronize evidence records; verify sequence and hash integrity; rebuild a SQLite index. |
| `runner.py` | Execute a deterministic fake backend, retain raw response text, commit parsed turns, resume or report uncertain attempts, and account for invalid descendants. |
| `legacy.py` | Import original JSONL bytes, preserve unknown/missing fields, attach optional analysis supplements, and build/rebuild a catalog. |
| `cli.py` | Expose validation, synthetic campaigns, evidence inspection, and corpus import/verification. |

## Identities and immutable state

A protocol uses schema `behaviorlab.protocol/1` and refers to a registry's canonical SHA-256 fingerprint. The registry uses `behaviorlab.models/1`; model records contain the observed tag, full artifact digest, archived template and its checksum, defaults, and provenance. The tag alone is not the model identity.

Protocol and registry objects retain canonical JSON strings plus frozen dataclasses and tuples. Caller-owned dictionaries cannot mutate a running snapshot. The campaign header embeds both complete snapshots, so later files or external directories are unnecessary for resuming it. It also records software, parser, backend, and data-class versions.

Each node is identified by root, segment, and global turn. A single parent link identifies the previous actual message. Shared prefixes exist once. Sibling histories do not share mutable lists. RF extends R; it cannot accidentally restore F's counterfactual utterances.

Full history contains the unchanged system prompt, X's original opening cue in X's view, and actual ancestor messages. Restricted history contains the system prompt and the last three participant messages. The projection preserves empty content exactly, remaps roles for the current recipient, and excludes all generated trace fields.

Model comparison in this version is a comparison of pinned configurations including their templates. The archived Gemma template is a placeholder, so complete rendering provenance also requires the inference runtime and accessible tokenizer metadata at the next milestone.

## Evidence before interpretation

The journal is `events.jsonl`. Every event has a sequence number, UTC timestamp, event type, payload, previous-event hash, and content hash. A request event includes its exact payload, hash, seed within the payload, model fingerprint, parent, root, segment, global turn, speaker, and history policy.

The write order is:

1. Save the request and synchronize the journal to disk.
2. Invoke the backend.
3. Save the complete raw response string and synchronize it.
4. Parse it using the recorded parser version, then commit a valid turn or record an invalid outcome.

Hash chains detect accidental corruption and sequence changes; they are not signatures proving who authored the data. Filesystem synchronization and injected interruption tests do not constitute a guarantee against every hardware or filesystem failure. A partially written final line is detected and preserved for explicit recovery.

`index.sqlite` is disposable. Its rows contain indexed journal events, and its identity table records the source event count and head hash. Rebuilding replaces it atomically from a verified snapshot while holding the journal writer lock. The implementation targets macOS/Linux using POSIX file locking.

## Recovery and technical outcomes

| Saved evidence | Resume behavior |
|---|---|
| Committed turn | Reconstruct and verify its request and parsed outcome; reuse it. |
| Raw response, no committed turn | Parse and commit it without inference. |
| Request, no raw response | Report uncertainty. An explicit retry flag records authorization and creates a new attempt. |
| Backend exception | Preserve the error and pause. Explicit retry retains the failed attempt. |
| Output cap, malformed response, or detected context truncation | Record an invalid node; block descendants; continue independent graph portions. |
| Unexpected separate thinking output when thinking is off | Preserve raw evidence and invalidate the branch under the strict synthetic protocol. |
| Empty content with normal completion | Retain and continue; it is not replaced or interpreted as an exit. |
| Literal `[END]` in this closed protocol | Retain as content; no semantic stopping rule is enabled. |

The backend always identifies itself as `deterministic-fake/1`, and every campaign identifies its data as a synthetic engineering fixture. The API-shaped responses make journaling and parsing testable without contacting an inference server. Estimated token counts are not invented for these fixtures.

The next adapter must add actual backend timing, model identity checks, template/mode qualification, recipient-specific context bounds, and operational decisions for failures under live inference. It must not simply enable a network switch on an unqualified research proposal.

## Imported reference corpus

The importer reads explicitly supplied `data/runs`, `data/runs2`, and `data/runs3` directories. It validates header/footer framing, paired-message counts, and speaker order; it retains every record type. The source checkout is never written to.

The import directory holds a manifest, content-addressed raw blobs, and a rebuildable `catalog.sqlite`. A dataset fingerprint covers source URL/revision, file paths and hashes, counts, and optional supplements. Re-importing identical evidence at the same destination is idempotent; different evidence is rejected there.

SQLite indexes original headers and footers, all records, source line numbers, and selected query fields. Complete original file bytes remain authoritative. `thinking_present` distinguishes an absent field from a recorded empty/null field. Model fingerprints are only populated if the source recorded them; the current registry is never used to fill historical gaps.

An audit is stored as a separately identified supplement. Its interpretations do not rewrite the original data. A rebuilt import works after the original source checkout is removed, which preserves the boundary between the new laboratory and the earlier study.


## Version 2 integration bridge

Runtime registry/protocol v2 adds local engineering execution while preserving v1 synthetic histories and hashes. `backends.py` owns capability validation, explicit request mapping, HTTP transport, artifact observations, and response parsing. `runner.py` retains the same durable request/response/outcome sequence for both backend classes. Credentials are resolved from environment variables at dispatch and are excluded from protocol/journal payloads. Original response bytes and HTTP metadata accompany live raw responses.

`webui.py` implements supported single-user session authentication, catalog discovery, and display-only export/import of one actual branch ancestry. Import receipts prevent automatic duplication after an uncertain outcome. The existing WebUI is the transcript reader; the laboratory remains the authoritative evidence store. Local gateway campaigns currently require an identified Ollama artifact. Cloud execution, rendered-context qualification, and research annotations remain unimplemented; see [current validation](MILESTONE-2-BRIDGE.md).


## MTPLX qualification extension

`mtplx.py` verifies a full local artifact manifest and selected runtime source/package fingerprints, checks effective server settings, renders recipient-specific input through an optional local tokenizer helper, and validates MTPLX engine captures against the intended tokens and controls. This helper uses the separately installed MTPLX environment; the core and tests remain standard-library Python. Unsupported settings are rejected and oversize rendered requests stop before generation. Captured reasoning remains separate from visible conversation content.

Direct and WebUI MTPLX routes require the generation destination to match the verified local engine. WebUI strips the metadata used for MTPLX cache bypass; its tested route requires caching enabled. Observed cache hits preserved rendered inputs but sometimes changed seeded output, so the initial controlled baseline uses direct cache-bypassed requests. The earlier Ollama-only gateway restrictions above describe the initial bridge stage. See [the current qualification](MTPLX-QUALIFICATION.md) for measured scope and unresolved work.

## Final generation controls and parser history

MTPLX's dispatch capture can contain the requested output allowance even when its generator later applies a lower server cap. Parser `http-chat/2` checks the final effective allowance and clamp flags, sampling values, generation mode/depth, seed/retry counts, and cache usage as well as the captured input. Preflight rejects a requested allowance above the pinned server cap before tokenization or generation. The [long-trial record](MTPLX-LONG-TRIAL.md) documents the discrepancy that exposed this gap.

Campaigns retain their original parser version. Parser-1 evidence can still be replayed and exported, but new inference from those campaigns is blocked. `scripts/reassess_mtplx_parser.py` evaluates saved responses under the current contract in a separate report, preserving the original journal bytes and outcomes. This makes a corrected interpretation distinguishable from the instrument's historical decision.

The client HTTP deadline is independently configurable through `run-local --request-timeout` and is recorded in transport evidence. It is not sent as a generation parameter. Increasing that deadline does not change the model's output allowance or the server's context limit. Received responses survive supplemental-capture failures; an unresolved request still requires explicit retry authorization.
