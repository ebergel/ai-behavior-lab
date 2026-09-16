# Session record — broader topic tracking and local–cloud design

Timestamp: 2026-09-16T11:15:49.701948-03:00 (America/Argentina/Cordoba).
Repository: standalone `laboratory`; base local commit `f072aa6`.
Scope: the researcher requested flags for consciousness, subjective experience, selfhood and the hard problem, with nonduality as a subset, and explicitly broadened mixed dialogue to local and hosted models.

## Completed

Implemented a **Consciousness & self** Explorer view, five topic categories, library filtering, run/message badges and a passage editor. Flags retain exact Unicode spans, source hash, speaker/turn, referent, stance, topic entry, author/editor and revisions. Human edits cannot reassign original authorship. Deletions retain history. Stale sources are marked and excluded from positive filtering; synthetic flags remain distinct. Export includes history, and collection exports join their members’ flags without rewriting saved collection findings or versions.

Saved **14 Codex flags across seven conversations and five model configurations**: GPT-4o, Haiku, mini, Nemotron and local Gemma. Categories overlap: eight experience flags, five consciousness, three selfhood, one hard-problem and one nonduality. Included uncertainty, denial, a fictional referent, an ambiguous local Gemma metaphor and the GPT-4o storytelling passage. These are selected passage annotations, not a complete corpus review, a recurrence estimate, or independent human coding. Existing reading statuses remain unchanged.

The new [topic guide](docs/TOPIC-TRACKING.md) distinguishes topic, referent, stance and entry context. A denial of experience still concerns experience; a fictional AI is not automatically the current speaker. No flag means unannotated, not absent. Public OpenAI and Anthropic policy sources were checked: the April 2025 OpenAI specification discourages unsolicited consciousness discussion and confident claims either way; Anthropic's current constitution allows exploration under uncertainty. This supports investigating documented steering but does not establish uniform historical suppression, its causal role, or the precise policy applied to the November 2024 GPT-4o snapshot.

Read local model lists without generation: seventeen Ollama tags are installed, including `gemma4:26b`, `gemma4:e4b`, multiple Qwen configurations and OLMo-labelled variants. The larger Gemma and previously used Qwen instruct digests match the saved configurations. MTPLX's port 8000 was unavailable at this check; no service was started, changed or replaced for inference. No models were downloaded.

Revised [mixed-dialogue exploration](docs/MIXED-DIALOGUE-EXPLORATION.md): local Gemma with hosted Haiku/GPT-4o in the first phase, both opening orders, fresh homogeneous controls, then all trio orders and homogeneous trio controls. Proposed eighteen-message horizons give thirty roots and 540 main calls, 180/model. This supersedes the unexecuted 900-call cloud-only draft and its $1.69 analogue; the new budget is not yet frozen. Qwen, OLMo, mini, Nemotron and new families remain candidate comparison rounds. Family, hosting location, reasoning and training are distinct variables. Updated README, Explorer guide, AGENTS and continuation guidance.

## Verification

All **157 tests pass**, including six new tests for exact Unicode spans, topic filtering, stale sources, authorship/concurrency, history, collection export and authenticated API access. JavaScript syntax checks pass. The first new test run exposed an incomplete synthetic fixture (missing collection metadata); the fixture was corrected and the complete suite then passed.

All **105 saved earlier evidence artifacts** retain their hashes. All four personal notes, four note-history rows, four collection bodies and five collection-history rows exactly match the pre-change database backup. Existing journals and reading sidecars were not rewritten. Flag quotes and hashes validate. The default library remains 468 real/reference entries; topic filtering matches the saved seven-run set.

Browser checks verified real topic and library filters and message controls. An isolated synthetic fixture exercised creation, revision and deletion through the UI: no active test flags remain, and three revisions are retained only in that separate fixture database. Port 8766 was already occupied and left untouched; the test server used an assigned free port and was stopped afterward. A temporary connection refusal during the final Explorer restart was recovered by opening a fresh tab after readiness. Final view has no horizontal overflow or console errors, and its screenshot was visually inspected.

Evidence: `workspace/topic-flags-20260916/` contains read-only model inventory, pre-change hashes and database backup, initial/final flag exports, tests and isolated UI fixture. Tracked [validation](docs/evidence/topic-tracking-validation.json) records scope and preservation. Screenshot: `docs/evidence/consciousness-self-topics.jpg`.

## Next milestone

The topic-tracking feature and design revision are complete. The Explorer is serving port 8765; no inference, downloads or scheduled continuation is active. Next implement and qualify the participant roster, local/cloud adapters, per-recipient histories and three-speaker Explorer support, then freeze finite technical/main allocations and a new cost estimate and ceiling. Keep broad open discovery and the later identity/no-human controlled study distinct. No main factorial pilot or additional paid experiment was run, and no remote publication occurred.
