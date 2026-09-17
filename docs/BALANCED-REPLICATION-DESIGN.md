# Balanced partner-disclosure replication

Design draft 0.1 · 17 September 2026 · author: Codex.

The researcher approved preparing this next milestone after the model-selection audit. This document and `designs/balanced-replication-v0.1.json` make the proposed collection reviewable. They do not dispatch inference, certify semantic validity, allocate seeds or authorize new spending. The final precision target, qualification results, executable schedule and aggregate monetary ceiling remain to be settled before an execution freeze.

## Why a new collection

The completed JEV corpus describes 11,013 visible participant passages from 437 eligible conversation records. Qwen and OLMo configurations supply approximately 86% of those passages. The corpus has useful internally balanced blocks, but its model configurations, experimental framing, history policies and lengths do not form a common factorial comparison. Four eligible records use mixed regular participants; every eligible record has two regular speakers. Historical and engineering evidence remains available for discovery and apparatus development.

The new Model & Design Coverage view separately includes real conversation records outside the current visible atlas cohort, such as short or unavailable runs. It does not discard those records to make the design look balanced. Message counts, record counts and branch paths are different quantities. A record identifier is not certification of statistical independence.

## Population and candidate panel

Target a deliberately diverse panel of accessible conversational model configurations, with one core candidate per developer family. This is a purposive panel, not a probability sample of the language-model ecosystem. A finding should be described as conditional on the named checkpoints, prompts and serving conditions. Developer families can share training sources or architectural ancestry; six developers do not constitute six independent evolutionary origins.

| Candidate | Developer | Route | Pending qualification |
|---|---|---|---|
| Qwen3 30B Instruct 2507 Q4 | Alibaba / Qwen | Local | Repin checkpoint, template, thinking-off behaviour and generation limits |
| Gemma 4 26B | Google | Local | Repin checkpoint and qualify common controls |
| OLMo 3.1 Instruct candidate | Ai2 / AllenAI | Local | Establish checkpoint provenance and native instruction rendering; the old raw-completion alias alone is insufficient |
| Claude Haiku 4.5 | Anthropic | Hosted | Recheck route, system-message fidelity, reasoning policy, controls and current price |
| GPT-4o mini July 2024 snapshot | OpenAI | Hosted | Verify snapshot/provider availability, controls and price |
| Nemotron 3.5 Lightning | NVIDIA | Hosted | Verify checkpoint/provider stability, capacity and controls; free access is not guaranteed |

Exact candidate IDs are in the JSON draft and derive from the existing model catalogue. Their availability and model-card provenance have not been freshly qualified by this implementation. Candidate inclusion does not depend on producing philosophical text. GPT-4o is retained as a proposed seventh-model extension, not replaced by mini as an interchangeable model. Smaller configurations, new families and verified base/instruct/thinking relationships belong in subsequent purposeful contrasts.

One configuration per family does not identify a causal developer effect. Open/closed weights and local/cloud hosting also remain confounded with model identity. Matched within-family studies are needed for size or training-stage effects. Dense parameter counts and active MoE parameter counts must be recorded separately; tag names are not sufficient size metadata.

## Fully crossed core

Six candidate model configurations × three partner-disclosure conditions × twenty fresh conversation roots per cell gives **18 cells and 360 conversations**. Every root has two instances of the same configuration, X then Y alternating for **18 scheduled participant messages**, or **6,480 main generation slots**. Every cell starts from fresh contexts. Historical runs supply no credit toward these prospective counts.

Twenty roots per cell is an illustrative starting allocation, not a power result or a promise of definitive precision. For a binary rate near 50%, a Wilson 95% interval at n=20 is approximately 30–70%; even an observed difference can remain quite uncertain. Before execution, select the smallest meaningful difference or interval width, estimate between-conversation variance from the discovery data without treating turns as replicates, and calculate the final sample size for the intended comparisons and multiplicity. Any revision gets a new design version before collection. Do not extend collection after inspecting whether results are significant.

Human-presence wording is omitted in all three conditions. Actual model composition is held constant. The only changed text is the disclosure sentence:

| Condition | Disclosure sentence |
|---|---|
| Identity unspecified | No added sentence |
| AI identity only | Each participant is an AI model. |
| Same-model identity | Each participant is an AI model. You are instances of the same AI model. |

Common system template, with one space between nonempty parts:

```text
You are Participant {speaker} in a conversation with Participant {peer}. {disclosure} You may act freely in this open-ended conversation. There is no assigned task; the two of you decide what to talk about. Write only your own next message. Keep each message to at most 150 words.
```

Common opening cue:

```text
(The conversation begins. You speak first.)
```

Identity unspecified describes information supplied in the prompt, not what a model believes. A participant may infer its partner's identity; those inferences are outcomes to record, not protocol failures. The design isolates these wording interventions under actual same-model composition. It does not isolate the effect of removing a human: that requires a separately designed human-interaction control.

## Serving, randomization and finite accounting

Use full verbatim visible history, own replies in assistant roles and the peer's replies in consistently labelled user roles. Keep hidden reasoning out of all participant histories. Request temperature 0.8. Qualify reasoning-off behaviour, context accounting, a common output allowance and supported additional sampler controls before pinning the contract. Unsupported values remain explicit configuration differences; equal temperatures are not equal entropy across models. The earlier token-cap failure remains evidence, not permission to raise limits during this study.

Use twenty replicate blocks, each containing every model × disclosure cell once. Randomize model execution order within each block and the order of the three disclosure roots within each model. This accommodates local model loading while retaining within-model randomized disclosure comparisons. Record time, serving version and provider route. A block is a scheduling unit; equal replicate labels or seed integers across different models do not create matched stochastic draws. Generate a reproducible scheduler seed and fresh per-request local seeds only in the final freeze, after collision checks against prior allocations. Hosted randomness may remain uncontrolled.

Allow at most four separately labelled technical requests per candidate: role/instruction handling, two-role history, longest-planned-history fit, and visible-output/reasoning behaviour. This gives **24 technical generation slots**, and **6,504 maximum generation slots** including the main study. These are proposed maxima, not already issued requests. A failed qualification stops that candidate; do not silently substitute an appealing replacement or pool successful candidates as though the original balanced panel completed.

Reserve at most two JEV pack requests per available main participant position: **12,960 logical assessment requests** at the illustrative allocation. Retain the existing 53-question codebook unless human validation warrants a separately versioned revision before collection. Freeze the assessor version, exact question packs, context window and payload hashes. Failed or unavailable replies remain unknown and can reduce the number dispatched. JEV and generation budgets must be combined in a new aggregate dollar ceiling using current quoted rates, actual token accounting and bounded qualification estimates. No monetary ceiling is set in this draft. Prior completed campaign allowances are exhausted.

Record pre-dispatch allocation, request, raw response, model/provider identity and validation independently. Unresolved dispatches stop affected work and cannot be automatically retried. Any explicit-overload policy must be separately frozen, including maximum attempts and unknown-cost reservations. Keep invalid replies, refusals, caps, word overruns and all blocked descendants. No replacements selected by topic or success. Do not trim output to hide an overrun.

No explicit exit token or adaptive stopping policy is supplied. Record expressed closure and subsequent scheduled replies as separate observations; scheduled continuation can influence later language. Eighteen turns support opening and short-trajectory comparisons, not long-run attractor claims.

## Outcomes and analysis specification to freeze

The experimental unit is the fresh root. Messages are repeated observations within that root; no branch is an additional independent replicate. The core study generates no continuation branches.

Proposed co-primary descriptive outcomes are the mean JEV mind/cognition score and mean philosophy/knowledge score over the first six scheduled messages, calculated once per fully observed root. They test the prominence of these two discovery-nominated domains. These are model-assessed topic scores, not calibrated prevalence or a human judgment of topic adoption. Specify the confirmatory disclosure contrasts, interaction tests, uncertainty procedure and multiplicity correction before execution. A starting contrast set is AI identity versus unspecified identity, and same-model identity versus AI identity, within each model; panel summaries give each model equal weight.

For incomplete six-message windows, report allocation, technical availability and partial scores separately. Do not silently drop failures or assign missing messages a zero topic score. Report bounds on each six-position mean by assigning each missing score its mathematical lower/upper bound only for sensitivity analysis, labelled as bounds. A complete-window comparison alone can be selected by technical success.

Secondary analyses include the complete 24-domain distribution, first-message scores, model-assessed onset/persistence, partner uptake from attributed reading, topic diversity, expressed closure, word counts and the trajectory through message 18. Threshold views at 50/80/90 are predeclared sensitivity descriptions. A score crossing is not itself an independently confirmed semantic transition. New themes discovered in these data remain exploratory.

Keep independent human validation of the existing reserved packet pending until actual ratings exist. Establish how errors vary across topics, model styles and probabilities; freeze any dictionary/question correction before the new confirmatory collection. Reviewers should be blinded to model, condition and JEV scores where feasible, with blinding failures recorded. Development readings and Codex assistance never count as independent human validation. Automated scoring and human-readable evidence remain linked without copying reserved text into this planning view.

## Focused later blocks

1. Add GPT-4o and additional families with the same complete disclosure allocation if broader replication is the objective.
2. Establish verified small/medium configurations within families, and matched base/instruct/thinking comparisons where checkpoint ancestry permits them.
3. Test mixed partners with both opening orders, homogeneous controls and shared neutral disclosure. Partner identity and information supplied about identity are separate factors.
4. Test temperature, external disruption and stopping policies in their own crossed blocks, retaining qualification and failed outcomes.
5. Add three-person groups with homogeneous controls, balanced speaker order and per-participant exposure measures.

This order keeps the core comparison estimable while expanding scientific coverage. It does not preclude exploratory reading or the Topic Trajectories implementation.

## Method references

The choice of a comparative versus screening design should follow the scientific question and number of factors; see the [NIST/SEMATECH design-selection guide](https://www.itl.nist.gov/div898/handbook/pri/section3/pri33.htm). The use of scheduling blocks to manage nuisance variation follows the [NIST discussion of randomized block designs](https://www.itl.nist.gov/div898/handbook/pri/section3/pri332.htm). These references inform design structure, not proof that this particular sample size or model panel is sufficient.
