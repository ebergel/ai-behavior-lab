# Session record — intact windows and corpus preparation

Recorded: **2026-09-17T13:31:25.044950-03:00**, America/Argentina/Cordoba (UTC−03:00).

Scope: the researcher's “go” to qualify long-passage handling and prepare the full-corpus assessment. **Offline implementation and preflight are complete; external qualification is pending explicit approval. Zero new TypeSafe calls were sent.**

## Completed and verified

- Established that question definitions drive the largest payloads. Nine full 53-question requests exceed the unchanged 60,000-byte screen; the largest is 68,808 bytes. The longest target/context window is 27,644 bytes.
- Implemented a uniform two-pack policy: 24 broad questions and 29 focused/form/stance/coverage questions, each receiving the identical full passage and actual two-event context. Exact question objects partition the prior 53-question codebook. No text truncation, chunking or score recombination.
- Froze 54 qualification calls, ceiling $0.60, under `workspace/jev-atlas/intact-window-20260917-v1`: all 15 long windows and twelve prior controls, two calls each. Packs: `d5078aa105039b65e07cb188` and `903d721b5cebc479b8011e0d`. Qualification requests range 18,732–50,347 bytes.
- Audited every visible corpus target offline: 11,054 targets, 22,108 logical request hashes, 18,567–50,347-byte payloads. Conversation targets 11,013; technical/short targets 41; unavailable positions 484. `corpus-readiness.json` is preflight evidence, not a dispatched corpus campaign.
- Added full-path history/speaker audit. Every target has a recorded speaker model. 9,587 targets have clean observed histories; 1,467 have flagged/incomplete history, including 123 with otherwise normal target status. Branches use actual parents. Clean observed history does not establish historical runtime validity.
- Implemented a gated corpus-freeze action: requires completed live qualification, retains exact target/context inputs, reuses only checksum-matched completed requests, reserves up to 60 previously unassessed reference lineages, and calculates empirical cost scenarios and an aggregate reserve. It has not been invoked because qualification is pending. There is no corpus-dispatch command.
- Fixed atlas inventory rendering when a newer pack does not inherit the 56-reading packet. Related prepared packs now direct users to their aggregate terminal coordinator. Browser checks confirm 24 broad rows, six stance rows and unavailable scores, with no render error; returned the browser to the completed assessment.
- All 236 Python tests and 26 JavaScript checks passed. Tests cover intact states, fixed partitions, refusal of unsupported size, source drift, exact reuse, independent-reference separation, branch history, no duplicate dispatch and aggregate failure stop.
- Exported and restore-tested a private research snapshot with 2,040 files, 1,450 original evidence files and 573 transcript projections. All preceding 1,445 original evidence files and all 14 notebook tables remain unchanged. Bundle fingerprint `26f471234ea04db6f69765aec2b1afa7a072e34dc3607a3ff4c7489430096aa4`.

## Blocked action and pending approval

Automatic approval review rejected the first `jev_corpus run --max-calls 1` command before execution. Reason: the existing explicit approval covered the preceding 39-call allocation, and “go” was insufficient for sending this new private transcript/context payload to TypeSafe. A self-contained async question requests approval for these exact 27 passages/context, two packs per passage, **54 calls under $0.60 to api.typesafe.ai**. The question is pending. No alternate route was attempted. Both new batch request directories remain empty.

After approval, save its receipt, inspect one request, complete only remaining frozen calls, summarize, then freeze the corpus campaign. Roughly 22,000 later requests need a separate aggregate execution implementation/allocation and dispatch authorization. Do not treat either preflight or the 54-call approval as authorization for them.

See [preparation and exact resume commands](docs/JEV-INTACT-WINDOW-QUALIFICATION.md), [validation](docs/evidence/jev-intact-window-validation.json), and [continuation](docs/CONTINUATION.md). No human reference ratings, new behavioral findings, automation, remote-access setup or public release occurred. Publication remains restricted to the existing private repository under standing authorization.
