# Repository and publication scope

The laboratory's standalone development repository is **[ebergel/ai-behavior-lab](https://github.com/ebergel/ai-behavior-lab)**. Public publication was authorized on 14 October 2026, including transcripts and research notebooks, with `main` as the working branch. The earlier public [llm-self-play-attractors](https://github.com/ebergel/llm-self-play-attractors) remains a separate reference project.

## What is versioned

The repository tracks the application and inference tooling, tests and synthetic examples, experimental designs, methodological documents, written reports, compact validation artifacts, app screenshots, timestamped session records, and the self-contained [research snapshot](../research/README.md). Existing local commit history is retained. Machine-specific historical configurations retain their original provenance; they are not portable runtime qualification.

`research/` includes byte-for-byte original evidence, readable transcripts, and all eighteen notebook tables with their revision histories. A checksum manifest and offline restore command recreate the populated lab from a clone. Transcripts are core versioned research entities. See [data scope, restoration and updates](RESEARCH-DATA.md).

The live `workspace/` remains ignored because it also contains credentials, indexes, caches, vendor code and disposable diagnostics. Environment files are ignored except `.env.example`. Git contains the explicitly exported research snapshot, not an automatically synchronized live database. Later notes and runs require a new snapshot and commit. Credentials are never part of the snapshot.

## Working with the remote

```sh
git clone https://github.com/ebergel/ai-behavior-lab.git
cd ai-behavior-lab
python3 -m unittest discover -s tests -v
python3 -m behaviorlab.research_bundle restore --bundle research --destination workspace
python3 -m behaviorlab explore --workspace workspace --port 8765
```

After reviewing and committing later changes, publish them with `git push origin main`. The initial upload does not install an automatic sync job or deploy the Explorer as a website. The app continues to run locally.

## Public publication · 14 October 2026

The researcher explicitly authorized synchronization of the full project, including transcripts and notebooks, and changing this repository to public. The publication preserves existing history, research records and failed/partial results. Historical references to a private repository describe earlier milestones.

Public visibility does not by itself grant an open-source license; no new code or data license is selected in this work. Existing third-party notices and provenance remain intact. Private runtime credentials, caches and the live SQLite database remain excluded; the portable snapshot carries the notebook contents and revision histories.

See the timestamped publication session record for verification of the remote commit, visibility and snapshot. Publication does not deploy the local app or establish automatic synchronization.
