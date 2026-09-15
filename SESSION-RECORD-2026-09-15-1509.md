# Session record — transcript explorer v1

Recorded: 2026-09-15T15:09:14.634115-03:00 (America/Argentina/Cordoba).
Scope: standalone Behavior Laboratory repository. User requested a dedicated application for transcript exploration alongside WebUI. Parent commit: `18c42e94f7a0e495e092bf669bb8f30220af58d1`.

## Completed

Built and launched the local explorer at **http://127.0.0.1:8765**. It indexes 400 imported reference conversations and 34 real laboratory roots; 60 synthetic roots are available separately and excluded from the default library. The 434 real roots contain 10,982 visible participant replies including flagged partial outputs. Recorded mechanical counts show 117 roots with a cap and 35 with exact repetition; these are inventory summaries, not semantic prevalence.

Implemented searchable/filterable cards, a message atlas, a close reader with actual branch ancestry, side-by-side comparisons, source-linked personal notes and passage tags, notebook export, and access to six existing experiment reports. Prompts and per-recipient settings appear beside the transcript. MTPLX settings include reasoning mode, requested cap and recorded runtime context. Exact saved requests, raw responses and original historical records remain inspectable. Missing metadata is not supplied from present-day defaults. Successive engineering versions have visible campaign paths.

Kept WebUI and its bridge. The app shows existing verified export links and performs no WebUI writes. The new explorer reads source evidence and stores observations separately in `workspace/explorer/notes.sqlite`. Revision history survives edits and removals; source quote offsets are checked against exact Unicode text. Notebook observations do not enter formal coding packets.

Added `Open Explorer.command`, a standalone CLI entry, packaged browser assets, an isolated UI fixture generator and the user guide in `docs/EXPLORER.md`. Updated README, architecture, continuation and project instructions to reflect the user's new app priority. Prior session records were preserved.

## Verification

All **105 tests passed** in the working repository and a separate copied source tree. JavaScript and launcher shell syntax checks passed. Browser checks covered the real catalogue and an isolated synthetic fixture, including filtered URLs, actual RF ancestry, comparison, source inspection, report display, selected passages, Unicode, literal HTML rendering, note persistence and a 390-pixel responsive layout without horizontal overflow. No browser console errors remained in the final library check. Finder double-click was not directly tested; the launcher passed syntax validation and its server command ran successfully.

All 400 imported blobs verified against the unchanged dataset fingerprint. Rechecked 88 distinct workspace artifacts recorded in prior validation manifests; every fingerprint matched. Runner, history, probes, formal annotations, trajectory outcomes and legacy-importer code remained unchanged. The evidence record is `docs/evidence/explorer-validation.json`; test logs, screenshots and detailed checks are in ignored `workspace/explorer/validation/`.

Two test observations were saved only in the isolated fixture notebook. The real notebook contains no test notes. The isolated server was stopped and the real explorer was left running. One source-index notice identifies a separate capacity snapshot diagnostic format; its findings remain accessible through the capacity report.

## Scientific and operational status

No model calls, downloads, cloud spending, new WebUI imports, public deployment or scheduled wakeups occurred. Existing failed capacity results and older parser evidence remain unchanged. The live factorial pilot is still disabled, measurement v2 is a draft, and independent human adjudication remains pending.

The app uses literal search and manual observations. Embedding search, semantic labels, named saved collections, parameter-value filter building, notebook restore UI and experiment launching are not implemented. Removed-note history remains in SQLite; the JSON export contains current visible observations only.

## Next phase

Use first-hand reading to assemble a small, attributed set of passages and counterexamples, keeping personal exploration separate from formal ratings. Let these observations inform the next hypotheses and experimental-design revision. Preserve the deferred runtime accounting and qualification work in `docs/CONTINUATION.md`. The next inference batch still requires a frozen question, protocol, seed allocation, budget and failure rules.
