# MTPLX / Qwen3.8 candidate

**Initial identification, 14 September 2026 — locally inspected at that stage.**

**Subsequent work:** actual generation, full model-file hashing, rendered-token checks, and cache/WebUI constraints are documented in the [MTPLX qualification](MTPLX-QUALIFICATION.md). The statements below describe the earlier identification step.

The previously unidentified Open WebUI connection at `http://localhost:8000/v1` serves MTPLX when the user starts it. The user reports that this model is fast and supplied the command below. That performance report is useful for selecting a candidate, but is not yet a laboratory benchmark.

```sh
/opt/homebrew/bin/mtplx serve \
  --model grant-ai/Qwen3.8-27B-Abliterated-MTPLX \
  --profile sustained --depth 3 \
  --temperature 1.0 --top-p 0.95 --top-k 20 \
  --reasoning on --reasoning-effort medium \
  --paged-kv-quantization off --port 8000
```

The [candidate specification](../design/mtplx-qwen38.candidate.json) preserves these arguments and the local inspection results. Its candidate schema cannot be executed as a laboratory runtime protocol.

## What is verified locally

MTPLX **2.8.3** is installed. Its own cache contains `grant-ai/Qwen3.8-27B-Abliterated-MTPLX`, reported as approximately **30.4 GB**. Inspection of that actual directory passes the runtime-contract and MTP tensor gates: an **8-bit affine** language body, **BF16 MTP head**, and maximum configured MTP depth **3**, with the sustained profile recommended. The recorded contract names an older MTPLX version, 2.7.1; the installed inspector accepts it. Its `exactness_baseline` object is empty, so that file does not supply a numerical equivalence benchmark.

The local generation configuration contains temperature 1.0, top-p 0.95, and top-k 20, matching the supplied launch settings. The tokenizer/model configuration declares a 262,144-token context limit; this declaration is not a demonstrated usable context on this 96 GB machine. Metadata/tokenizer/template files were fingerprinted. The full weight files were not hashed, so the candidate's complete weight digest remains unknown.

Use the actual local path for inspection:

```sh
/opt/homebrew/bin/mtplx inspect \
  /Users/eduardobergel/.mtplx/models/grant-ai--Qwen3.8-27B-Abliterated-MTPLX --json
```

An inspection using only the Hugging Face identifier resolved a metadata-only HF snapshot and reported missing tensors. The local MTPLX cache inspection passed. This does not establish a problem with the user's launch command or installed model.

Port 8000 was stopped at inspection. No server, warmup, generation, download, or repair was launched in this identification step.

## Why it is useful to the laboratory

MTPLX uses native multi-token prediction to draft ahead and verify blocks. Its maintainers describe rejection sampling with residual correction as preserving the target sampling distribution. That provides a plausible explanation for the user's speed observation, and a useful execution property to check on this particular build. It does not imply identical output strings under the same seed, since the two algorithms can consume randomness differently. [Official MTPLX documentation](https://github.com/youssofal/MTPLX).

The model card identifies an abliterated source checkpoint, quantized weights, and a replacement of the source's injected chat-template prompt with the stock template. This is a distinct model artifact, not simply the previously tested Qwen running faster. Comparing it directly with the earlier models changes weights, template/runtime, and potentially reasoning and sampling together. [Publisher's model card](https://huggingface.co/grant-ai/Qwen3.8-27B-Abliterated-MTPLX).

Retain the user's exact configuration as a reference condition. A useful controlled extension is reasoning on/medium versus off on these same weights, with other settings held fixed. A separate AR-versus-MTP comparison can examine execution consistency. Neither contrast should be folded into the original 2×2 participant matrix without explicitly revising the design.

## Required integration details

1. **Prevent telemetry from entering the conversation.** Installed `serve` CLI code sets `stats_footer=True` by default and documents `--no-stats-footer` to disable a visible TPS footer. Add this flag to a laboratory launch and verify the returned content. Otherwise the other participant could receive runtime-generated text as if its partner had said it.
2. **Specify reasoning history.** Installed help says `--preserve-thinking auto` preserves thinking by default for Qwen3.8. The laboratory's current policy withholds generated traces from both participant histories. `--preserve-thinking off` is the candidate setting for that policy, but the actual rendered request and cache behavior still need verification. Reasoning generation and reasoning-history retention are separate controls.
3. **Check cached prefixes against actual branch ancestry.** MTPLX documents warm-prefix sessions and an enabled SSD cache by default. Cache reuse may be an exact performance optimization; its existence alone is not evidence of conversational memory leakage. Test cold/warm runs and F/R/RF histories to ensure omitted turns or traces are not restored implicitly. Turning off the SSD tier alone does not prove that in-memory prefix reuse is absent.
4. **Declare supported parameters and provenance.** MTPLX supports `top_k`, whereas the present generic laboratory chat adapter rejects it. Add an explicit MTPLX capability profile, capture effective server settings and artifact identity, and check model naming, seed behavior, finish reasons, reasoning fields, and usage. The current native-artifact verifier only covers Ollama and must not be presented as MTPLX verification.
5. **Qualify actual context and output budgets.** Set explicit runtime limits after measuring the recipient's rendered tokens. Reasoning-on needs accounting for both reasoning and visible output. Inspect direct and WebUI-mediated requests and confirm that unsupported parameters or stateful defaults do not change a planned condition.

The immediate implementation target is a small MTPLX qualification protocol through the existing OpenAI-compatible adapter, followed by the WebUI route. The user's running configuration remains unchanged until that protocol is made concrete and executed.
