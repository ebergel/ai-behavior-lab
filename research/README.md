# Research snapshot

Original transcripts are core research entities.

- `transcripts/`: readable conversations, prompts, settings, all recorded visible/thinking text and message IDs.
- `evidence/`: unchanged original journals, raw requests/responses, imported source bytes and research sidecars.
- `catalog.json`: maps conversation IDs to readable files and authoritative sources.
- `notebook/readable.json`: notes, collections, findings, topic definitions/reviews, musings and all histories.
- Other `notebook/*.json`: exact table schemas and row values for restoration, including deleted entries.

Readable transcripts omit duplicated raw request/response/record fields; these remain in original evidence. Synthetic and unstarted records retain their labels. Historical host paths and local WebUI links are provenance, not portable execution credentials or a promise that a closed experiment can be rerun.

Restore offline into a NEW directory: `python3 -m behaviorlab.research_bundle restore --bundle research --destination workspace`. Then run `python3 -m behaviorlab explore --workspace workspace`. No model calls are made. Restore refuses to overwrite an existing workspace. See `docs/RESEARCH-DATA.md` for scope and updates.
