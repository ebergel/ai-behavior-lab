# Replication candidate audit

17 September 2026 · Codex · read-only metadata and offline rendering checks.

The six-family panel remains feasible as a candidate panel. **No candidate is newly qualified for generation by this audit.** The strongest new finding is an already installed, provenance-checkable OLMo chat artifact that can replace the raw alias in the next technical qualification. No model weights were downloaded, no model output was generated, and no paid request was made.

The [retained evidence](evidence/replication-candidates-20260917.json) contains the selected API metadata, manifest records, OLMo file-hash verification, publisher file listing and six exact offline render checks. It records retrieval sources and limitations. Candidate metadata is time-sensitive; recheck it immediately before the executable freeze.

## Local candidates

| Configuration | Verified in this audit | Remaining qualification |
|---|---|---|
| Qwen3 30B Instruct 2507 Q4 | Installed manifest still `19e422b023139…`; GGUF/Jinja template and defaults recorded | Reverify pinned runtime/files, native recipient rendering and input counts; test proposed common output/context controls |
| Gemma 4 26B Q4 | Installed manifest still `5571076f3d70…`; metadata and defaults recorded | Reverify native Gemma renderer and proposed controls; `/api/show`'s plain prompt placeholder is not the effective chat template |
| OLMo 3.1 32B Instruct Q4, native HF tag | Installed full file hash matches the quantization publisher's LFS SHA-256; supplied-system, no-tools offline rendering agrees with upstream in six fixtures | Qualify actual Ollama rendering/tokenization, stop handling, context fit, generation limits and visible output; do not treat old raw-alias runs as controls for this route |

Qwen and Gemma retain the same manifest identities as the earlier [native Ollama engineering qualification](OLLAMA-MIXED-QUALIFICATION.md). This audit did not rehash their full weight files or rerun that qualification. Metadata advertises capabilities and defaults; it does not establish effective settings for a future call.

The selected native OLMo tag is:

```text
hf.co/unsloth/Olmo-3.1-32B-Instruct-GGUF:Q4_K_M
```

Its manifest SHA-256 is `4e6927902f5249a23d1fddc297cdab29446d0507123f96fec153242660472aa1`. Its **19,482,036,256-byte file was actually hashed** as `4e671b2402c30c5fc1fea99d97af96332933a33db0d2c27c581537a815044795`, with unchanged file size and modification time during the read. That hash and size equal the publisher's `Olmo-3.1-32B-Instruct-Q4_K_M.gguf` at revision `8560671d3678feb9071a684b7110b2df87b49473`.

The quantization publisher identifies [Ai2's OLMo 3.1 32B Instruct](https://huggingface.co/allenai/Olmo-3.1-32B-Instruct) as its base model. The observed upstream revision is `ac0587e4a7744a551c059d8cd17ba220bc940dae`. This establishes byte identity to the [published quantization](https://huggingface.co/unsloth/Olmo-3.1-32B-Instruct-GGUF), not an independent verification of the quantizer's transformation from upstream tensors.

The historical `olmo31-instruct-raw` alias uses a different 19,482,033,312-byte artifact (`002a5687076790b1c86cd73323f4acc15ec1d0d671231767919e59d656e5a21b`) and a plain `{{ .Prompt }}` template. The size/hash difference does not itself prove different numerical weights; metadata can change a GGUF hash. No tensor-equivalence comparison was made. Preserve that historical route and its observations as a distinct configuration.

Six offline Jinja2 3.1.6 renders tested each proposed disclosure with either the opening cue alone or a short own/peer history, using a supplied system prompt, no tools and the upstream EOS token. The upstream tokenizer template and the template reported for the installed native artifact produced identical bytes in all six cases. Both avoid inserting OLMo's default identity preamble when the experiment supplies its own system message. These are template-level fixtures, **not captures of Ollama's generation inputs or token IDs**. They do not qualify the full 18-message window.

## Hosted candidates

The public OpenRouter catalogue and model endpoint metadata listed all three exact IDs. API access with this account, provider stability, reasoning control and effective parameter fidelity still need finite technical checks.

| Model ID | Listed route of interest | Listed context | Input / output USD per million tokens |
|---|---|---:|---:|
| `anthropic/claude-haiku-4.5` | `anthropic` | 200,000 | 1.00 / 5.00 |
| `openai/gpt-4o-mini-2024-07-18` | `openai` | 128,000 | 0.15 / 0.60 |
| `nvidia/nemotron-3.5-lightning:free` | `nvidia/nvfp4` | 1,000,000 | 0 / 0 |

These are the captured route prices, not a run quote or upper bound. Other Haiku routes are listed; some have higher prices. Cache discounts and non-token charges are separate fields in the retained metadata. Free-route availability and quotas can change.

Source endpoints: [Haiku](https://openrouter.ai/api/v1/models/anthropic/claude-haiku-4.5/endpoints), [mini](https://openrouter.ai/api/v1/models/openai/gpt-4o-mini-2024-07-18/endpoints), [Nemotron](https://openrouter.ai/api/v1/models/nvidia/nemotron-3.5-lightning:free/endpoints).

Temperature and output-token limits are listed for all three routes. Top-p is also listed. Mini and Nemotron list seed support, which does not establish determinism. Haiku and Nemotron list reasoning controls; mini does not list the same controls. Do not send an identical reasoning object indiscriminately or assume omission disables reasoning everywhere. Pin a route, disable fallback, require the intended supported controls, and inspect actual response/provider identity in the technical qualification. A dated mini ID is useful provenance, not a guarantee that all serving details are immutable. The NVIDIA route explicitly names NVFP4, which belongs in its configuration identity.

## Next executable milestone

The [version 0.2 design draft](../designs/balanced-replication-v0.2.json) records this candidate correction while preserving version 0.1. It remains non-executable. The proposed **24 technical calls** still mean four per candidate, not permission to retry until a candidate passes. First prepare exact role/history/long-window/output fixtures, local render/token preflights, pinned provider requests, output and input ceilings, seeds, ledger, stop rules and a new combined spending cap. Preserve a failed qualification and stop that candidate. Do not replace it on the basis of attractive dialogue content.

After technical qualification, settle precision and independent semantic validation before the balanced behavioural collection. The historical score variance is summarized in [precision planning](REPLICATION-PRECISION.md); it does not justify carrying the illustrative twenty roots forward automatically.
