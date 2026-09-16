# Session record — cost prediction calibration

Recorded: 2026-09-16T10:01:27.058814-03:00 (America/Argentina/Cordoba).

The user requested updated predictions after observing $0.1425 for the completed mini/Haiku batch. Recalibrated planning figures using the immutable journal's actual bill, completion lengths and per-root growth in prompt tokens. This was a read-only calculation; no inference, provider metadata requests, credential access, budget changes or new experiment execution.

Measured baseline: 8 conversations × 12 messages = 96 calls, $0.14248480. Mini: $0.00938580 across four roots. Haiku: $0.13309900 across four roots, 93.4% of the total. Mini reported 15,616 cached input tokens; the measured bill preserves their discount. Projected additional input uses the saved undiscounted price.

Balanced future planning estimates, evenly split by model and condition:

| Conversations | Messages each | Projected cost |
|---:|---:|---:|
| 40 | 12 | $0.71 |
| 8 | 30 | $0.68 |
| 40 | 30 | $3.38 |
| 100 | 30 | $8.46 |
| 40 | 60 | $12.00 |

These point estimates retain each root's measured twelve-message bill, then extrapolate completion tokens at its observed mean and prompt tokens at its observed mean increment. More roots scale linearly; longer full-history conversations accumulate repeated input cost. They are not confidence intervals or enforced spending ceilings. Different prompts, output lengths, reasoning, routing, stopping policy or prices require revised assumptions. The older forty-root thirty-message plan differs in controls and remains held; the projection is a planning analogue, not a guarantee or authorization to execute it.

Added `scripts/estimate_participant_costs.py` and its output `docs/evidence/participant-cost-calibration.json`. Updated the existing comparison report, README and continuation document. The cost section is available with the comparison report in Explorer Results. Frozen plans, runner dependencies, old session records and source transcripts were preserved.

Verification: all 145 standard-library tests pass. The calculator reproduces the measured bill, linear same-length scaling and displayed thirty/sixty-message totals; saved JSON matches a fresh calculation. Verified the final source bytes and all 101 earlier artifact hashes unchanged. Inference dispatch was patched to fail during the calculation check. Git whitespace check passes. No UI behavior changed.

No inference or scheduled continuation is running. Existing $1 and $5 frozen spending controls were preserved. Future planning should distinguish empirical expected cost from an authorized maximum. This new timestamped record does not replace earlier records.
