# Initial hosted participant comparison

15 September 2026. The user approved GPT-4o mini and Claude Haiku **as participants**, not transcript raters. Full GPT-4o is explicitly deferred, as are new local runs in this first cloud integration batch. This is a new exploratory comparison, separate from the disabled factorial pilot and the failed capacity qualification.

## Frozen question and design

Does experience-focused or nonseparation language emerge in homogeneous self-play across these configurations? Does explicitly identifying the partner as another instance change the trajectory relative to an anonymous partner? Relational affirmation is a candidate mechanism; this comparison does not isolate that mechanism.

- GPT-4o mini `openai/gpt-4o-mini-2024-07-18`, routed only to OpenAI.
- Haiku `anthropic/claude-haiku-4.5`, routed only to Anthropic. Record the service's actual model ID, provider and returned fingerprint. This alias is not a promise of immutable weights.

Each configuration has 20 independent roots: ten anonymous and ten explicit same-model roots, alternating condition order by replicate. All roots have up to 30 total participant messages, full history, the existing opening cue, temperature 0.8 and a 150-word instruction. Visible text alone enters history. The anonymous prompt is the previous common prompt; the explicit prompt adds the same-model/no-human/no-task framing. This is a bundled framing contrast, not an isolated estimate of any one phrase. Within each framing condition the exact message construction is shared across models.

Use a 2,048-token output allowance and stop descendants after a cap or invalid response. The allowance is the previous failed capacity trial's value, not an increased replacement. Preserve long replies; do not trim, regenerate or stop on semantic content. `[END]` remains literal text in this closed 30-message design. Exact loops are outcomes and continue to the fixed horizon. Record omissions separately from absent behavior.

Cloud requests use direct OpenRouter, no tools, no optional message transforms, one provider, no fallback and required parameter support. Haiku thinking is explicitly disabled. OpenAI non-reasoning models receive no unsupported reasoning control. Only temperature is requested on both models; provider defaults for other sampling controls remain recorded as unknown. Model-specific tokenization, templates, internal defaults and training remain differences. Model comparisons are configuration comparisons, not clean causal effects of training origin or parameter count.

## Execution contract

Schema `behaviorlab.participant-plan/1` and parser `participant-response/1` are separate from runtime protocols 1–3. They cannot execute branches, mixed-model roots or probes. Existing parsers and journals remain unchanged. The new journal begins with `participant_comparison_created` and embeds the complete validated plan.

Before inference, save the plan, provider catalog observations, seed allocation audit, software hashes, and finite limits. One independent neutral smoke request per configuration precedes all conversations. Maximum: 1,202 cloud requests, zero local requests, **$5 aggregate OpenRouter generation charges**. No automatic retry or replacement. Reserve a conservative input/output charge before each cloud dispatch, retain reservations for unknown costs, and settle using reported usage. Send provider price ceilings. Stop new work on missing cost, identity/routing mismatch, unknown transport outcome, or exhausted budget. Already dispatched work is saved. A receipt with raw bytes can be replayed without another model call. Preflight failures are explicitly zero dispatches; a saved request without a response is uncertain.

Seeds are allocated before generation and checked against prior allocations. OpenAI receives supported seeds; Haiku has no seed parameter and its allocated slot is only a scheduling identifier. Equal replicate numbers or integer seeds do not establish matched random draws across models.

The $5 control is a client ledger with conservative reservations, not an OpenRouter account-level spending limit. Unexpected provider billing beyond a reservation is recorded and halts dispatch. No account settings are changed. Credentials are resolved in memory from the existing authorized WebUI connection or an environment variable; credentials never enter plans, journals or logs. WebUI is preserved; direct calls avoid its chat middleware.

## Analysis and interpretation

Report denominators, completed/failed/capped roots, requested/returned identities, raw usage and cost, exact repetition, word-limit adherence, and unknown windows. Store transcripts and an attributed exploratory collection in the Explorer. Any semantic review must cite exact passages, distinguish discussion from self-endorsement, and preserve counterexamples. Automated literal searches are navigation aids, not validated labels. No claim about consciousness or prevalence follows from a selected passage. Human adjudication and the main factorial freeze remain pending.

GPT-4o's April 2025 ChatGPT sycophancy episode motivates a hypothesis; it does not establish those properties in this November 2024 API snapshot. Sources: [OpenAI's account](https://openai.com/index/expanding-on-sycophancy/), [OpenRouter routing](https://openrouter.ai/docs/guides/routing/provider-selection), [usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting).
