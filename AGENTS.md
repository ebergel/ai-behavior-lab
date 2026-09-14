# Project boundary

This is a standalone laboratory repository. The user explicitly clarified that it is a new GitHub project, not an extension or fork of `ebergel/llm-self-play-attractors`. Treat that earlier repository as a reference and optional data source. Do not require its directory structure at runtime or change its files as part of laboratory development.

# Evidence and verification

Keep generated campaigns and imported datasets under the ignored `workspace/` directory or another explicitly selected evidence directory. Label synthetic engineering output separately from actual inference and scientific results. Preserve exact source bytes and missing historical metadata.

Run `python3 -m unittest discover -s tests -v` from this repository. The core and tests require no third-party packages. The optional MTPLX tokenizer helper uses the separately installed MTPLX Python environment. The research proposal and executable synthetic protocol have different schemas; do not convert an unqualified design into an actual behavioral campaign implicitly.

Runtime protocol v2 permits bounded local engineering via `run-local`; it is not a qualified research protocol. Keep cloud execution blocked until explicit budgeting and routing verification are implemented. Use the existing WebUI for transcript display. Credentials belong in runtime environment variables or owner-only ignored files, never in protocol documents or journal payloads. Gateway conversion tests and actual outbound network captures are different evidence; report their scopes accurately.

MTPLX's initial controlled baseline uses direct calls with session-cache bypass. Cache-enabled runs preserved rendered input but changed seeded replies at two matched requests; do not assume cache equivalence. The tested WebUI version strips metadata and cannot preserve this bypass request. Consult `docs/MTPLX-QUALIFICATION.md` before extending those profiles. Short engineering qualification does not qualify the full configured context window or a behavioral campaign.

HTTP parser `http-chat/2` checks MTPLX's final effective generator limits as well as dispatch capture. The latter can contain a requested budget that is subsequently clamped. Preserve parser-1 journals and use explicit reassessment sidecars; do not rewrite outcomes or issue new inference from a legacy-parser campaign. Client HTTP deadlines are recorded outside model inputs.

# Session records

Use a new `SESSION-RECORD-YYYY-MM-DD-HHMM.md` in this repository for each session record. Use local time in `America/Argentina/Cordoba`, include the full timestamp and scope inside, and preserve earlier records. Distinguish completed and verified work from proposals and future experiments.
