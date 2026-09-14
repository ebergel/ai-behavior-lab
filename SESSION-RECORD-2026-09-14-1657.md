# Session record — Open WebUI and cloud integration assessment

Recorded: 2026-09-14T16:57:41-03:00
Timezone: America/Argentina/Cordoba (UTC−03:00)
Scope: Assess the user's existing WebUI as an interface and model gateway for the standalone laboratory.

The user explained that Open WebUI is already installed, with non-Ollama local connections and OpenRouter, and asked whether the laboratory could use it. The recommendation is to reuse it for model exploration and transcript reading, retain laboratory ownership of the experiment graph and raw evidence, and validate its API gateway before experimental use. A general chat viewer is no longer the first interface task; any custom view should address experiment-specific needs.

Verified the running Open WebUI version as 0.11.3 on port 8080. Read its public API schema and version/configuration endpoints. An unauthenticated model-list request returned HTTP 401. Through read-only, explicitly selected database fields, confirmed enabled connections to OpenRouter and a local OpenAI-compatible server at port 8000, plus Ollama at port 11434. The port-8000 endpoint refused a model-list connection; its implementation and available models remain unidentified. OpenRouter's actual authenticated model catalog and account availability remain unverified.

Persisted API-key support is disabled. No saved model presets or text filter functions were found. One active function is a video-generation pipe. The memory context setting is enabled; installed source confirms memory insertion also requires the request's memory feature flag. Inspected installed code showing that saved model parameters/system prompts and inlet filters can affect API requests. Read only non-secret configuration fields; no credentials, chat contents, user preferences, or function valves were read. Pinokio discovery did not find a reachable control plane; the running WebUI was identified directly.

Reviewed official Open WebUI API/filter documentation, its backend-controlled UI tutorial (which is explicitly community-maintained and tested on an older release), and OpenRouter's provider-routing documentation. For cloud experiments, the proposed adapter must record service/model/provider identity and unsupported controls, avoid silent provider/model fallback, preserve usage/cost data, and apply a campaign budget. Cloud service identifiers are not local weight digests.

Created [the integration assessment](docs/WEBUI-INTEGRATION.md) and linked it from the README and plan. This is a recommendation and implementation handoff, not a completed integration. No runtime code, application setting, model installation, API credential, or remote repository was changed. No model completion was requested; no paid cloud inference occurred.

Next implementation: backend-neutral model identity/capability records, supported WebUI authentication and model discovery, local adapters plus a validated WebUI gateway, a single-transcript display/export check, then independently specified local and cloud engineering trials. Preserve the existing user's chat settings and the standalone project boundary. The prior Milestone 1 code remains at commit 61906ba until subsequent implementation changes.

Documentation links were checked. Runtime tests were not repeated because this turn changed documentation only.
