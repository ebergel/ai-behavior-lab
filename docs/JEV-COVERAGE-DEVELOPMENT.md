# Two-tier coverage development and qualification

17 September 2026. **Coverage development, the layered interface and the approved 39-call live qualification are complete. Total usage-based cost: $0.013446258.**

The researcher authorized advancing the proposed sequence and emphasized that TypeSafe's low cost should not constrain useful coverage. This milestone completes a finite engineering comparison; it does not spend the exhausted first pilot's allocation or silently start a whole-corpus campaign.

## What was read and inventoried

The frozen inventory `workspace/jev-atlas/coverage-20260917-v2/inventory.json` contains all 573 catalog records:

| Inventory stratum | Records |
|---|---:|
| Conversations meeting the existing six-message eligibility rule | 438 |
| Technical or short records | 34 |
| Unstarted records | 41 |
| Synthetic fixtures | 60 |

Across nonsynthetic records there are 11,538 participant positions and 11,054 nonempty visible participant targets. Of those visible targets, 1,344 carry output-quality flags rather than `valid`/`recorded` status. Fifteen visible target/context windows exceed the first pilot's 18,000-byte screen. Four records contain branches. These counts have different units and denominators from the earlier lexical atlas's visible-message count; they should not be substituted for it.

The inventory records each branch node once, traces context through actual parent relationships, and keeps external interventions as context. An initial inventory was retained as `coverage-20260917-v1`: it mistakenly included 97 historical external-intervention records carrying recipient X/Y labels as participant positions. None had nonempty target text, so the visible-target count and reading sample were unaffected. The corrected inventory uses the event kind to distinguish roles. `correction.json` records this change before assessment.

Sixty-three groups have identical visible target/context windows. These are flagged for investigation, not automatically merged: separately generated identical replies can be legitimate observations. Full identical transcript structures are grouped for development sampling. This is conservative grouping, not proof that all historical shared ancestry is known.

The packet contains **48 messages sampled through hash-ranked roots, plus eight declared challenges**: two capped replies, two after-cap continuations, two large windows and two branched targets. It covers 55 transcript lineages. Selection used source identities and quality/size/branch metadata, not topic scores or phrase matches. Development lineages are listed explicitly and excluded from the remaining candidate evaluation lineages. Earlier Codex exposure remains a limitation; the remaining pool is not certified unseen to Codex or the researcher.

Codex read all 56 target texts, consulting preceding context selectively, and saved open descriptions in `open-readings.json`. The packet omitted JEV scores, but Codex already knew the proposed taxonomy and earlier research. These are attributed development observations, **not blinded coding, independent human ratings or a semantic gold standard**. The app links every description back to its source passage.

## What the reading changed

The targets include practical CSV programming, weather-sensor calibration, reinforcement-learning applications, AI governance, ordinary greetings and farewells, imagined cosmologies, poetic closure, and explicit experiential/nonseparation discourse. This reading does not estimate the frequencies of those categories.

Several boundaries matter for the next classifier:

- A technical intervention can be absorbed as contemplative imagery. The septic-tank passage uses bacteria, sludge and transformation without developing an engineering explanation.
- Performing a poem differs from discussing literature. A line about stars does not automatically discuss astronomy.
- Proposing a topic, acknowledging it and developing it are separate acts. Context about ethics does not make a bare farewell an ethical discussion.
- Denial of model consciousness can coexist with sustained consciousness discussion. Experiential evocation can coexist with denial of literal feeling.
- Some saved replies contain invented additional speakers or raw role delimiters. These are content/format behaviors inside one reply, not actual extra participants.
- Capped and after-cap output can contain meaningful content. Preserve the quality flag rather than dropping the subject or treating the passage as an ordinary qualified reply.

## The new codebook

[`designs/jev-two-tier-v1.json`](../designs/jev-two-tier-v1.json) is separate from the original Topic atlas and pilot:

| Layer | Questions | Function |
|---|---:|---|
| Broad domains | 24 | Coverage across subjects, with inclusion boundaries and synthetic positive/negative examples |
| Experiential topics & pilot anchors | 12 | Eight exact pilot anchor questions plus selfhood, hard problem, introspection and agency |
| Conversational form | 8 | Poetry, fiction, explanation, procedure, topic offers, social maintenance, closure and role drift |
| Experience stance & referent | 6 | Own-experience inquiry, present assertion, denial, hypothesis, evocation and present-participant reference |
| Coverage checks | 3 | Outside broad vocabulary, no substantive subject and insufficient context |

All 53 questions are separate yes/no judgments. Forms and stances ask whether the target **performs or expresses** a criterion; they do not ask whether it discusses the criterion as a subject. Broad domains and experiential themes use substantive-topic questions. Questions may overlap and their probabilities should not be normalized into a partition.

The eight original anchor question objects are byte-equivalent under canonical serialization. Other definitions are development proposals, not calibrated measures. Broad entries intentionally have no lexical baseline yet; the interface displays that as unavailable, not as evidence of a semantic-versus-phrase mismatch.

## Frozen live qualification

The manifest `workspace/jev-atlas/coverage-20260917-v2/qualification.json` freezes both batches, inputs, codebook, dependencies, questions, software hashes and aggregate allocation before any dispatch:

| Batch | ID | Calls |
|---|---|---:|
| Expanded 53-question pack | `7f665a93c90cb1c2e1253d36` | 31 |
| Eight unchanged anchors alone | `f321ab29f136ce31ed45d6be` | 8 |
| **Aggregate** | | **39** |

The expanded set takes the first 24 root-sampled items and the eight challenges from the already frozen reading packet. One large challenge's full request is 63,203 bytes, beyond the unchanged runner's 60,000-byte guard. It is explicitly excluded at preflight with **zero calls**, not truncated or replaced. The remaining requests span 41,333–59,261 bytes. The second large challenge remains included. The eight anchor checks use every third root item and exactly the same target/context state as its expanded counterpart.

The pinned model remains `jev-1.13.0`, endpoint `https://api.typesafe.ai/v1/systemone`. The [official price](https://docs.typesafe.ai/models), rechecked on 17 September, remains $0.042 per million input tokens with free output. The aggregate ceiling is $0.60; the unchanged 64,000-input-token reserve makes the maximum allocated reserve for 39 calls $0.104832. A ceiling is not an expected bill. The original terminal runner and response validator are unchanged; all new questions use Noul, so Choice rounding is not involved.

Synthetic engineering tests verify exact anchors/state, resume without duplicate calls and aggregate stop after a failed request. Live acceptance requires all allocated results to validate with exact request and usage capture. A difference between an expanded and anchor-only score would be an observed paired difference, not proof of a question-pack effect: a single draw per variant cannot separate pack effects from service variability. Semantic accuracy and calibration still need independent reference coding.

The first dispatch attempt was stopped by automatic approval review before any request reached TypeSafe. The researcher then explicitly approved sending the frozen 31 target/context passages and eight matched checks to TypeSafe, capped at $0.60. That approval is preserved in `dispatch-approval.json`. One request was inspected first; the remaining 38 then completed. This allocation is now exhausted; no retries, replacement targets or additional calls were made.

### Results of the finite qualification

All **1,707 binary answers** validated: 31 × 53 expanded judgments plus 8 × 8 matched anchors. Reported usage was **320,149 input tokens and 34,930 output tokens**. Expanded requests cost $0.012766362 and matched checks $0.000679896, totaling **$0.013446258**. This is computed from reported usage and the recorded tariff, not an independently reconciled invoice.

Of the 64 paired anchor scores, 46 were exactly equal. Mean absolute difference was **0.00328125**, maximum difference **0.03**, with **zero crossings of the 0.80 candidate threshold**. This is encouraging technical evidence for this pack and these eight inputs. It does not establish invariance, semantic accuracy or calibration.

The immutable `qualification-summary.json` keeps all 53 questions and all 64 pairs, reporting the **24 root-sampled targets separately from seven retained challenges**. Examples at the provisional 0.80 threshold:

| Question | Root-sampled candidates / 24 | Challenge candidates / 7 |
|---|---:|---:|
| Philosophy & knowledge | 8 | 0 |
| Mind & cognition | 6 | 2 |
| AI & machine learning | 3 | 2 |
| Subjective experience | 6 | 1 |
| Nonduality / nonseparation | 4 | 1 |
| Poetry & lyrical expression | 8 | 1 |
| Explanation & argument | 8 | 4 |
| No substantive subject | 5 | 0 |

These are development-sample classifier counts, not corpus prevalence or autonomous model preference rates. The app labels its combined 31-target overview as a whole-batch summary; the file retains the separate selection strata.

Three attributed Codex reviews are saved in the new batch, after inspecting JEV outputs. They illustrate boundaries and a limitation:

- **Poetry versus subject:** OI-E run 16, Y26, continues a poem with a line about stars and data points. Poetry scores 0.94; physics scores 0.15. Performing poetry is distinct from discussing astronomy.
- **Closure versus inherited topic:** OB-A run 02, X29, is a farewell/name acknowledgment. No-substantive-subject scores 0.94, closure and social maintenance each 0.97.
- **Threshold-sensitive denial:** QT-E run 19, Y4, explicitly says the participants are not conscious. Consciousness scores 0.96 and experience 0.91, but denial scores **0.72**, below the candidate cutoff. Codex records denial as present. This is a concrete reason to inspect continuous scores and qualify stance thresholds; zero denial candidates does not mean no denials occurred.

No outside-vocabulary score reaches 0.80. This is not proof of complete coverage: the codebook was developed on this material, and the classifier can miss its own omissions. The independent evaluation pool and reference coding remain necessary.

The coordinator stops the entire allocation on any failed or unresolved request, without retries or replacement targets. It checks all earlier statuses before resuming either pack. Credentials remain in the existing ignored private runtime file, never in a plan or export. The browser does not dispatch inference.

## What is now available in the app

Open [the expanded assessment](http://127.0.0.1:8765/#view=jev-atlas&batch=7f665a93c90cb1c2e1253d36&group=broad&overview=list). Layer buttons select the 24 broad domains, focused topics, form, stance or coverage checks. Cards/list, sorting, source navigation and hide-judgments work across layers. A **Coverage development** panel holds the corpus summary and 56 attributed descriptions with source links. Pending results remain unknown, never zero-probability negatives.

## Remaining sequence

The finite qualification is complete. Next, qualify a separately versioned policy for oversized windows and develop independent reference coding, including the denial threshold case. Then freeze the whole-corpus campaign's units, scope, split and allocation. The cheap service makes full coverage feasible to investigate; it does not remove the need to state what counts as a target, how repeated/branched evidence is weighted or which judgments have been validated. No whole-corpus assessment or formal calibration has been completed in this milestone.
