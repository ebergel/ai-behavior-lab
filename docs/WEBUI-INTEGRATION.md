# Open WebUI and cloud model integration

**14 September 2026 — initial assessment and design.** The integration bridge was subsequently implemented and tested in this session; see [Milestone 2 bridge validation](MILESTONE-2-BRIDGE.md) for the current state. The inspection below is retained as the pre-integration record, including which checks had not yet occurred at that point.

The user already has Open WebUI with local and cloud connections. Reuse that installation for model exploration and transcript reading. Keep the laboratory responsible for protocol execution, history interventions, sampling specifications, and authoritative evidence. Add experiment-specific visualization only where the existing interface does not express the factorial matrix or shared branch ancestry.

## What was verified locally

Open WebUI **0.11.3** is running at port 8080. Its version endpoint and public OpenAPI schema were read. The schema exposes model discovery, chat completion, chat import, and connection-management routes. Its authenticated model catalog returned HTTP 401 to an unauthenticated request; no authenticated catalog or completion request was attempted.

Read-only queries of selected configuration fields showed:

| Connection or feature | Saved state / observed status |
|---|---|
| OpenRouter | Enabled connection to `https://openrouter.ai/api/v1`; no configured model-ID restriction. Actual accessible models and account availability remain unverified. |
| Other local inference | Enabled OpenAI-compatible connection to `http://localhost:8000/v1`; its model-list request received connection refused. The server implementation and models are not yet identified. |
| Ollama | Enabled connection to `http://localhost:11434`. |
| Open WebUI API keys | Disabled in persisted configuration; integration authentication remains to be configured. |
| Saved model presets | None in the model table at inspection. |
| Functions | One active video-generation pipe; no active text filter functions found. |
| Memory context feature | Enabled in persisted configuration. Installed middleware adds this context when the request also enables the memory feature. |

Only non-secret configuration fields and function metadata were selected. API keys, credential values, chat contents, user preferences, and function valve values were not read. No settings were changed, server started, or model completion generated. These observations are a dated configuration inspection, not an end-to-end integration test. Pinokio was checked as a discovery option; its control plane was not reachable, and this running installation was identified directly.

## Recommended division of responsibilities

| Component | Role |
|---|---|
| Laboratory core | Freeze conditions, schedule roots, construct each participant's exact history, fork and restore branches, journal evidence, score outcomes, and account for failures. |
| Backend adapters | Translate a declared protocol into each provider's supported interface and retain the raw request/response, model identity, finish reason, usage, and available trace fields. |
| Open WebUI | Existing interface for exploratory conversations, model browsing, and a readable view of exported laboratory transcripts. Its provider gateway can also be used after validation. |
| Small laboratory-specific view, if needed | Factorial-cell status, within-root contrasts, ancestry, annotation and validity flags. This is additional research functionality, not a second general chat interface. |

Open WebUI documents an OpenAI-compatible `/api/chat/completions` endpoint covering its connected Ollama, OpenAI-compatible, and Function models. Its API applies inlet filters, so using the API alone does not establish an unmodified route. [API reference](https://docs.openwebui.com/reference/api-endpoints/).

The installed code independently confirms the relevant behavior: the OpenAI router applies saved model parameters and system prompts; shared middleware invokes inlet filters and can add memory context. No such text filters or presets were found in the inspected tables, but request-level features and future configuration changes still need explicit control. These are part of the experimental configuration, not inherently undesirable features.

Start with the native Ollama adapter as a locally inspectable comparison and an OpenAI-compatible adapter for other servers. Add a validated Open WebUI gateway route to reuse its configured provider connections. Preserve a direct OpenRouter option when specific routing controls or response metadata cannot be reliably passed through WebUI. The laboratory should not depend on WebUI being present on every future installation.

## Reproducibility checks before using the gateway

1. Configure a dedicated laboratory authentication mechanism through the supported WebUI interface. Keep credentials outside versioned protocols and journal payloads. Current API-key support is disabled; an unauthenticated model-list request is not sufficient to discover the available models.
2. Select base models and explicitly disable memory, retrieval, tools, web search, and automatic follow-up/title-generation tasks for the scientific baseline. Record any active global functions and relevant defaults. Preserve the user's ordinary chat configuration.
3. Verify the outbound message roles, content, sampling parameters, stopping behavior, and reasoning fields using a controlled receiver or equivalent inspectable route. Comparing generated answers alone cannot show that two requests were equivalent. Record both the submitted WebUI request and the effective provider request where observable; otherwise mark the latter unknown.
4. Check short and long requests, empty content, malformed responses, truncation, errors, and interruptions. Confirm that model or provider fallback does not silently turn one planned condition into another.
5. Mirror a completed laboratory transcript into WebUI and verify that X/Y labels and model identities remain clear. Display formatting must not enter model inputs. The laboratory journal remains authoritative; manually edited or regenerated WebUI continuations are separate exploratory material unless explicitly imported as a new intervention.

Open WebUI provides a documented example of backend-controlled conversations appearing in its interface, using message-tree identifiers. The example is explicitly a community tutorial tested on an older release, so the installed 0.11.3 behavior must be checked rather than copied unquestioningly. [Backend-controlled flow](https://docs.openwebui.com/reference/api-flow/).

## Cloud experiments

Cloud access expands the study to hosted models and local–cloud pairings under the same branching design. This is useful for comparing trajectories and directional influence across participants. It does not give the laboratory access to cloud weights, hidden provider prompts, or internal activations.

The registry must distinguish a local artifact digest from a remote service identity. For a remote participant, record the requested model ID/version, actual reported model and provider, endpoint, request time, supported parameter set, and any returned fingerprint. Unavailable weight digests remain unknown; do not manufacture an equivalent by hashing the model name.

OpenRouter can distribute requests among providers by default. For a controlled condition, select the intended provider/endpoint, disable unintended fallbacks, and require support for the parameters included in the request. Its `provider.only`, `allow_fallbacks`, and `require_parameters` controls support these restrictions. They do not guarantee an immutable deployment or deterministic sampling. [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection).

Do not send the native Ollama options dictionary unchanged to every service. Each adapter needs a capability map for sampling, output limits, reasoning controls, and stopping. Unsupported controls must be rejected or explicitly excluded in a separately specified protocol. Retain raw usage/cost information and enforce a campaign budget before launching a cloud batch. The existing 1,800-call local plan should not automatically become a paid cloud campaign.

## Revised Milestone 2 order

1. Add backend-neutral identities and capability declarations while retaining native evidence.
2. Establish authenticated WebUI model discovery and identify the configured local port-8000 server.
3. Implement and test local Ollama, OpenAI-compatible, and WebUI gateway routes; validate passthrough behavior.
4. Add a one-transcript WebUI export/view check before building any general-purpose viewer.
5. Run local engineering qualification, then a separately budgeted cloud smoke test after model selection.
6. Add a compact factorial/branch dashboard only for functionality that WebUI does not supply.

The Milestone 1 implementation remains useful unchanged. This proposal broadens the adapter layer and reuses the installed interface; it does not change the scientific interpretation of the existing synthetic tests.
