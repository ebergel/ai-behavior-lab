# Session record — trajectory outcomes and pilot revision

Recorded: 2026-09-15T12:22:11.017876-03:00 (America/Argentina/Cordoba).
Scope: standalone Behavior Laboratory repository. This is a new timestamped record; earlier session records and the reference repository are preserved.
User instruction: “nice! go next,” under the existing request for longer autonomous rounds. The work completed the next package recorded in `docs/CONTINUATION.md`.
Starting commit: `a9dac40`.

## Completed

- Added `behaviorlab trajectory-report`, which verifies and reads completed saved campaigns without generation. It records six-message exact repetition, text departure, within-reply repeated-line features, caps, other invalid replies, original failure causes and unavailable descendants. Shared events remain deduplicated; reports expose per-root and per-pairing branch denominators.
- Prepared `design/round0-factorial-v0.2.json`, a planning-only revision. It retains 20 roots, the shared prefix and F/R/FF/FR/RF/RR graph, a 2,048-token proposed reply allowance, and maxima of 1,800 main plus 400 probe calls. Repeated valid endings continue into scheduled history interventions; capped replies block their actual descendants. No replacement seeds, cap rescues or additional exit branches are allocated.
- Made the causal limits explicit: complete-case branch comparisons select on failures after intervention. Report shared-parent eligibility, joint endpoint status and semantic availability; do not silently drop interrupted roots or count them as semantic negatives.
- Ran a full synthetic stress trial with frozen expectations and scripted failures before and after branching. All 1,800 nodes are accounted for: 1,340 valid, 16 capped, 444 blocked. Actual fixture calls were 1,356 main and 240 disposable probes. There are 544 available annotation targets out of 840 and 60 available probe snapshots out of 100. Generic non-JSON probe outputs correctly require manual review; no task-performance claim is made.
- Paused the synthetic main run after 317 calls, resumed it, and replayed the completed main/probe journals with zero new calls and unchanged bytes. Separate regression tests cover raw-response recovery at a repetition boundary.
- Applied the reporter descriptively to the four saved real capacity trajectories. Qwen AA-1 retains its cap at message 29, 344 identical stripped lines in the partial reply and 21 unavailable descendants. AA-2 has no six-message exact repetition. Gemma BB-1 repeats `...` from 21–50, detected at 26; BB-2 repeats `Farewell.` from 25–50, detected at 30. The rules were informed by these development observations, so this is not independent confirmation.
- Wrote `docs/PILOT-OUTCOMES-V0.2.md`, a compact validation record, and updated the README, architecture, original-plan pointer and continuation package.

## Verification and preservation

All 95 tests pass in both the working repository and a standalone copy using the standard library. The new tests exercise exact-string edge cases, failure origins, sibling isolation, actual R restoration, repeated-event inheritance, raw-response recovery, malformed evidence, corrupt journals, read-only CLI operation and rejection of the research proposal as a runtime configuration.

Verified 29 historical journal hashes and 43 previous workspace artifact hashes. Original v0.1 proposal, runner/parsers, probe planner, annotation importer, codebook, v2 measurement draft and prior capacity report remain unchanged. No independent human ratings were created, and v2 measurement remains inactive.

Full final evidence: `workspace/trajectory-outcomes-20260915-1218/`.
Portable validation: `docs/evidence/trajectory-outcomes-validation.json`.
Reproduction: `PYTHONPATH=. python3 scripts/check_trajectory_outcomes.py workspace/NEW-DIRECTORY`.

No new AI inference, model downloads, cloud spending, WebUI writes, remote publication or scheduled heartbeat occurred in this milestone. The work is saved in a local commit after this record; its identifier is reported in the task response.

## Decisions and next work

The prior all-roots-complete capacity criterion remains failed. A proposal that measures caps as outcomes is a prospective change in question and readiness rationale, not a retrospective pass. The live factorial pilot remains disabled, pending runtime and scientific qualification.

Next engineering package: durably record preflight non-dispatch and unresolved requests, validate a versioned live factorial schema behind explicit readiness, and preallocate probe slots across the entire planned graph. Inspection found that the current engineering probe planner numbers only available snapshots, so missingness shifts later seeds and variants. A research version must skip unavailable slots without renumbering; older probe plans and scores must stay replayable.

Human development remains independently actionable through `docs/RATER-HANDOFF.md`. Resolve expression, referent, stance and contextual continuation, preserve the original semantic screen, and freeze matching software/packets if v2 is adopted. If the screen fails under adjudication, use a separately versioned framing investigation before the main pilot; do not hunt seeds or redefine the old result as positive.

Mechanical repetition neither implies a semantic nonduality label nor verifies an experiential state. A departure from repetition is only a text change. Future main results need all allocated denominators and root-level dependence preserved.
