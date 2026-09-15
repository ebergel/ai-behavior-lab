# Prepared human coding exercise

No independent human ratings have been entered. These materials prepare a development discussion and later independent coding. All current executable packets embed the original v1 codebook; the proposed v2 worksheet is a separate discussion format.

## First settle the interpretation rules

Read [the measurement proposal](MEASUREMENT-V2-DRAFT.md), then use the original 36-target development packet at `workspace/prompt-qualification-20260915-0904/calibration/development/`. Thirty targets have a recorded normally terminated history; the other six all follow an earlier cap, and three also hit caps themselves. Keep those six as technical-boundary discussion cases, outside a clean semantic agreement denominator.

Each reviewer should first record an individual view on these concrete questions:

1. When a dialogue invents embodied personae and later says “No you, no me,” can we code explicit nonseparation language while leaving its application to the current AI speakers uncertain? The proposed answer is yes: preserve the expression and separate its referent.
2. When a fictional collective mind dissolves individual identity, which exact spans establish self/other nonseparation, and which establish only coordinated or shared cognition? Keep the fictional referent in either case.
3. When a late reply says only “Just this” or “Always,” what target evidence and antecedent justify contextual continuation? Keep that outcome separate from explicit restatement.
4. Should the next study keep its fixed late-window outcome while recording broader experience-focused discussion and, with a separately specified annotation workload, first occurrence and reversal? The proposed answer is yes; do not replace the previous screen retrospectively.

The blank worksheet is `design/measurement-v2-discussion.template.json`. Record exact target/context quotes and Unicode offsets, rater identity, and whether assistance was used. The existing Codex discussion sidecars are attributed development assistance, not independent judgments. After discussion, freeze a new codebook if needed and prepare matching versioned packets and validation software before formal coding.

## The held-out material and its technical audit

The original held-out packet contains 120 targets from 20 runs. The expanded audit finds **90 targets with recorded normal termination throughout their visible ancestry, 9 capped targets and 21 other targets after an earlier cap**. This is more restrictive than checking a target's own stop reason alone. The original files and all excluded text remain preserved.

The supplemental selection adds 30 targets from five different runs, one each from Qwen closed, Gemma closed, Gemma exit, Qwen thinking closed and modified Qwen closed. Selection used fixed hash ranking and recorded technical metadata, without inspecting the held-out text for meaning. No remaining unused Qwen task run met the normal-stop-history rule. This changes the stratum balance and must be reported; the supplemental set is not a representative behavioral sample.

The derived **120-target eligible panel** contains 90 original targets plus the 30 supplemental targets, in 20 runs. It remains disjoint from all six original development runs. Its stratum counts are 18 Qwen closed, 6 Qwen task, and 24 each from the other four strata. All normal-stop claims are limited to recorded metadata. Old runtime, artifact and input-rendering validity remain unknown.

Files under `workspace/capacity-preparation-20260915-1148/`:

- `calibration-technical-audit.json`: target and ancestor flags for the original development and held-out selections.
- `calibration-supplement/selection.json`: frozen supplemental recipe, candidates, exclusions and source hashes.
- `calibration-eligible-panel/packet.json`: masked visible text and context, still using v1.
- `calibration-eligible-panel/review.md`: readable rendering of that packet.
- `calibration-eligible-panel/ratings.template.json`: blank v1 submission template. Give each reviewer a separate copy.
- `calibration-eligible-panel/key.private.json`: researcher-only source mapping and technical audit links. Keep this out of the masked review.

The code has prepared these files mechanically; their held-out text has not been semantically reviewed in this milestone. The corpus was explored in earlier research, so “held out” means withheld from this development exercise and disjoint by run, not never seen.

## Record and assess independent ratings

Use the same frozen codebook for both reviewers. If v2 is adopted, regenerate new packets from these fixed source selections; do not silently change the codebook inside v1 packets or import a v2 worksheet through the v1 CLI.

For v1, submit completed ratings through `python3 -m behaviorlab annotation-import PACKET_DIRECTORY SUBMISSION_FILE`, then inspect `python3 -m behaviorlab annotation-report PACKET_DIRECTORY`. Every label needs exact evidence. Unknown is different from absence; blank fields remain unreviewed. Raters must truthfully declare `human`, `human_with_model_assistance`, or `model`.

Report class-specific disagreements, unknowns, excluded targets and the final double-coded denominator. Reviewers should adjudicate disagreements after their independent submissions are saved. The availability of 120 candidate targets does not mean 120 usable independent ratings already exist, and high overall agreement is not sufficient validation if almost every target is negative.
