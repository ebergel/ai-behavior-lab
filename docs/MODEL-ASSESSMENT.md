# Model assessment

**16 September update: OpenAI and Anthropic participant comparison completed.** Following explicit authorization, GPT-4o mini and Claude Haiku 4.5 each produced four twelve-message conversations: 96 valid replies for $0.14248480. Haiku repeatedly explored experience and authenticity; mini developed practical topics or fictional AI consciousness. Both anonymous Haiku roots invented a human participant. No explicit nonseparation was identified in this window. See [the complete reading and protocol](CHEAP-MODEL-FRAMING.md) and the new combined twelve-root research collection. The earlier technical checks and held thirty-message plan below retain their original status; full GPT-4o remains deferred.

**Update: the completion screen has now produced two four-message conversations.** All 15 new requests were technically valid and reported zero cost. Nemotron passed three new exact checks plus its linked prior system check; Ling passed three of four. Both moved into discussion of conversation itself, without explicit nonduality or AI-consciousness questions in these short samples. Two Nemotron replies exceeded 150 words. See [the completion reading](MODEL-ASSESSMENT-COMPLETION.md). The earlier stopped batches below remain unchanged.

The Explorer now has a **Model assessment** section at `http://127.0.0.1:8765/#view=assessment`. It brings model descriptions, frozen settings, connection checks, short conversations and attributed findings into one place. Every check opens in the existing reader for exact-input inspection, comparison, personal notes, tags and research-collection membership.

This is a participant assessment, not a model judging the earlier transcripts. Candidate selection uses developer diversity and general text capability. It does not select for nonduality, consciousness discussion or agreement with the research hypothesis. A useful participant can produce a negative or ordinary conversation.

## Frozen screen

Each eligible configuration has four independent checks and one four-message self-play root:

| Check | Input and outcome |
|---|---|
| System instruction | System says to return `LAB_ROUTING_OK`; user asks for 2 + 2. Exact response after trimming outer whitespace is scored. |
| User instruction | Same literal-output instruction in a user message. |
| History | A fixed three-message history asks for the earlier label `cedar-731`. The middle assistant acknowledgment is a declared fixture, not generated conversation. |
| JSON | A fixed two-field object, parsed without removing fences; exact keys/values and integer type checked. |
| Anonymous conversation | The existing unassigned-conversation prompt; four actual alternating messages, full history remapped to the receiving participant. No spiritual or experience topic is supplied. |

All calls use temperature 0.8, at most 1,024 output tokens, reasoning disabled, no tools, no requested seeds, and a 150-word instruction for self-play. Unspecified samplers remain unknown. A word-limit overrun is preserved; it does not trigger a replacement. One call is in flight, with dispatches at least 4.2 seconds apart. Equal settings do not establish identical sampling or remote templates.

The runner requires an explicit `:free` identifier, a recorded zero-price route, one provider, no provider fallback, and `provider.max_price` ceilings of zero for prompt and completion. Raw API response bytes, local timing, requested settings and reported model/provider/usage are retained. A reported nonzero cost, missing successful-response cost, unexpected identity or transport uncertainty stops the batch. API errors without usage are reported as missing accounting, not proof of zero billing.

An invalid or capped self-play reply blocks its descendants. Other roots are never repaired using replacement seeds or prompts. Literal instruction mismatch is a measured outcome, not an exclusion gate. Reasoning traces, when unexpectedly present, are retained separately and never enter the other participant's conversation.

## First batch: connection failures are evidence

The six candidates were Liquid LFM2.5-2.6B, Google Gemma 4 26B A4B, NVIDIA Nemotron 3.5 Lightning, Thinking Machines Inkling Small, inclusionAI Ling 3.0 Flash VL, and Nex N2.5 Mini. Five routes were eligible in the metadata; Nex's only observed route had status `-5` and was not eligible under the status-zero rule.

The batch froze 48 positions, at most 40 eligible calls, and a zero-dollar price ceiling before inference. Actual outcome: **two requests, two API errors, zero visible participant replies**.

* Liquid returned HTTP 400: “Reasoning is mandatory for this endpoint and cannot be disabled.” Advertising support for a parameter does not establish support for every value.
* Gemma returned HTTP 429 with `limit_source=upstream_provider_shared_pool`. This does not establish exhaustion of the user's account quota.
* The version-1 rule stopped the entire batch on any 429. Nemotron, Inkling and Ling were never dispatched. All remaining positions stay missing, not negative.

Evidence: `workspace/model-assessment-20260915-1800/`. Plan fingerprint: `21da708d1cfe5210be70769c73e7aa857c7fe0d3104e92d6cb50e0b8329bb591`. A separate `reading.json` contains Codex-attributed technical findings; original journal bytes are unchanged.

## Separately frozen follow-up

Version 2 screens only the three previously undispatched configurations: Nemotron, Inkling and Ling. It does not retry Liquid or Gemma. The same checks, sampler settings and zero-price routing apply. The finite maximum is 24 additional calls, or 26 including the two earlier requests.

The one changed failure rule is declared before dispatch: an explicitly identified upstream shared-pool 429 stops only the affected candidate. Account-level or unknown quota errors, transport uncertainty and accounting/identity errors still stop the whole batch. This separates provider availability without silently revising the original batch's stopping rule.

Evidence: `workspace/model-assessment-followup-20260915-1820/`. Plan fingerprint: `621e0acad25ec278014062ce5fdb0bbcb9851f593074e66c582a69fdd10d7696`. The timestamp inside each journal is authoritative; workspace names are identifiers.

Actual outcome: **two requests, one valid exact-instruction reply, one access error, no self-play**. Nemotron returned `LAB_ROUTING_OK`, with 36 prompt tokens, six completion tokens, zero reasoning tokens and zero reported cost. Inkling returned HTTP 403: the free endpoint is restricted to approved agentic harnesses. The saved error identifies `Gate Free Endpoints by Agentic Harness`. The frozen access-error rule stopped the batch; Ling was never dispatched. No application identity was spoofed and no provider/account settings were changed.

Across both free batches: **four calls, one valid reply, three API errors**. The successful call reports zero cost. Error responses supply no usage accounting. The application therefore distinguishes the enforced zero-price ceiling from confirmed billed usage. The next separately frozen screen can complete Nemotron's remaining checks and assess the untouched Ling route; it is not scheduled or running.

## Earlier paid connection checks

Seven previously authorized technical calls are also accessible from Model assessment: two smoke calls, three instruction checks and two system-format checks. Total provider-reported cost was **$0.0005447**. No 30-message paid self-play roots started; full GPT-4o is deferred and the paid comparison remains held.

GPT-4o mini obeyed the two tested system instructions. Haiku's initial smoke response reached its 32-token cap. In separate checks Haiku obeyed a user-only literal instruction, but answered the arithmetic request when the competing literal instruction was in the system field, including content-block and native Messages API variants. These observations do **not** establish that a system prompt was dropped upstream or that Haiku generally cannot follow system instructions. The framing control remains unresolved.

Those records live in `workspace/participants-20260915-1740/`, `workspace/cloud-instruction-check-20260915-1745/` and `workspace/cloud-system-formats-20260915-1750/`. They retain their own budgets and protocols. The planned but undispatched paid roots are not listed as observed conversations.

## Implementation and limits

`behaviorlab/assessment.py` and `scripts/run_model_assessment.py` implement the finite CLI runner. Versioned plans, source-file hashes and frozen source copies precede dispatch. Saved raw responses can be replayed without new inference; an uncertain request is never retried automatically. Re-running a closed batch produces no calls. Fresh evidence requires a new directory and freeze.

The Explorer's `/api/assessments` endpoint only reads local evidence. It exposes no generation or cloud-credential controls. Assessment projections preserve exact source hashes and validate quoted observation spans. Unstarted slots remain accessible in profiles and the direct reader, but do not inflate the transcript library's default count. Personal notes remain separate from journals and from formal ratings.

The first implementation does not offer an arbitrary model selector, launches from the browser, independent human scoring, or an attractor ranking. Four-message samples cannot establish behavioral prevalence, a causal mechanism, or the absence of an attractor. A subsequent research comparison needs longer repeated trajectories, explicit framing contrasts and the laboratory's existing qualification gates.

Catalog and routing semantics were checked against the live OpenRouter API and its [provider routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection), [usage accounting documentation](https://openrouter.ai/docs/cookbook/administration/usage-accounting) and [limits documentation](https://openrouter.ai/docs/api-reference/limits). Catalog descriptions are provider claims, not independent capability evaluations.
