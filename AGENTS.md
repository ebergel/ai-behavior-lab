# Project boundary

This is a standalone laboratory repository. The user explicitly clarified that it is a new GitHub project, not an extension or fork of `ebergel/llm-self-play-attractors`. Treat that earlier repository as a reference and optional data source. Do not require its directory structure at runtime or change its files as part of laboratory development.

# Evidence and verification

Keep generated campaigns and imported datasets under the ignored `workspace/` directory or another explicitly selected evidence directory. Label synthetic engineering output separately from actual inference and scientific results. Preserve exact source bytes and missing historical metadata.

Run `python3 -m unittest discover -s tests -v` from this repository. No third-party runtime packages are currently required. The research proposal and executable synthetic protocol have different schemas; do not convert an unqualified design into an actual behavioral campaign implicitly.

# Session records

Use a new `SESSION-RECORD-YYYY-MM-DD-HHMM.md` in this repository for each session record. Use local time in `America/Argentina/Cordoba`, include the full timestamp and scope inside, and preserve earlier records. Distinguish completed and verified work from proposals and future experiments.
