# Session record — research collection and first reading

Recorded: 2026-09-15T15:37:55.218745-03:00 (America/Argentina/Cordoba).
Scope: standalone Behavior Laboratory. Parent commit: `d036975ecf0ab8bb2f524ae4a2210b0f4447eab1`.

## User direction

The user asked to use the explorer to explore and save findings together in a single tidy entity, reducing the amount of material they needed to hold in cognitive context. The earlier suggestion was a small comparative reading set with exact passages, counterexamples and causal hypotheses. This session implemented that research collection and completed a bounded first reading pass.

## Completed

Saved **Understanding, experience & nonseparation** in the explorer, collection `5bf785a35611b33960c681a0`. It contains **24 real conversations, 10 Codex-attributed findings and 30 verified source passages**. Eight conversations received full visible-transcript readings, four selected-passage reviews, and twelve remain explicitly queued. Selection was purposive and informed by keyword retrieval and model/condition coverage. This is not a prevalence estimate or independent human coding.

Findings distinguish different routes into nonseparation, experience stance, relational elaboration, ordinary agreement and philosophical counterexamples, generated human-partner identity, absorption of outside challenges, task completion, repeated endings, caps and transcript-role contamination. The common anonymous Gemma example reaches observer–observed unity without the explicit same-model prompt, then attributes human qualities to its actual AI partner. A base-Qwen example repeats ordinary agreement about environmental cooperation. These motivate tests of framing and reciprocal continuation; they do not establish subjective experience, ego absence, meditative realization or a single human/model mechanism.

The collection keeps a short synthesis, expandable findings, a reading queue, selection limits and personal observations together. Every passage links to its full message, prompt and settings. Returning restores the finding. Passage comparison is available. Personal notes can be assigned to a collection without becoming Codex findings or formal ratings. The initial real notebook had no personal notes and none were fabricated during this work.

Implemented versioned collection storage in the existing SQLite notebook, immutable original authorship, declared editors, exact Unicode span/source validation, conflict rejection, changed-source warnings and a single export bundle. The export carries the collection, linked personal notes, selected visible transcripts, saved reasoning fields, prompts, settings and source fingerprints. Raw request/transport payloads remain in the source store. Created collections and their individual reading status can be managed in the app; structured finding editing, source-bundle import and revision restoration are not yet UI features.

The source collection is in ignored `workspace/explorer/notes.sqlite`. Its exact input, receipt and portable export are in `workspace/explorer/first-reading/`. A pre-write SQLite backup was saved with owner-only permissions. Updated the explorer guide, README, architecture and continuation instructions. The concise operational record is `docs/FIRST-READING.md`.

## Verification

All **112 tests pass** in the working repository and a separate copied tree. New tests cover collection persistence/export, attribution, optimistic revisions, exact quotes, changed and missing sources, reading membership, personal-note linkage and HTTP origin/export contracts. JavaScript syntax and diff checks pass.

Browser checks exercised real finding expansion, four-passage comparison, the focused source message and return to its original finding. An isolated synthetic collection tested creation, adding a run, saving a linked personal observation and persistence after reload. No browser errors remained. A normal-size screenshot was inspected. A phone viewport override did not take effect in the browser, so this session does not claim mobile validation of the new collection view; the override was reset. The isolated server was stopped, and the real explorer remained available.

All 30 saved quotes match their exact source spans and fingerprints. All 400 imported blobs verify. All 88 prior workspace artifact hashes rechecked unchanged. The runner, history, probes, formal annotations, trajectory-outcomes and legacy-importer modules remain unchanged. Prior records were preserved. The portable validation is `docs/evidence/first-reading-validation.json`.

## Boundaries and next phase

No new inference, cloud spending, downloads, WebUI writes, public deployment or scheduled wakeups occurred. The live research pilot remains disabled, the prior failed capacity screen remains recorded, and independent human adjudication is pending. Model-generated empirical-sounding claims encountered in transcripts were not externally verified or promoted to scientific evidence.

The next phase can continue inside this same collection: read the twelve queued comparisons, add the user's practitioner interpretations under personal observations, refine disputed distinctions and counterexamples, then turn the surviving hypotheses into a frozen causal design. Record the scope of each additional reading. Existing runtime qualification, seed allocation, finite budgets and failure rules still apply before any new inference.
