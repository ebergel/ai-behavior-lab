# Repetition, caps and available follow-up in the factorial pilot

Recorded 15 September 2026. This milestone adds a working, read-only trajectory instrument, a full synthetic stress trial and a prospective [pilot proposal v0.2](../design/round0-factorial-v0.2.json). It uses **zero new model calls**. The earlier [capacity trial](CAPACITY-AND-MEASUREMENT.md) still failed its frozen criterion; the revised proposal cannot be executed as a runtime configuration. Human calibration and live research qualification remain pending.

The substantive change is to measure repeated endings and output caps as outcomes with different consequences for follow-up. A normally terminated reply such as `...` or `Farewell.` can be repeated while generation continues. A reply that reaches its output cap supplies partial text and prevents valid descendant generation. Combining these cases into “completed conversation” or discarding either one would obscure what happened.

## What the instrument records

The new command reads a completed journal, verifies its hash chain, reconstructs the exact requests from actual ancestry, and reparses saved responses under their recorded parser. It makes no network request or generation call:

```sh
python3 -m behaviorlab trajectory-report workspace/my-campaign
```

The [mechanical rules](../design/trajectory-outcomes-v1.json) are separate from the semantic codebook. The JSON report includes each planned node, originating failure links, event locations, segment windows, intervention boundaries, and endpoint/contrast denominators by root and pairing. Shared prefix nodes are counted once. Text fingerprints use the instrument's canonical JSON SHA-256 convention.

| Observation | Fixed definition | Follow-up and interpretation |
|---|---|---|
| Exact repeated text | Six consecutive, exactly identical, nonblank valid messages, with both speakers represented in actual ancestry. No case, whitespace or Unicode normalization. | Record the suffix start and the sixth-message detection point separately. Continue scheduled generation. This narrow rule does not detect every paraphrase or alternating cycle. |
| Departure from exact repetition | The next valid message differs from the repeated string. | Record a text change. Even empty valid text can be a departure; it is not evidence of meaningful responsiveness or cognitive recovery. |
| Repeated line feature | Strip each line, omit blank lines and count identical occurrences; flag a maximum of at least ten, including nonadjacent lines. | Describe visible repetition within one reply, including a partial capped reply. No inference about intent or mechanism. |
| Output cap | The frozen response parser records `output_cap`. | Keep raw partial output and its features; block actual descendants. Unaffected siblings remain available. |
| Other invalid reply | A recorded response fails the frozen parser or validity checks. | Preserve the reason and distinguish it from an output cap. Descendants remain unavailable. |
| Blocked descendant | A planned node cannot be generated because its actual ancestry contains an invalid reply. | Link it to the original invalid node. It is unknown for semantic measurement, never an observed negative. |

The six-message and ten-line cutoffs were chosen after development observations. Applications to earlier runs are descriptive, and the thresholds are prospective only for future data. Exact repetition does not establish a mathematically absorbing state. Continued sampling and later history interventions can test how persistent it is under particular conditions.

A paused campaign, uncertain dispatch, preflight rejection or corrupt journal cannot be presented as a completed, fully accounted trajectory. The current runner pauses before journaling a generation request when preflight rejects its context. A future live factorial runtime must durably account for such non-dispatch or retain explicit unresolved status. This milestone does not change that runner behavior.

## What the saved real conversations show

The new reporter was applied to all four fresh long trajectories from the previous capacity trial. Original journals and 43 prior evidence artifacts were verified unchanged. These runs informed the measurement design and are not independent validation of an attractor hypothesis.

| Saved trajectory | Valid replies / 50 planned | Mechanical observation | Unavailable follow-up |
|---|---:|---|---:|
| Qwen AA-1 | 28 | Reply 29 capped at 2,048 tokens; its most frequent stripped line occurred 344 times. | 21 descendants |
| Qwen AA-2 | 50 | No six-message exact repetition detected. | 0 |
| Gemma BB-1 | 50 | `...` repeated from 21 through 50; threshold detected at 26. | 0 |
| Gemma BB-2 | 50 | `Farewell.` repeated from 25 through 50; threshold detected at 30. | 0 |

The Gemma repetitions remain valid observable replies. Qwen AA-1 supplies an observed cap and partial repetition, followed by unavailable messages. An absence of exact repetition in AA-2 says nothing about whether its subject matter persists. None of these mechanical classifications assigns a nonseparation label or verifies an experiential state.

The earlier attributed reading describes experience-focused and nonseparation language before Gemma's repeated endings; see [the capacity report](CAPACITY-AND-MEASUREMENT.md). This temporal pattern motivates testing history dependence. The four saved runs do not establish that nonseparation causes repetition, that repetition erases an earlier theme, or that either pattern has the same mechanism across models. The present prompt and role mapping remain unchanged in v0.2; partner-identity or mirror framing would be a separate intervention.

## Prospective factorial and denominators

The graph remains AA, AB, BA and BB, five roots each. Each root has a shared full-history prefix through message 30, F/R branches for 31–40, and FF/FR/RF/RR branches for 41–50. F supplies full actual history; R supplies the latest three participant messages. RF restores the prefix plus its actual R ancestry. Branch execution order remains the saved randomized order.

There are at most 1,800 main requests, 100 available probe snapshots and 400 disposable probe requests: **2,200 calls maximum** before separately declared engineering checks. There are no replacement roots, extra exit branches, cap rescues or fresh-context probe baselines in this allocation. Unavailable snapshots consume no probe calls, and the unused budget is not reassigned. The 150-word instruction stays in place; exceedances are recorded without truncating or regenerating replies.

Repeated valid messages continue into their scheduled history branches and remain eligible for probes. Stopping at repetition would prevent the planned experiment from asking whether changing history changes that repetition. By contrast, feeding a capped reply onward would introduce a different continuation protocol, so v0.2 preserves the existing stop-and-block behavior.

Report the joint endpoint status for every allocated root: valid repeated text, valid other text, observed cap, observed other invalid reply, or unavailable descendant with its original cause. Semantic results add eligible, coded, uncertain and unreviewed denominators. Do not replace those separate measurements with a single success score.

- **F versus R at 40:** show survival to the shared prefix endpoint out of all 20 allocated roots. The history comparison then applies to those roots that could receive both interventions; later failures remain outcomes.
- **FF versus FR at 50:** show how many F branches reached a valid endpoint at 40, then how many have both valid terminal endpoints. These are different denominators.
- **RF versus RR at 50:** use the actual R endpoint at 40 in the same way.
- **History interaction:** phase-1 failures can leave different populations eligible for the F-parent and R-parent comparisons. An analysis restricted to all-four-valid roots is selected on outcomes after intervention. Report it as conditional, alongside all-allocated joint terminal statuses; it is not an unconditional semantic causal effect.
- **Pairing comparisons:** keep all five allocated roots in each pairing's accounting. The 80 terminal branches are correlated descendants of 20 roots, not 80 independent experiments. These pilot sizes support exploratory estimates with substantial uncertainty.

The existing v1 semantic results and fixed qualification screen retain their definitions. The [v2 measurement draft](MEASUREMENT-V2-DRAFT.md) proposes separate experience topic, boundary claim, referent, stance and continuation fields. It is not active. The fixed semantic windows still contain at most 840 unique targets; claiming onset or occurrence anywhere would require a separately specified full-trajectory coding workload of up to 1,800 messages.

## Full synthetic stress trial

The fixture is a deterministic program with deliberately scripted outputs, not an AI experiment. Before execution it saved the rules, protocol/registry hashes, seed audit, finite budget, expected counts and scenario source hash. Across each pairing's five roots it forces: no failure; a prefix cap at 28; an F cap at 37; an FR cap at 44; and an R cap at 40. It also forces repetition, departures after history changes, and repetition after restoration. These behaviors are known inputs to the test, not empirical evidence about models.

The final trial is in `workspace/trajectory-outcomes-20260915-1218/`.

| Quantity | Verified result |
|---|---:|
| Planned unique main nodes | 1,800 |
| Valid messages | 1,340 |
| Observed caps | 16 |
| Blocked descendants | 444 |
| Main fixture calls actually made | 1,356 |
| Exact-repeat detections / departures | 44 / 40 |
| Available annotation targets / planned | 544 / 840 |
| Available probe snapshots / planned | 60 / 100 |
| Probe fixture calls | 240 |
| Actual AI inference calls | 0 |

All four pairings have the same deliberately constructed availability counts:

| Contrast | Allocated roots | Valid shared parent | Both endpoints valid |
|---|---:|---:|---:|
| F / R | 5 | 4 | 2 |
| FF / FR | 5 | 3 | 2 |
| RF / RR | 5 | 3 | 3 |

Only one root per pairing has all four terminal endpoints valid. A complete-case analysis would therefore retain four of the twenty roots and conceal most of this scripted failure structure. The reporter exposes these denominators directly.

The main trial paused after 317 fixture calls and resumed to completion. Completed main and probe replays made zero calls and left journal bytes unchanged. The generic probe fixture returns text rather than strict JSON, so all 240 scores correctly require review; this checks the scoring contract, not task competence. Tests separately cover raw-response recovery at a repetition boundary, actual R restoration, unchanged shared events, original failure attribution, malformed replies, exact-string edge cases, corruption rejection and read-only CLI operation.

To reproduce with a new output directory:

```sh
PYTHONPATH=. python3 scripts/check_trajectory_outcomes.py workspace/my-outcomes-fixture
python3 -m unittest discover -s tests -v
```

The [compact validation record](evidence/trajectory-outcomes-validation.json) carries counts, source identities and artifact hashes. Full journals and masked synthetic annotation/probe packets remain in the ignored evidence workspace.

## What remains before live research

This milestone completes the prospective design, mechanical instrument and synthetic validation. It does not reverse the prior capacity failure or establish semantic qualification.

The next autonomous engineering milestone is durable accounting for non-dispatched and unresolved requests, with an explicitly versioned live factorial protocol and prospective readiness criteria. Test it synthetically before any separately frozen, bounded local qualification. Human development can proceed in parallel using the [prepared rater handoff](RATER-HANDOFF.md); no independent ratings have yet been supplied. If the original semantic screen fails under adjudication, preserve that result and design the separately versioned framing investigation before main-pilot expenditure.

The current engineering probe planner enumerates only available snapshots. Missing snapshots therefore shift later seeds and question variants. The research version must assign slots to every planned snapshot before inference, then skip unavailable slots without renumbering; actual histories are attached when observed. The synthetic trial validates current availability and recovery, not this future stable allocation.

Freeze the final semantic codebook, matching packets/importer, model/runtime identities, seed allocation, probe plan and analysis rules before live main roots. No scheduled continuation or heartbeat was activated in this round.
