# Session record — standalone laboratory, Milestone 1

Recorded: 2026-09-14T16:50:07-03:00
Timezone: America/Argentina/Cordoba (UTC−03:00)
Scope: Implement the first instrument milestone following the laboratory plan, while honoring the user's explicit clarification that this is a new repository.

**User clarification and project boundary**

The user first requested the next implementation step, then interrupted to clarify that the laboratory is a new GitHub project, not an extension of the earlier experiment repository. The interrupted portion had only read files. Work resumed with a separate Git repository initialized on branch `main` in this `laboratory/` directory. The earlier `ebergel/llm-self-play-attractors` repository is used as a reference and optional data source only. No GitHub remote has been created or configured in this milestone.

**Completed implementation**

Built a Python 3.9+ package with no third-party runtime dependencies. It includes validated, versioned protocol and model registries; frozen model/protocol objects; immutable message ancestry; participant-specific full/recent history construction; four history paths; a single-writer append-only journal with canonical hashes; durable request and raw-response records; a deterministic fake backend; explicit unresolved-attempt handling; pause/resume; branch failure accounting; and a rebuildable SQLite event index.

Built an explicit reference-corpus importer that preserves original JSONL bytes in content-addressed storage and creates a queryable SQLite catalog. Unknown record fields and non-message records are retained. Missing model digests remain unknown. Absent trace fields remain distinguishable from observed empty traces. Audit interpretations are stored as a separate supplement, preserving original data.

Added a CLI, standalone example protocol and registry, 27 automated tests, architecture and usage documentation, research-source provenance, and compact verification evidence. The original laboratory research proposal remains a separate, unexecuted design; the runtime accepts only a distinct synthetic-engineering schema.

**Verified outcomes**

All 27 tests passed. Tests cover the real restricted-history restoration path, X/Y model and role mapping, immutable snapshots, registry/template drift, single-writer exclusion, saved-response recovery without regeneration, explicit retries after uncertainty, raw response preservation, empty messages, literal `[END]` under a closed protocol, malformed output, cap hits, unexpected traces, corrupt/partial journals, and source-corpus integrity.

The full synthetic factorial paused after 75 new calls and resumed to exactly 1,800 requests/responses/committed turns across 20 roots and 80 endpoints. Re-running the completed campaign left its journal bytes unchanged. This is fake-backend output, not a new behavioral result.

Imported all 400 primary source runs from revision a93f71368e08e9040e49a10cbef8f4e9c956e16c. Reproduced 10,396 paired messages and 280 third-party messages. Stage paired-message counts are 2,742, 4,153, and 3,501. All 400 imported source hashes matched the original files after work. No original experiment file was modified. The prior audit REPORT.md was attached with SHA-256 `3e9a0721abb71614056b6fe1d5c6870c4f80eaa529adc44cd555e7e34862f212` as separate analysis.

A clean source-only copy, with no old repository or data store, passed all 27 tests and a CLI smoke run. This verifies that the new laboratory has no sibling-directory runtime dependency. Local documentation links were checked.

**Artifacts**

- [Project README](README.md)
- [Scientific plan](PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Milestone verification](docs/MILESTONE-1.md)
- [Machine-readable validation](docs/evidence/milestone-1-validation.json)
- [Synthetic example](examples/history-factorial.fake.json)
- [Model registry](design/models.json)
- [Research provenance](docs/REFERENCES.md)

Generated evidence is in the Git-ignored `workspace/demo-factorial/` and `workspace/reference-corpus/` directories. The first local source commit is created after this record; its commit ID is reported in the task response rather than inserted recursively into its own committed record.

**Not yet performed / next step**

No new live inference, model download, historical reproduction, behavioral qualification, or actual factorial pilot was performed during this implementation. The copied initial readiness journal belongs to the preceding planning session. No live adapter or browser UI is implemented yet. The small Qwen4 thinking/template issue remains unresolved.

The next step is Milestone 2: implement the local Ollama adapter, model identity/mode checks, recipient-specific context bounds, real engineering trials including mixed-model and long histories, and a minimal campaign viewer. Model qualification and annotation/probe decisions precede the scientific pilot. The repository's GitHub name, remote, and publication remain to be established separately.
