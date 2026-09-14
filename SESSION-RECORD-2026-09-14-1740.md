# Session record — MTPLX engine identification

Timestamp: 2026-09-14T17:40:59-03:00 (America/Argentina/Cordoba).

The user identified the previously unknown WebUI port-8000 connection as MTPLX serving `grant-ai/Qwen3.8-27B-Abliterated-MTPLX`, and supplied its exact launch command. Recorded that command unchanged in `design/mtplx-qwen38.candidate.json` and wrote `docs/MTPLX-INTEGRATION.md` for its laboratory qualification.

Read-only checks confirmed MTPLX 2.8.3 and the local model cache (~30.4 GB). Inspection by absolute local cache path passed the runtime-contract and 15-tensor MTP gates: 8-bit affine body, BF16 MTP head, maximum supported depth 3, sustained profile. This is an artifact/header/contract check, not an executed sampling or fidelity test. Metadata files were hashed; full tensor bytes were not hashed. Port 8000 had no listener.

An initial inspect call using the Hugging Face identifier resolved a metadata-only HF snapshot, reported missing tensors, and exited 3. Inspecting the actual MTPLX model directory then passed. This was an inspection-path distinction, not evidence that the user's working launch command or installed weights were broken. No repair, override, download, server start, or model generation was performed.

Installed CLI help/source confirms a stats footer enabled by default and a `--no-stats-footer` option. Laboratory use should suppress it so performance labels cannot feed the partner. Reasoning-history preservation and warm/SSD prefix reuse need explicit checks under the laboratory's trace-withholding and history-restriction policies. The user's reasoning-on/medium settings should be retained as a reference condition; reasoning off can be a controlled contrast on the same artifact. MTPLX's generic OpenAI interface requires additional capability/provenance work in the laboratory; no executable MTPLX protocol was declared qualified.

Consulted the official MTPLX repository and model card. Their speed/exactness claims are attributed claims, not measurements on this Mac. The model card describes modified weights and a replaced chat template; this remains a separate checkpoint condition from the Ollama models already tested. Prior evidence/session records were preserved. Only documentation and a non-executable candidate specification changed, so the inference test suite was not rerun.
