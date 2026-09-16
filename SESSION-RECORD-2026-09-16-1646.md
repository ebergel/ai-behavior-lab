# Session record — self-contained private laboratory

Timestamp: 2026-09-16T16:46:02.852650-03:00 (America/Argentina/Cordoba).

Scope: the researcher explicitly requested that the private GitHub repository include the transcripts and research notebook, because transcripts are core entities and the repository should stand on its own. This supersedes the initial code-only publication boundary recorded earlier today.

## Completed publication

The self-contained research snapshot was committed and pushed to [ebergel/ai-behavior-lab](https://github.com/ebergel/ai-behavior-lab), main branch, commit `627b6d61bc397ba4345c3f91eb98db153e25e217`. GitHub visibility was confirmed private. This laboratory remains independent of the earlier public reference project.

The tracked `research/` directory contains 940 original evidence files, 573 readable catalog projections, all fourteen notebook tables with full stored revision histories, a source map and a checksum manifest: 1,531 files totaling 253,447,504 bytes. Original journals, raw requests/responses, imported transcript bytes, failures, protocols, review/analysis sidecars and frozen local code are retained. Readable projections preserve visible and recorded reasoning text; duplicated raw payloads remain in the authoritative evidence.

The default library contains 472 reference/laboratory records, including technical checks. The full catalog also preserves 60 synthetic entries and 41 unstarted slots with their original labels. Inventory counts are not comparable replicate counts. Six research collections contain 43 findings. Five personal notes, 28 topic flags, 23 dictionary entries, twelve opening reviews, five musings and their stored histories are included.

Snapshot fingerprint: `a839c7eb8bf6455f12359f55c04bc7c1a3cf043317e608fdea7de9c967a48a48`. Exact notebook table fingerprint: `b6b38ae993980bae033b17091a2c07da323c8497a1d1f6197d9e7747529476b0`.

## Restoration and verification

`python3 -m behaviorlab.research_bundle restore --bundle research --destination workspace` restores only into a new directory. It verifies all file hashes and every portable conversation projection, restores exact notebook rows, and preserves source IDs and original relative paths. The macOS launcher restores a missing workspace before starting the app. No model server, API key or reference checkout is needed for reading and reanalysis. Existing workspaces are never overwritten. `.gitattributes` preserves the snapshot's original line endings.

Both a clean local code copy and a fresh download from GitHub restored successfully. Python audit hooks blocked reads under the original project and all network connections during those restoration checks; there were zero attempted blocked operations. Validation checked 174 exact quoted passages, all fourteen notebook tables, the six collections and every source-current review/flag. Topic atlas retained 438 eligible records, 11,204 visible messages and twelve resolved reviews; consciousness retained 204 literal-match records, and Haiku plus consciousness retained four Finder results.

A separate localhost HTTP check on the GitHub-restored copy served the app successfully, exposed all 472 default records and six collections, and opened the four-dialogue mixed pilot. The temporary server was shut down. The normal Explorer was not stopped or replaced.

All 210 Python tests and fourteen JavaScript tests passed. Tests cover restoration without the original sources, exact Unicode spans and revision/deletion history, credential exclusion, failure on credential candidates, tampered/unlisted files, symlinks, path traversal and existing-destination protection. Preservation checks passed for all 940 exported originals, the current notebook rows, 111 prior source hashes, 32 frozen pilot dependencies and 105 prior pilot artifacts.

See [research data and restoration](docs/RESEARCH-DATA.md), [validation](docs/evidence/research-publication-validation.json), and [the reproducible standalone check](docs/evidence/research-publication-check.py).

## Scope and next work

Credential files, live SQLite/index files, old binary backups, vendor dependencies, model weights, caches, locks and disposable logs remain excluded. Every snapshot file passed known-local-credential and provider-token/JWT/bearer/private-key screening; this is bounded screening, not a universal secret detector. No original evidence, researcher note or attribution was changed. No inference or spending occurred.

This is a versioned research snapshot, not automatic synchronization. Later runs and annotations require a reviewed export and push. The live workspace remains ignored. A future public release remains separate work; the prospective opening/partner runner remains the next research milestone and was not executed in this session.
