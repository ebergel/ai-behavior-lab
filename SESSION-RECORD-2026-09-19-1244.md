# Session record · Bounded JEV recovery and partial research snapshot

Recorded: 2026-09-19T12:44:10.146344-03:00, America/Argentina/Cordoba.

Scope: act on the researcher's “I agree with next plan steps, go”: inspect the stopped full Mind & discourse run, continue only never-dispatched requests under the original aggregate $10 ceiling, audit results, refresh the lab and preserve a self-contained private research snapshot.

## Completed and verified

- Preserved the original plan, scoring questions, source text, frozen runner and every existing receipt. Prepared two separate frozen recovery versions with exact baseline ledgers, pinned code and original aggregate accounting. No successful or uncertain request was resent.
- Recovery v1 encountered a sandbox DNS failure on its first dispatch. A separate connectivity probe confirmed the sandbox restriction. The receipt remains conservatively unknown. A network-enabled public endpoint probe succeeded before v2 began.
- Recovery v2 produced **18 additional valid assessments**, then stopped on a new transport failure after 16.3753 seconds without an HTTP status. In-flight work drained. The cause beyond transport failure is not established.
- Audited totals: **18,309 / 19,316 assessments (94.8%)**, including 120 exact reuses; **494,343 probabilities**. New attempts: **18,194**. Reported new cost **$3.961531728**, unknown reservation **$0.01344**, total committed **$3.974971728**, ceiling **$10**.
- **1,007 assessments remain missing:** five uncertain dispatched outcomes and 1,002 never-dispatched requests. The job is **blocked/stopped**, not complete or running. No automatic retry or scheduled wakeup is active.
- Both wordings are observed for **9,099 / 9,605 conversation messages**, all 41 technical messages and all 12 synthetic controls. Controls and technical messages remain separate; missing scores remain unknown.
- Added a read-only audit script and descriptive report: `scripts/audit_discourse_corpus.py`, `docs/MIND-DISCOURSE-RECOVERY.md`. The machine-readable audit is in the frozen allocation directory as `recovery-audit-20260919.json`.
- Restarted only Behavior Laboratory through App Hub. The live `/api/jobs` confirms blocked status and 18,309 completed assessments; the pilot remains complete at 240.
- Full implementation suite: **417 Python and 114 JavaScript tests passed**. Subsequently, **30 targeted v2 recovery tests**, **five job-adapter tests** and **six job-UI tests** passed. No inference was dispatched by tests. `git diff --check` passed.

## Research preservation and publication

The new snapshot passed credential scanning, hash verification and a complete offline restoration/reindex. It contains **85,229 files**, **1,512,079,289 bytes**, and adds **36,403 files**. Every previously published evidence file and all **18 notebook tables** are unchanged. Inventory remains 573 indexed records (472 default-library records), with synthetic fixtures separately identified.

Snapshot SHA-256: `bd961610467c320bea37393021f3967d3055ee6a07a0844d37246166cca33bb8`.

The verified snapshot is being copied into `research/` for the private repository. Commit/push confirmation is a subsequent publication step; this record does not claim an already completed push. The older running snapshot and `SESSION-RECORD-2026-09-18-2149.md` remain preserved. Unrelated pre-existing Topic atlas/Lab summary edits are left outside this work's commit.

## Remaining work

Investigate TypeSafe transport reliability before any new frozen continuation. Only the 1,002 never-dispatched requests remain eligible for such a continuation; the five unknown outcomes must not be automatically repeated. The latest v2 allocation is blocked by its stop policy and is not silently reopened.

The descriptive results are exploratory, message-weighted classifier responses. Independent classifier validation, model-balanced comparisons and conversation-aware uncertainty remain pending. Names plus portraits and names plus definitions assess different operational constructs; neither provides evidence of model experience or author identity.
