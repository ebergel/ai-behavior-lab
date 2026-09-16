# Private repository and publication scope

The laboratory's standalone development repository is **[ebergel/ai-behavior-lab](https://github.com/ebergel/ai-behavior-lab)**. It is private, with `main` as the working branch. The earlier public [llm-self-play-attractors](https://github.com/ebergel/llm-self-play-attractors) remains a separate reference project.

## What is versioned

The repository tracks the application and inference tooling, tests and synthetic examples, experimental designs, methodological documents, written reports, compact validation artifacts, app screenshots, and timestamped session records. Existing local commit history is retained. Machine-specific historical configurations retain their original provenance; they are not portable runtime qualification.

`workspace/` is deliberately excluded. It contains full imported and generated evidence, raw requests/responses, model-access credentials, temporary diagnostics, and `explorer/notes.sqlite` with the current notebook, collections, dictionary revisions, opening reviews and musings. Environment files are ignored except `.env.example`.

A Git push backs up tracked project files and history. It is **not a full backup of the research workspace**. A fresh clone can run the software and synthetic tests, but does not contain the populated research library or live notebook. Those require a separately prepared evidence/notebook backup and restore. Do not copy the whole workspace to Git: its private credential material must remain local. Reference data can also be imported using the instructions in the README.

## Working with the remote

```sh
git clone https://github.com/ebergel/ai-behavior-lab.git
cd ai-behavior-lab
python3 -m unittest discover -s tests -v
python3 -m behaviorlab explore --workspace workspace --port 8765
```

After reviewing and committing later changes, publish them with `git push origin main`. The initial upload does not install an automatic sync job or deploy the Explorer as a website. The app continues to run locally.

## Later public release

Private development is the present scope. No open-source license or public distribution is selected by this publication. GitHub visibility applies to the repository, not individual branches: a public edition would need a separate repository or an explicit visibility change after preparing an appropriate release. A separate public release can retain scientific provenance while selecting distributable code and evidence deliberately; that preparation is future work.
