# Session record — laboratory WebUI integration bridge

Timestamp: 2026-09-14T17:37:11-03:00 (America/Argentina/Cordoba).
Scope: the user authorized the next integration step after clarification that WebUI's API-key setting, rather than its OpenRouter connection, was disabled.

## Completed

The independent `laboratory/` repository now supports runtime protocol/registry v2 for bounded local engineering. Added native Ollama, OpenAI-compatible, and authenticated WebUI adapters to the existing durable journal/recovery system. Model service identities are distinct from optional actual weight digests. Unsupported controls, observed artifact drift, malformed responses, caps, and unexpected traces are explicit failures. HTTP responses retain raw text, original bytes, status, selected headers, timing, and provider usage fields. Credentials never enter the protocol or evidence payload.

Authenticated through the installed WebUI 0.11.3 supported single-user sign-in route. Kept the session token in the ignored owner-only workspace file. No API-key or connection settings changed. Catalog inspection found 467 entries: 17 Ollama, 447 associated with the OpenRouter connection, two function pipes, and one arena/other entry. No OpenRouter key was read or exposed, and no paid cloud generation occurred.

Verified actual WebUI forwarding to a temporary, uniquely named synthetic receiver on the idle existing port-8000 connection. Short/empty/Unicode and long histories preserved the expected outgoing OpenAI JSON, including sampling and provider restrictions. The receiver was stopped and its cached model removed. No connection configuration was changed. The original non-Ollama server at that address remains unidentified/stopped; a clarification was sent to the user.

Inspected and exercised the installed WebUI Ollama converter. Native controls must be carried in `options`; the adapter now does so. Both converter checks matched expected native payloads. This is source-function verification, not a final outbound WebUI-to-Ollama network capture.

Executed a 14-node short engineering branch graph with Qwen 30B through native Ollama and Gemma 26B through WebUI. Paused after three calls and resumed eleven. All FF/FR/RF/RR paths reached turn 6; no invalid, blocked, or unresolved nodes. Executed one additional local Qwen call through Ollama's OpenAI-compatible route. Total: 15 successful real local calls, deliberately task-directed engineering content, zero paid cloud calls. Maximum reported prompt count: 204 tokens. These are not behavioral or long-context results.

Exported the actual RF ancestry and imported it into WebUI. API round-trip verification preserved the message tree. Browser inspection confirmed all six turns and explicit X/Y/model labels. The verified tab is retained as a deliverable. WebUI display timestamps in this initial export reflect export time; actual generation timing remains in the journal. The display copy is exploratory if edited or continued.

## Verification and artifacts

39 automated tests passed in the working repository and in a clean source-only copy. Both v2 protocol documents validated in that independent copy. Completed live campaigns replayed with no network and no journal-byte change. The reference checkout remains clean and unchanged.

- Current report: `docs/MILESTONE-2-BRIDGE.md`.
- Machine-readable validation and source hashes: `docs/evidence/milestone-2-bridge-validation.json`.
- Real campaign evidence: `workspace/local-bridge-20260914/` and `workspace/local-openai-20260914/`.
- Synthetic gateway/converter evidence: `workspace/webui-contract-20260914/`.
- WebUI transcript: http://127.0.0.1:8080/c/9782f8f6-be8e-405c-aea4-4f4d20aa0909

All prior session records are preserved. Generated campaigns and private authentication material remain ignored by Git. The new laboratory still has no GitHub remote; this work does not modify or extend the earlier repository.

## Next phase

The integration bridge is complete, while broader Milestone 2 qualification remains open. Establish recipient-specific rendered-context bounds and run longer mixed-model trials. Obtain a final WebUI-to-Ollama outbound capture if selecting that gateway for the research baseline. Identify and qualify the stopped non-Ollama engine. Implement explicit cloud budgets and verify provider identity before cloud generation. Then finish phenotype qualification, probes, annotation, and a frozen factorial protocol. No semantic conclusions about experience, consciousness, or nonduality are warranted from this engineering stimulus.
