# Milestone 2: working local integration bridge

**14 September 2026. Scope: integration and engineering verification.**

The standalone laboratory can now make real local calls through three adapters and mirror a completed branch into the user's existing Open WebUI. The integration step is complete. The wider Milestone 2 qualification, including recipient-specific context bounds and long trajectories, remains open. No behavioral factorial campaign or paid cloud completion was launched.

## What was exercised

| Check | Observed result |
|---|---|
| Automated suite | 39 tests pass, including the original 27 core/import tests. |
| Native Ollama | Seven Qwen 30B Instruct calls in the mixed branching check. |
| WebUI gateway | Seven Gemma 26B calls through `/api/chat/completions`, using explicit native options. |
| OpenAI-compatible adapter | One additional Qwen call through Ollama's local `/v1/chat/completions`. This is the same inference engine behind another interface. |
| Local branching trial | All 14 nodes committed; FF, FR, RF, RR reached turn 6; zero invalid turns, blocked descendants, or unresolved attempts. |
| Pause/resume | Paused after three actual calls; resumed for the remaining eleven. Completed campaigns replayed without network access or any journal-byte change. |
| WebUI → local OpenAI receiver | Two synthetic requests captured at the receiver: short/empty/Unicode input and a 51-message history plus system prompt. Expected outbound JSON matched exactly, including roles, content, seed, limits, sampling, reasoning disable, stops, and provider restrictions. |
| WebUI Ollama conversion | The two installed conversion functions were isolated from the installed source and executed on short/long test inputs. Both matched the intended native request. This checks conversion code; it is not a network capture of the final WebUI → Ollama request. |
| Transcript mirror | One six-turn RF ancestry imported. The imported history matched the exported tree exactly. The browser displayed all six turns with X/Y labels and model identities. |

Fifteen local generation calls returned successfully. The maximum server-reported prompt count was **204 tokens**. Their combined generation-HTTP elapsed time was approximately **13.02 seconds**, excluding discovery, verification, user-interface work, and pauses. This small check is not a sustained-throughput or long-context benchmark.

The engineering stimulus explicitly asks for a short discussion of scientific-notebook checks. It deliberately supplies a task and constrains response length. These transcripts therefore provide no test of spontaneous experience-focused or nondual discourse under the proposed task-free condition.

## Authentication and connected models

WebUI 0.11.3 is running in its existing single-user mode. Its supported sign-in endpoint supplied a session token, which is kept in an owner-only file under ignored `workspace/private/`. No API-key setting was changed. The saved OpenRouter key was not read, copied, or printed.

The authenticated catalog contained **467 entries**: 17 Ollama entries, 447 entries associated with the OpenRouter connection, two function-pipe entries, and one other/arena entry. Catalog visibility does not establish paid generation availability, an account balance, or a fixed provider deployment. No paid model completions were sent.

The other saved local connection, `http://localhost:8000/v1`, was not serving models. Its original application remains unidentified. For the OpenAI receiver check, a temporary server used that idle, already configured port and advertised only a unique synthetic contract model. It rejected other model IDs, did not record authorization headers, changed no connection settings, stopped after the check, and its cached entry was removed by a catalog refresh. This does not validate the user's stopped non-Ollama inference engine.

Post-check inspection confirmed the saved Ollama/OpenAI connection URLs, disabled WebUI API-key setting, and ordinary memory-context setting matched the earlier inspection.

## Implementation and evidence guarantees

Runtime registry/protocol version 1 remains compatible with the synthetic campaigns. Version 2 distinguishes service identity, endpoint, declared capabilities, accepted reported model names, optional actual artifact digest, and artifact provenance. An unknown remote weight digest is `null`; it is not fabricated from a service name. `run-local` requires an explicit call limit and an `engineering_local` protocol. The previous `demo` command cannot accidentally run it.

The adapters reject unsupported controls. Native Ollama requests specify all the existing sampling/context options. For Ollama models reached through WebUI, `think` and `keep_alive` are placed in the gateway's nested `options` structure, alongside sampling, context, output budget, and seed. The installed converter moves the two native root controls back out before forwarding to Ollama. Treating WebUI's Ollama route as a generic OpenAI parameter surface would lose controls in this version.

For new local calls, the adapter verifies the actual Ollama digest, template hash, model-defaults hash, and server version. The gateway additionally checks its version and the authenticated model entry; local gateway campaigns currently require a matching Ollama artifact and reject exposed function/filter routes. This is not a general proof that all possible future gateway settings are neutral. Each request records that its effective provider request was not captured on that actual call.

The journal retains the exact canonical JSON request before dispatch, raw response text, original response bytes encoded in base64, response hash, HTTP status, selected non-secret response headers, timestamps, elapsed duration, and raw usage/finish/trace fields. Credentials are transport-only. HTTP error responses are retained and invalidate the branch; transport exceptions with uncertain outcomes require explicit retry authorization. Saved raw responses are reused on recovery. Parser failure, output caps, reported model mismatch, and unexpected trace output in an explicitly disabled mode remain visible.

WebUI requests turn memory, web search, code interpreter, and automatic title/tag/follow-up tasks off at request level, without changing the user's ordinary chat settings. The transcript importer records a pending receipt before submission; an uncertain import is not silently repeated. A known imported chat can retry its verification read without creating another copy.

## Evidence locations

The tracked [validation summary](evidence/milestone-2-bridge-validation.json) contains campaign/registry/protocol hashes, journal heads, per-call timing/usage, contract evidence hashes, and the WebUI import receipt. Full local artifacts remain in the ignored evidence workspace:

- `workspace/local-bridge-20260914/`: 14-node real mixed-adapter campaign and RF transcript export/receipt.
- `workspace/local-openai-20260914/`: one real local compatibility-route call.
- `workspace/webui-contract-20260914/report.json`: submitted and captured synthetic gateway payloads and responses.
- `workspace/webui-contract-20260914/ollama-converter.json`: source fingerprint and isolated converter comparisons.

The reusable receiver check is `python3 -m scripts.check_webui_contract --port 8000 --output workspace/a-new-check/report.json`. It requires an idle port already configured as a local OpenAI-compatible connection in WebUI; it fails if that port is occupied. It does not reconfigure WebUI automatically.

The viewed local transcript is [Behavior Lab · local engineering · AB-r01:RF:6](http://127.0.0.1:8080/c/9782f8f6-be8e-405c-aea4-4f4d20aa0909). This link is specific to the present installation. Its bubble roles are display layout; both participants are AI models. The authoritative conversation and actual generation timestamps remain in the journal, and displayed timestamps in this initial export reflect export time. Manual WebUI edits or continuations are separate exploratory material.

## Remaining before scientific use

1. Establish recipient-specific rendered-input counts or defensible bounds, then run the planned long and mixed-model technical trajectories. The short real prompts and long synthetic receiver input do not establish context validity.
2. Capture the final WebUI → Ollama payload through a controlled route if that gateway will be used in the research baseline, and freeze or recheck relevant gateway configuration. The current native adapter provides a simpler inspectable baseline.
3. Identify and start the user's non-Ollama server, then qualify its model identities, supported parameters, and trace behavior.
4. Add budget enforcement and provider verification before cloud execution. Direct OpenAI-compatible transport and remote identity structures exist, and provider-control forwarding passed a synthetic receiver check; paid cloud execution remains intentionally unsupported by the runtime protocol.
5. Complete phenotype qualification, probes, codebook/annotation, and protocol freezing before the 20-root factorial pilot. No experimental conclusion about experience or nonduality follows from this integration check.
