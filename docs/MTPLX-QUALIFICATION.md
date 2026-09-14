# MTPLX engineering qualification

14 September 2026. This extends the [initial identification](MTPLX-INTEGRATION.md) with actual local generation and captured engine inputs. It is part of the standalone laboratory, not a new behavioral result from the earlier experiment.

## Instrument changes

The laboratory now has explicit `mtplx` and `webui-mtplx` adapters. They accept the model's native top-k, thinking, effort, generation mode, depth, and cache controls. Protocols still use the bounded `engineering_local` execution class. The original Ollama adapters and version-1 synthetic campaigns remain supported.

The model identity is a manifest of every local JSON, Jinja template, and safetensors file, with a SHA-256 hash for each complete file. The manifest fingerprint is `786256ef4f4c3a3f6a485692404b751168607715f292fd6f7f8c4666b97e8ea6`; it covers 30,370,836,756 bytes of model/configuration/tokenizer material. This is a content-addressed manifest identifier, not the hash of a single concatenated weights file. Selected installed runtime sources and package metadata are separately pinned. This is stronger provenance than a model name, but not a reproducible build of the whole operating system or dependency environment.

Before inference, the adapter checks file inventory, sizes, content hashes, and effective server settings. Full content hashes are cached only while device/inode/size/modification/change signatures remain identical; changes during hashing are rejected. A separate helper uses the installed MTPLX Python environment to render the local tokenizer template, without loading model weights or downloading anything. The instrument reserves the requested output allowance before sending a generation. Input plus reserve must fit the explicit 32,768-token runtime window.

MTPLX's built-in request capture records the token IDs supplied to generation and the effective sampler. Each response is checked against the independently rendered token sequence, mode, depth, seed, cache policy, thinking mode, and trace-retention policy. A hidden retry, changed resolved seed, usage discrepancy, or input mismatch invalidates the turn. HTTP response bytes survive even if capture collection fails. The first two smoke responses retained parsed captures and original capture-file hashes; subsequent responses also embed the original capture bytes. All original capture files remain archived locally.

Reasoning is retained as evidence and excluded from both participants' next inputs. A reasoning-off response with a nonempty trace is invalid. Output-cap stops are invalid rather than accepted as completed turns. The context check applies to each recipient's exact rendered request; the declared 262,144-token model limit does not establish a usable window on this machine.

## Observed results

| Check | Result |
|---|---|
| Direct mode smoke | 2 calls committed; reasoning on/off represented correctly. |
| Uncached history branches | 28 calls committed: both modes, FF/FR/RF/RR, endpoints at turn 6. Paused after 3 calls and resumed for 25 without replacing the saved prefix. |
| Cached ON branches | 14 calls committed; 5 actual cache hits. Captured input tokens matched the intended histories throughout. |
| WebUI with cache enabled | 2 calls committed; both reasoning modes preserved; 1 actual cache hit. |
| WebUI cache-bypass check | 1 deliberate negative-control call rejected: requested bypass was not effective. Raw evidence retained. |
| Automated and standalone verification | 49 tests pass in the workspace and in a copy with no evidence workspace or reference checkout. All five completed campaigns replay offline without changing journal bytes. |
| WebUI transcript | One six-turn ON/RF branch imported; the saved WebUI history exactly matched the export. |

There were **47 generation calls: 46 technically accepted and one expected rejection**. All 47 engine token sequences matched independent rendering. No output-cap stops, hidden retries, unresolved attempts, or visible telemetry footers were observed. The maximum input was **313 tokens** and maximum generated output **447 tokens**. This remains a short-context check, despite the configured 32,768-token window.

The calls took **213.69 seconds** of combined generation HTTP time. Median server-reported decode speed was **37.99 tokens/second**, mixing short outputs and reasoning modes. Highest reported peak MLX memory was approximately **34.26 GiB**; this is engine telemetry, not total machine memory. None of these measurements is a sustained speed or long-context benchmark.

### Cache behavior is an experimental control

Comparing the cached and bypassed ON branch runs yields nine requests with identical messages, seed, and controls other than cache policy. Seven produced identical visible text and traces. Two, `ON-history:R:4` and `ON-history:FF:5`, produced different visible text and traces at actual cache hits of 128 and 193 tokens, respectively. Their captured input sequences remained correct. Five later comparisons already had different conversation histories because an earlier reply had diverged.

This rules out silently restored omitted text in the observed rendered inputs; it does not establish numerical equivalence of the cached computation. The check does not identify the mechanism behind the output differences or demonstrate a changed output distribution. The baseline should therefore use **direct MTPLX with `metadata.cache_mode=off`**. Cache-enabled execution remains a separate condition pending a dedicated repeatability comparison.

### WebUI routing constraint

WebUI 0.11.3 removes `metadata` before forwarding an OpenAI-compatible request. The negative control requested `cache_mode=off`, but MTPLX observed its session bank enabled; the laboratory rejected the response with `MTPLX changed requested cache policy`. Reasoning, seed, sampling, and rendered content passed their checks. With `cache_mode=auto`, both gateway smoke calls passed and kept reasoning separate from visible text.

The gateway adapter resolves the selected connection URL before generation and requires it to match the verified loopback MTPLX service. Configuration is inspected only for routing; credentials and full configuration responses are not retained in evidence. No connection settings were changed and no paid completions were made. The gateway has a qualified short route with caching enabled; it is not interchangeable with the cache-bypassed baseline. WebUI remains useful for reading laboratory transcripts and separate exploration.

## Evidence

The tracked [validation record](evidence/mtplx-qualification-validation.json) contains per-call observations, protocol/registry and journal hashes, the cache comparison, source fingerprints, checks, and cleanup status. Full evidence is retained under ignored `workspace/mtplx-qualification-20260914/`: five campaign journals, all 47 engine captures, before/after server snapshots, artifact manifest, test logs, and transcript export/receipt. Engine dispatch capture is evidence of rendered tokens and effective controls; it is not a byte-for-byte network capture of WebUI's outbound HTTP body.

The [six-turn restoration transcript](http://127.0.0.1:8080/c/4bde71b8-c40e-4282-810f-8d363d7ef649) is a local installation link. It was verified by API round trip, not by a new visual browser inspection. Generated traces remain in the laboratory evidence and are excluded from this initial transcript view.

The temporary qualification server was stopped after verifying its unique launch identity. Port 8000 was idle before and after the check. WebUI's catalog was refreshed after shutdown. The user's saved launch configuration and previous session records were preserved.

## Configuration

The user's temperature 1.0, top-p 0.95, top-k 20, sustained profile, depth 3, and reasoning-on/medium reference are preserved. Separate protocol labels select reasoning on and off on the same weights. Engineering calls reserve 1,024 total generated tokens, including reasoning, and set both presence and frequency penalties to zero.

The qualification server uses the actual cached model path, a 32,768-token context, serial scheduling, no warmup generation, no SSD session cache, explicit reasoning-history stripping, the local tokenizer template, and no telemetry footer. Direct requests choose whether to bypass the in-memory session bank. Disabling the SSD tier alone would not disable that bank.

The installed source also clarifies the footer behavior: although the CLI flag defaults to enabled, this build normally limits footer injection to MTPLX-owned UI clients, unless an environment override broadens its scope. The laboratory explicitly disables the flag and checks observed content for its marker.

The following command records the qualification launch. The tracked registries contain installation-specific paths and this launch identity; reusing them on another installation requires a newly captured registry and matching protocol hashes. Start only when the port is free and sufficient memory is available.

```sh
MTPLX_REQUEST_CAPTURE_DIR="$PWD/workspace/mtplx-qualification-20260914/captures" \
MTPLX_REQUEST_CAPTURE_KEEP=1000 \
/opt/homebrew/bin/mtplx serve \
  --model /Users/eduardobergel/.mtplx/models/grant-ai--Qwen3.8-27B-Abliterated-MTPLX \
  --model-id grant-ai/Qwen3.8-27B-Abliterated-MTPLX \
  --host 127.0.0.1 --port 8000 --profile sustained --depth 3 \
  --temperature 1.0 --top-p 0.95 --top-k 20 \
  --reasoning on --reasoning-effort medium --preserve-thinking off \
  --paged-kv-quantization off --chat-template-profile tokenizer --tool-prompt-mode native \
  --context-window 32768 --max-tokens 1024 --ssd-session-cache off \
  --no-stats-footer --warmup-tokens 0 --scheduler-mode serial --fan-mode default \
  --app-launch-id behaviorlab-mtplx-qualification-20260914
```

From another terminal in the laboratory directory, use a new campaign directory for a new run:

```sh
python3 -m behaviorlab run-local workspace/my-mtplx-smoke \
  --protocol examples/mtplx-mode-smoke.engineering.json \
  --registry design/mtplx-engineering-models.json --max-calls 2
python3 -m behaviorlab run-local workspace/my-mtplx-history \
  --protocol examples/mtplx-history.engineering.json \
  --registry design/mtplx-engineering-models.json --max-calls 28
python3 -m behaviorlab run-local workspace/my-mtplx-cached-history \
  --protocol examples/mtplx-cached-history.engineering.json \
  --registry design/mtplx-engineering-models.json --max-calls 14
python3 -m behaviorlab run-local workspace/my-mtplx-webui \
  --protocol examples/mtplx-webui.engineering.json \
  --registry design/mtplx-webui-engineering-models.json --max-calls 2 \
  --webui-token-file workspace/private/webui-token
```

Each protocol and registry is frozen into its campaign. Completed campaigns can be replayed offline, with no new inference or changes to journal bytes. The offline audit command is:

```sh
python3 -m scripts.summarize_mtplx_qualification workspace/mtplx-qualification-20260914
```

## Interpretation and remaining work

These prompts ask for arithmetic or a brief discussion of scientific-notebook checks. They test the apparatus. They do not test spontaneous experience-focused discourse, consciousness, or nonduality. “Committed” means that a response passed the technical contract, not that its answer was factually correct. In the two direct arithmetic smoke calls, reasoning on answered four pens correctly and reasoning off answered five incorrectly. One differently seeded example per mode supports no accuracy comparison.

Reasoning on/off is a useful same-artifact contrast for a subsequent scientific design. The present engineering roots have different derived seeds between modes. The cached ON history uses the same root seed coordinates as the uncached ON history, but cache equivalence would require a larger controlled comparison; exact rendered input matches alone do not prove identical internal computation or output distributions. AR-versus-MTP equivalence has not been measured.

The next stage remains a 50-turn technical qualification with realistic output lengths, recipient-specific context handling for the original Ollama candidates, and deliberate failure/recovery cases. After those pass, complete the experience/nonseparation codebook, probes, phenotype qualification, and preregistered factorial design. The MTPLX model is a distinct abliterated checkpoint and must not silently replace a participant in the original two-model factorial. Paid cloud execution remains blocked pending budget and provider-routing controls.
