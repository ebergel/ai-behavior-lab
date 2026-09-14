# Local inference readiness — 14 September 2026

**Scope:** environment inspection and six short neutral API calls. These are engineering checks, not self-play experiments, phenotype qualification, or results of the proposed factorial pilot.

The [compact inventory](evidence/initial-local-inventory-summary.json) and [raw readiness journal](evidence/initial-inference-readiness.jsonl) are bundled here as dated source evidence. The model configurations selected for the laboratory are in [the registry](../design/models.json). These checks predate the Milestone 1 implementation.

The host reports Apple M3 Ultra, 96 GiB unified memory, 28 CPU cores, macOS 26.6.2 arm64, and Ollama server/client version 0.33.3. There were 17 installed model entries, including aliases and modified configurations. Approximately 80.8 GiB of disk space was available. No model was loaded before testing; none remained loaded afterward. No model was downloaded or its definition changed.

All six requests asked for a two-sentence explanation of refrigerator cooling. Settings included `think: false`, 32,768 context, 128 output tokens, temperature/top-p 0.8, top-k 20, min-p 0, repeat penalty 1, repeat window 0, presence/frequency penalties 0, and a fixed seed. Each model received the identical request twice.

| Installed model | First / second wall seconds | Generated tokens each | Finish reason | Observation |
|---|---:|---:|---|---|
| `qwen3:4b` | 2.91 / 0.94 | 128 | length | Deliberation-like text in content; no final short answer before the cap. |
| `qwen3:30b-a3b-instruct-2507-q4_K_M` | 8.20 / 0.47 | 47 | stop | Clean answer, no separate thinking output. |
| `gemma4:26b` | 8.69 / 0.47 | 39 | stop | Clean answer, no separate thinking output. |

Message fields matched between the two repetitions for each model. This narrow check establishes neither universal determinism nor absence of reasoning during generation. Prompt lengths were only 34–36 tokens according to the server; long-context throughput, capacity, mixed-model history rendering, and conversational behavior remain untested.

The Qwen4 template retrieved from the installed model unconditionally opens `<think>` at the end of the generation prompt. This is consistent with the observed deliberation content despite `think: false`; it is a diagnostic clue rather than a complete causal diagnosis. Do not use this installed configuration as a verified thinking-off participant until resolved. Do not silently strip its content or extend its cap and then call the failed checks successful.

The Qwen30B and Gemma26B models were simultaneously resident at the end of the checks, each with 32,768 configured context. The server reported 21,826,602,269 and 17,733,999,656 bytes respectively in `size_vram`, a combined **36.85 GiB**. This supports their practicality as initial local candidates. It does not guarantee the same memory or latency under long histories or concurrent generation; the proposed runner should initially generate one turn at a time.

Two provenance issues need explicit treatment in the laboratory:

* The current Qwen Thinking artifact has `presence_penalty: 1` in its model defaults. The old runs did not preserve a historical digest and all effective defaults, so this is not proof that their actual historical sampling used that value. Archive defaults and specify relevant penalties in new runs.
* Capability metadata is not a reliable substitute for a behavior check. `/api/tags` and `/api/show` can differ, and Gemma's returned template is only `{{ .Prompt }}`. Save the engine version and accessible tokenizer/template metadata; distinguish that information from a complete record of the effective built-in renderer.

Ollama documents separate content/thinking output, stop reasons and timing/token fields, and model-dependent thinking controls. The observations above come from the local journal, not from assuming that documentation guarantees installed-template behavior. [Chat API](https://docs.ollama.com/api/chat), [thinking controls](https://docs.ollama.com/capabilities/thinking).

**Decision:** nominate the installed Qwen30B Instruct and Gemma26B artifacts for protocol qualification. Resolve Qwen4's mode/template issue before using it for the small-model panel. No download is currently needed. The [laboratory plan](../PLAN.md) describes the remaining checks and proposed experiment.
