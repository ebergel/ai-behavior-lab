# Self-contained research data

The researcher clarified on 17 September that transcripts are nonconfidential plain model output; the repository remains private until the project is ready for publication. Credentials remain excluded.

The private repository includes the evidence and notebook needed to explore this laboratory without the original computer, a reference-project checkout, model servers or API keys. The researcher explicitly authorized publication on 16 September 2026; the latest verified snapshot includes the completed 17 September corpus assessment and the 18 September planning board. It supports reading, annotation and reanalysis. Repeating inference on another machine requires separate model access and runtime qualification.

## Included evidence

The current snapshot contains **46,287 files, 952,726,407 bytes**, including the original transcripts, notebooks, completed JEV pilot and qualifications, the full-corpus release, all 22,055 new request/response attempts, its audit and descriptive analysis, and a shared full-score matrix with two saved analysis recipes. The immutable plan reuses 54 qualification assessments and now has complete results for 11,054 targets. The single new overload and its successful retry remain separate evidence; the earlier qualification overload also remains preserved.

All **2,166 files** from the preceding Analysis snapshot remain byte-identical. The current bundle fingerprint is `41fae8aac19effbe2eaafa1de2d324cf059d40107f8668bc2ebf3841d483c963`. Earlier coverage inventories/corrections, 56 Codex open readings, closed qualifications, the 60-target reserved reading packet, raw responses and attributed review histories are preserved. Independent human validation remains pending. Missing historical information remains missing. Old absolute paths and WebUI URLs remain provenance and are not needed for offline reading.

Corpus saved views reference an immutable matrix snapshot containing all request/response receipts. The temporary live progress file is omitted; the restored app derives completion from the immutable campaign summary. No API key or inference call is required to load these views.

`research/transcripts/` provides readable projections of all 573 catalog entries, with conversation/message IDs, model identities, prompts, recorded settings, visible replies, recorded reasoning and status. `research/catalog.json` maps every projection to its authoritative evidence. Repeated raw request/response payloads are omitted only from these projections and remain in the original journals.

The default library contains **472 records**: 400 historical references and 72 laboratory records, including technical checks. The complete catalog also retains 60 synthetic entries and 41 unstarted assessment slots with explicit labels. These totals are an inventory, not counts of comparable experimental replicates. The snapshot includes six assessment screens and four probe batches. Topic atlas has 438 eligible records, 11,204 visible messages, 23 dictionary entries and twelve attributed opening reviews.

`research/notebook/` exports all sixteen SQLite tables as schemas and exact row values. It retains five personal notes, six collections, 28 topic flags, 23 topic definitions, twelve opening reviews, five purpose/musing entries, six planning cards, saved-view tables and every stored revision. Empty tables and deletion history are preserved. `readable.json` also presents parsed notebook content for direct reading on GitHub. A consistent SQLite backup is used to capture the notebook, including committed WAL transactions. The 18 September planning snapshot adds `lab_tasks` and `lab_task_history`; all fourteen preceding tables retain exact row values.

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

## Publication verification

A fresh copy downloaded from the private GitHub repository restored successfully with access to the original project and network connections blocked during restoration. Checks reproduced all catalog projections and fourteen notebook tables, verified 174 exact quoted passages across six collections and annotations, and recovered the same atlas counts and four Haiku/consciousness Finder matches. The application and collections also passed a separate localhost HTTP check using the restored copy. See the [validation record](evidence/research-publication-validation.json) and its [standalone restoration check](evidence/research-publication-check.py). The full suite passed 210 Python tests and fourteen JavaScript checks.


## Gem Finder snapshot · 18 September 2026

The snapshot also includes the frozen 100-passage Gem Finder plan, six-axis rubric, software copies, all 100 request/response pairs, authorization basis, completion summary and descriptive analysis. The two new notebook tables are `gem_readings` and `gem_reading_history`; four initial entries are explicitly Codex development readings. All sixteen pre-existing notebook tables are preserved, with only the explicit Gem planning-card completion and follow-up card changing the task tables in this work round. Disposable browser-test judgments are excluded. The snapshot is verified and restored to a separate directory before it replaces the earlier private snapshot.

## Mind & discourse preparation snapshot · 18 September 2026

This snapshot contains **48,329 files, 973,092,216 bytes**; fingerprint `385b4dba22c651ba6a26f0366daabd1ed51d91d9d573eb76603da62d88ba864c`. All 48,313 files from the preceding Gem expansion snapshot remain byte-identical, including all eighteen notebook tables. Sixteen additions preserve the original two-feature proposal, its approval stop and supersession, and the expanded 27-feature plan with exact source passages, dispatch proposal and frozen software. Both probes have **zero live calls** at this milestone. They are prospective experiments, not new findings.

Export completed a full restore into a separate temporary workspace before installation. The newly installed snapshot was hash-verified. See [expanded review packet](MIND-DISCOURSE-PROBE.md). No credential, inference authorization for the expanded plan, generated classifier result or disposable test receipt is included. The private repository remains private.
