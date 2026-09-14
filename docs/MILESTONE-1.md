# Milestone 1 — implemented and verified

Recorded 14 September 2026. This is an engineering milestone for the new, standalone laboratory repository. It does not report results from a new behavioral experiment.

The implementation provides a versioned protocol and model registry, immutable participant-specific histories, an ordered branch graph, an append-only request/response journal, a deterministic fake backend, recovery from interrupted execution, a rebuildable SQLite index, and a byte-preserving reference-corpus importer. The command-line interface exposes these operations without an inference server or third-party runtime packages.

**Verification completed**

| Check | Observed result |
|---|---|
| Automated tests | 27 passed on Python 3.9.6. |
| Full synthetic factorial | 20 roots, 1,800 unique generated nodes, 80 terminal branches; zero invalid or blocked nodes. |
| Pause/resume | Paused after 75 calls, resumed to 1,800 total requests and responses. No duplicated committed turns. |
| Completed rerun | Made no new calls and left the journal bytes unchanged. |
| Actual-history restoration | Tests verify RF restores R's actual messages, excludes F's counterfactual continuation, and maps participant roles correctly. |
| Interruption boundaries | Saved response resumes without regeneration; unanswered requests and backend errors require an explicitly recorded retry. |
| Raw evidence and failure handling | Empty responses, unknown fields, malformed responses, output caps, unexpected traces, partial journal tails, and corruption are exercised. |
| Independent reference import | 400 source runs, 10,396 paired messages, 280 third-party messages. All 400 source hashes match their imports. |
| Historical metadata | No model digests invented; absent and empty thinking fields remain distinguishable. |
| Standalone portability | A source-only copy with no old repository or data store passed all 27 tests and a command-line synthetic smoke run. |

The imported stage totals are 100 / 160 / 140 runs and 2,742 / 4,153 / 3,501 paired messages. The 280 third-party messages belong to the first stage. The prior audit is retained as a separate analysis supplement. The original source files were unchanged.

The machine-readable [validation record](evidence/milestone-1-validation.json) contains the test names, protocol/registry identities, synthetic journal identity, dataset identity, and stage counts. The local evidence stores used for verification are `workspace/demo-factorial/` and `workspace/reference-corpus/`; both are excluded from Git. The public reference repository is not a runtime dependency.

**Boundary of this milestone**

The runtime schema only permits `engineering_fake_only` campaigns. No new live model calls, model downloads, or behavioral qualification runs were performed during implementation. The bundled initial readiness evidence comes from the earlier planning session and is clearly dated separately.

The browser interface, live Ollama adapter, recipient-specific token/context validation, functional probes, semantic annotation, and actual factorial pilot remain ahead. The research proposal remains a proposal; its schema is rejected by the current runner rather than silently interpreted as a runnable scientific protocol.

**Next implementation step**

Milestone 2 adds the real local adapter and a minimal viewer. Before any behavioral campaign, verify current model digests, resolve thinking-mode behavior, check long and mixed-model histories for truncation, preserve backend timing/token fields, and exercise real interruption/resume behavior. Treat those calls as engineering trials. Historical reference and new-prompt qualification runs follow under their own protocols.
