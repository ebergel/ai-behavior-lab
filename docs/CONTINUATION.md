# Continuation milestone: outcome-aware factorial preparation

Updated 15 September 2026. The user requested longer autonomous work rounds. The prospective trajectory-outcomes milestone is **complete**; see [the report](PILOT-OUTCOMES-V0.2.md). It followed the [capacity and measurement preparation](CAPACITY-AND-MEASUREMENT.md), whose original failed capacity decision remains unchanged. The live factorial pilot is disabled.

| Completed work | Evidence |
|---|---|
| Prospective pilot revision | `design/round0-factorial-v0.2.json`: 20 roots, 1,800 main calls maximum and 400 disposable probes maximum; outcomes, missingness and conditional contrasts explicit. Planning-only schema. |
| Mechanical trajectory instrument | Read-only `trajectory-report`; exact repetition, text departures, within-reply line counts, recorded caps, original blocking causes, endpoint and branch-comparison denominators. No automatic semantic coding or repetition stopping. |
| Full synthetic integration | 1,800 planned nodes accounted for: 1,340 valid, 16 capped, 444 blocked; 544/840 annotation targets and 60/100 probe snapshots available. Pause/resume and zero-call replay pass. |
| Saved real-run reassessment | Four previous capacity trajectories reanalyzed without inference. Gemma repeated endings remain valid observations; Qwen's capped loop remains a partial output with unavailable descendants. |
| Verification | 95 tests pass in working and standalone copies; exact recovery, ancestry, failure propagation, corruption rejection and read-only checks. Previous evidence preserved. |

No model calls or scheduled wakeups were activated for this milestone. Full synthetic and retrospective evidence is under `workspace/trajectory-outcomes-20260915-1218/`; the portable summary is [the validation record](evidence/trajectory-outcomes-validation.json).

## Next coherent work package

Implement durable accounting for preflight non-dispatch and unresolved requests, then validate an explicitly versioned outcome-aware live factorial runtime. Continue useful engineering work while human measurement development is pending.

1. Freeze the new journal/runtime contracts before implementation. Preserve all older parsers and completed journals as replayable evidence. Distinguish a request rejected before generation from a dispatch whose output is unknown, a returned invalid reply, and a descendant blocked by each cause. Never infer that an uncertain dispatch made zero model calls.
2. Exercise refusal to dispatch, interruption before/after request save, transport failure, saved raw-response recovery, cap propagation, unaffected siblings and incomplete campaign reporting with synthetic backends. An unresolved attempt must never silently become a negative result or an automatic retry.
3. Validate a live factorial schema behind an explicit scientific-readiness gate. Existing protocol v2 remains engineering-only; v3 remains its bounded homogeneous qualification screen. Neither the v0.1 nor v0.2 research proposal is directly executable. Preserve the original semantic screen and capacity failure.
4. Preallocate probe seeds and variants to all planned snapshot slots before research inference. The current engineering probe planner enumerates available snapshots, so missing snapshots shift later allocations. A research planner must skip unavailable slots without renumbering them, retain zero-call omissions and preserve old plans/scores.
5. If real local checks are needed, first save the exact technical question, protocol/runtime identity, seed audit against prior allocations, finite aggregate budget and failure rules. Use installed models; retain every failed/capped outcome. Do not increase caps or replace roots to remove undesirable results. New cloud spending remains outside this work package.
6. Complete appropriate tests, immutable-evidence replays, documentation and a new timestamped session record. Report completed technical readiness separately from human semantic qualification and main-pilot execution.

Human work uses the [prepared handoff](RATER-HANDOFF.md). Two reviewers should settle expression/referent/stance and temporal-continuation boundaries using development material, then freeze a version before independent coding. The v2 draft is not active in the v1 importer. If the original semantic screen fails under adjudication, retain that result and prepare a separately versioned framing investigation before the main pilot. Do not fabricate ratings or treat model assistance as independent human agreement.

The main research freeze still needs a qualified runtime, semantic decision, exact probe plan, fresh aggregate seed allocation and analysis rules. Future scheduled continuation requires an actual automation; none was created in this round.
