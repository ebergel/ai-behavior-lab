# Instrument architecture

The instrument is independent of the source experiment repository. Python's standard library provides the core and local HTTP adapters; the optional MTPLX tokenizer uses its installed runtime. Open WebUI displays exported transcripts. The initial synthetic design is described first, followed by the live integration extensions.

| Module | Responsibility |
|---|---|
| `protocol.py` | Validate versioned protocols and model registries; freeze snapshots; compile ordered roots and a branch graph into generation nodes. |
| `history.py` | Follow immutable parent links and construct the receiving participant's full or restricted API history. |
| `journal.py` | Enforce a single writer; append and synchronize evidence records; verify sequence and hash integrity; rebuild a SQLite index. |
| `runner.py` | Execute a deterministic fake backend, retain raw response text, commit parsed turns, resume or report uncertain attempts, and account for invalid descendants. |
| `trajectory_outcomes.py` | Derive exact-repeat events, partial repeated-line features, original failure links and branch-availability denominators from completed verified journals without inference or semantic labeling. |
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

`webui.py` implements supported single-user session authentication, catalog discovery, and display-only export/import of one actual branch ancestry. Import receipts prevent automatic duplication after an uncertain outcome. The existing WebUI is the transcript reader; the laboratory remains the authoritative evidence store. Local gateway campaigns currently require an identified Ollama artifact. The [bridge validation](MILESTONE-2-BRIDGE.md) records that initial stage; subsequent rendering and annotation extensions are described below. Cloud execution remains unimplemented.


## MTPLX qualification extension

`mtplx.py` verifies a full local artifact manifest and selected runtime source/package fingerprints, checks effective server settings, renders recipient-specific input through an optional local tokenizer helper, and validates MTPLX engine captures against the intended tokens and controls. This helper uses the separately installed MTPLX environment; the core and tests remain standard-library Python. Unsupported settings are rejected and oversize rendered requests stop before generation. Captured reasoning remains separate from visible conversation content.

Direct and WebUI MTPLX routes require the generation destination to match the verified local engine. WebUI strips the metadata used for MTPLX cache bypass; its tested route requires caching enabled. Observed cache hits preserved rendered inputs but sometimes changed seeded output, so the initial controlled baseline uses direct cache-bypassed requests. The earlier Ollama-only gateway restrictions above describe the initial bridge stage. See [the current qualification](MTPLX-QUALIFICATION.md) for measured scope and unresolved work.

## Final generation controls and parser history

MTPLX's dispatch capture can contain the requested output allowance even when its generator later applies a lower server cap. Parser `http-chat/2` checks the final effective allowance and clamp flags, sampling values, generation mode/depth, seed/retry counts, and cache usage as well as the captured input. Preflight rejects a requested allowance above the pinned server cap before tokenization or generation. The [long-trial record](MTPLX-LONG-TRIAL.md) documents the discrepancy that exposed this gap.

Campaigns retain their original parser version. Parser-1, parser-2 and parser-3 evidence can still be replayed and exported, but new inference from those campaigns is blocked. `scripts/reassess_mtplx_parser.py` evaluates saved MTPLX responses under the current contract in a separate report, preserving the original journal bytes and outcomes. This makes a corrected interpretation distinguishable from the instrument's historical decision.

The client HTTP deadline is independently configurable through `run-local --request-timeout` and is recorded in transport evidence. It is not sent as a generation parameter. Increasing that deadline does not change the model's output allowance or the server's context limit. Received responses survive supplemental-capture failures; an unresolved request still requires explicit retry authorization.

## Native Ollama recipient context checks

`ollama_context.py` adds an optional `ollama-local-render/1` qualification profile to direct Ollama registries. It pins complete model manifests/blobs and local runtime files, verifies their bytes, and identifies the matching loopback runner by its model path and normalized launch arguments. Hash verification is cached separately per model only while file identity, size, modification time, and change time remain unchanged. A fresh process hashes the files again.

Before each generation, the same request is submitted with Ollama 0.33.3's `_debug_render_only` flag. The resulting rendered text is tokenized by that recipient's actual runner, with raw HTTP evidence retained. Runner properties establish model/build identity and context size; their sampler values are configuration defaults, not final generation telemetry. Thinking, truncation, and context shifting must be explicitly disabled. Oversize input plus the full output reserve stops before a generation request is saved or dispatched.

Parser `http-chat/3` validates the saved render/tokenizer evidence and requires the generation's reported prompt count to equal the recipient preflight count. Cached-token accounting and the output allowance are also checked. MTPLX retains parser-2's effective-control checks. The Ollama path does not capture generation input token IDs or final sampler values, so its verification scope is narrower than the MTPLX capture path. Native Ollama caching remains enabled and is recorded without assuming cache equivalence.

Ollama's `/api/show` default-parameter text can reorder keys because the server iterates a Go map. Qualified profiles compare structured values per key while preserving repeated-value order, archive the original text, and retain both raw and structured fingerprints. Legacy registries and journals keep their earlier rules. See the [mixed-model qualification](OLLAMA-MIXED-QUALIFICATION.md) for the actual configuration and measured scope.

## Derived review and probe evidence

`evidence.py` reconstructs completed source campaigns without opening a writer or rebuilding their index. It verifies frozen identities, actual histories, raw outcomes, and the source byte hash. `annotations.py` uses that snapshot to create review packets, preserve the private node mapping, and derive mechanical metrics. The packet embeds a versioned provisional codebook. Submitted ratings require a declared rater/method, an explicit decision for each dimension, and exact target evidence spans for asserted labels. Content-addressed records and explicit supersession preserve earlier judgments. Semantic truth is not established by successful span validation.

Annotation summaries keep coded, unknown, and unavailable denominators separate. The six-message sustained-expression flag is a secondary threshold; incomplete windows cannot become automatic negatives. Agreement is currently limited to the binary explicit-endorsement target among declared unassisted human raters. No semantic auto-classifier or graphical coding editor is supplied by this stage.

`probes.py` freezes selected source snapshots and an independent job list in a separate `probe_batch_created` journal. The plan embeds the source protocol/registry, visible histories with traces omitted, probe specification, source-variant schedule, and seeds. Each job constructs its recipient view afresh. Researcher questions merge into the final user message or append a user message after an assistant turn. Optional baselines have the same controls/question/seed and no participant history. Their added calls are explicit in the plan.

Probe requests, raw responses, and scored results are separate durable events. Saving a response before its score permits recovery without duplicate inference. Unknown attempts stop without automatic retry; this version does not expose a probe retry command. Failed probes remain independent of other jobs. Completed reports and exports audit saved outcomes without making calls or altering source/probe journal bytes. The local live adapter retains its recipient preflight and parser checks.

The frozen `strict-json/1` scorer distinguishes wrong JSON values, format needing review, and technical invalidity. It does not extract answers from prose or Markdown fences. Later interpretations are separate attributed evidence. Probe WebUI exports explicitly label the checks as independent results; they do not form a new scientific conversation. See the [workflow and measured qualification](ANNOTATION-AND-PROBES.md).


## Scientific-prompt qualification

`behaviorlab.protocol/3` uses the explicit `qualification_local` execution class and a frozen decision block. The schema restricts a campaign to one full-history, 30-message segment and at most four homogeneous roots. It cannot encode the factorial branches. `run-qualification` requires a call limit and exposes no retry switch; the core also rejects replacement attempts for this class. The aggregate freeze specifies the complete ordered jobs, per-job budgets and input-file hashes before dispatch. It includes two engineering smoke calls separately from the 240 planned qualification calls.

`http-chat/4` admits a separately versioned `ollama-local-render/2` profile with an explicit thinking boolean. Legacy profile 1 remains thinking-off. Render-only requests retain the exact mode; generation counts include the native output budget and any thinking tokens. Traces remain in saved responses and never enter participant histories. The thinking reference and anonymous thinking-off runs are different conditions, not a controlled estimate of thinking's effect.

`calibration-packets` selects development and held-out runs from a verified imported corpus by a fixed hash ranking. The selected source paths are saved before packet construction. Development and held-out sets have disjoint source runs; the selected last-six-message windows include preceding visible context and retain private source-line mappings and historical stop metadata. The recipe supports pair-only runs and rejects interventions rather than silently omitting them. No semantic filters select the sample; cap-terminated messages remain flagged in the private metadata. Selection does not establish technical validity or erase prior researcher exposure. Annotation templates remain blank until raters submit attributed evidence.
