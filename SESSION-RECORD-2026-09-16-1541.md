# Session record — Private GitHub publication

Timestamp: 2026-09-16T15:41:37.622236-03:00
Scope: publish the standalone laboratory to a new private GitHub repository, as requested by the researcher.

## Completed and verified

Created **https://github.com/ebergel/ai-behavior-lab** under the authenticated `ebergel` account. GitHub reports `private: true`, visibility PRIVATE, `fork: false`, and default branch `main`. The earlier public `llm-self-play-attractors` repository was not modified. The local lab has `origin` set to the new repository, and local `main` tracks `origin/main`.

Uploaded the existing local history plus updated README, private repository scope and environment-file ignore rules. Verified that GitHub's main branch exactly matches initial publication commit `f9d4cfa26ef1f169a7d37462c16fb4dddd63322d`. The initial remote tree contains 285 files and no `workspace/` paths. This session record and the publication receipt are a follow-up documentation commit.

Reviewed all 478 blobs reachable in the 33 pre-publication commits with heuristic token, private-key, credential-assignment and URL-userinfo patterns, plus sensitive filename and file-size checks. Two URL-userinfo hits were endpoint-rejection fixtures targeting example.com in two revisions of `tests/test_live.py`; no unresolved credential candidates remain. This is a bounded review, not a guarantee of exhaustive secret detection. No tracked artifact approaches GitHub's large-file limit. The full suite passes 202 Python tests and 14 JavaScript checks.

## Scope and limitations

The private remote contains the app, experiment tooling, designs, written reports, compact validation artifacts, screenshots and session history. The roughly 571 MB local `workspace/` is ignored, including full transcripts, raw request/response evidence, credentials and `explorer/notes.sqlite`. The current notebook, collections, dictionary/review histories and musings are therefore not fully backed up by this Git push. No source evidence or annotation rows were rewritten.

A fresh clone can run the app and synthetic tests but requires separately imported/restored evidence and notebook data to reproduce the populated lab. `docs/REPOSITORY.md` explains this boundary. A separate evidence/notebook backup remains a useful next infrastructure step; credentials must be excluded from such a publication.

No public release, open-source license, hosted application deployment, collaborator invitation or automatic sync job was created. Future public distribution is a separate decision. GitHub repository visibility applies to all branches, so a public edition cannot be achieved by marking one branch public.

Evidence: `workspace/github-publication-20260916-1538/`; portable receipt: `docs/evidence/github-publication-20260916.json`. The local Explorer and model services were not restarted. No inference, downloads of models, cloud spending or scheduled continuation occurred. The opening/partner runner qualification and experimental freeze remain pending.
