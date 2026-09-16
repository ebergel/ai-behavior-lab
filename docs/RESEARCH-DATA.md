# Self-contained research data

The private repository includes the evidence and notebook needed to explore this laboratory without the original computer, a reference-project checkout, model servers or API keys. This snapshot was prepared on 16 September 2026 with the researcher's explicit authorization. It supports reading, annotation and reanalysis. Repeating inference on another machine requires separate model access and runtime qualification.

## Included evidence

`research/evidence/` preserves 940 files as original bytes: imported content-addressed transcripts, laboratory journals with original requests and responses, protocols and registries, failed attempts, diagnostics, analysis sidecars, review packets, and frozen local source snapshots. Missing historical information remains missing. Old absolute paths and WebUI URLs are retained as provenance; they are not required for offline reading.

`research/transcripts/` provides readable projections of all 573 catalog entries, with conversation/message IDs, model identities, prompts, recorded settings, visible replies, recorded reasoning and status. `research/catalog.json` maps every projection to its authoritative evidence. Repeated raw request/response payloads are omitted only from these projections and remain in the original journals.

The default library contains **472 records**: 400 historical references and 72 laboratory records, including technical checks. The complete catalog also retains 60 synthetic entries and 41 unstarted assessment slots with explicit labels. These totals are an inventory, not counts of comparable experimental replicates. The snapshot includes six assessment screens and four probe batches. Topic atlas has 438 eligible records, 11,204 visible messages, 23 dictionary entries and twelve attributed opening reviews.

`research/notebook/` exports all fourteen SQLite tables as schemas and exact row values. It retains five personal notes, six collections, 28 topic flags, 23 topic definitions, twelve opening reviews, five purpose/musing entries, saved-view tables and every stored revision. Empty tables and deletion history are preserved. `readable.json` also presents parsed notebook content for direct reading on GitHub. A consistent SQLite backup is used to capture the notebook, including committed WAL transactions.

The snapshot deliberately excludes credential files, the live SQLite database and indexes, old binary database backups, model weights, vendor dependencies, caches, locks, logs and disposable fixtures. This is a research snapshot, not an image of the entire computer. Original sources are never redacted or rewritten; export stops if its known-credential or token/private-key screening finds a candidate. That bounded screening is not a universal secret detector.

## Restore a fresh clone

Run from the repository root, with Python 3.9 or later:

```sh
python3 -m behaviorlab.research_bundle verify --bundle research
python3 -m behaviorlab.research_bundle restore --bundle research --destination workspace
python3 -m behaviorlab explore --workspace workspace --port 8765
```

Open `http://127.0.0.1:8765`. The macOS **Open Explorer.command** performs the restore automatically when starting the app with no existing workspace. It reuses an already running Explorer on port 8765.

Restore always requires a new destination. It verifies every file hash, restores original relative evidence paths and all notebook rows, rebuilds the catalog and checks every conversation projection before installing the new directory. It makes no inference requests. `.gitattributes` prevents Git from converting the snapshot's line endings.

To inspect a second copy while keeping a live workspace, choose a different path and port:

```sh
python3 -m behaviorlab.research_bundle restore --bundle research --destination /tmp/lab-reading-copy
python3 -m behaviorlab explore --workspace /tmp/lab-reading-copy --port 8770
```

The destination must not already exist. Runtime indexes regenerate locally. A manifest fingerprint detects accidental changes; Git history records which snapshot was published. Historical runtime qualification is not transferred to the new machine by restoration.

## Updating the snapshot

New annotations and runs remain in the live workspace until explicitly exported and committed. To prepare the next revision, use a **new directory outside the workspace**:

```sh
python3 -m behaviorlab.research_bundle export --workspace workspace --output /tmp/lab-research-next
python3 -m behaviorlab.research_bundle verify --bundle /tmp/lab-research-next
```

Export includes a full restore test. Review the manifest, inventory, notebook and source changes, then replace the tracked `research/` directory with the verified new snapshot, retaining the previous copy until verification is complete. Commit and push the reviewed update. Do not export into `workspace/`, force-add the live database, or copy credential folders into Git. Publication does not configure background synchronization or change repository visibility.

The original public reference project remains independent. The private lab stores its imported evidence with source provenance and content hashes; it does not require that repository at runtime. Any future public release needs its own deliberate selection of code and evidence.
