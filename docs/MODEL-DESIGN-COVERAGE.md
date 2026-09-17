# Model & Design Coverage

The coverage screen reads the existing catalog and the versioned balanced-replication draft. It never imports a generation client, dispatches inference or changes a transcript, notebook entry or JEV score. Open **Model & Design Coverage** in the sidebar, or `#view=coverage`.

## Using the view

Choose a scope and task filter. Switch rows between exact model configurations and developer families. Columns can show partner disclosure, human-presence wording, actual composition, participant count, external intervention, history, exit instruction, requested temperature, weight access, recorded model type, condition or recorded protocol/source block. Sort rows by record count, actual speaker-reply exposure or name.

Every cell, including zero, is clickable. It selects a paginated list of exactly those records, with model badges, condition, visible and unavailable positions, token-cap and branch indicators, recorded controls and source fingerprints. Open a transcript and use **Back to Model & Design Coverage** to retain the cell and page. Browser URLs retain the selected scope, task, axes and cell. Exports contain the filtered inventory, complete selected IDs, counting rules, source-derived inventory fingerprint and proposed design; they contain no transcript or hidden-reasoning text.

The purple **Balanced replication draft** section is prospective. Its 20-per-cell values are proposed new root counts and never represent observed data, credits from historical runs or an inference queue. Candidate identities, exact prompt differences, qualification needs, precision limitations and later experimental blocks are visible within the app. The full design is available through its report button.

## Counting rules

- **Conversation inventory:** nonsynthetic, started records with at least two regular participants, excluding explicit cloud assessment/integration checks. It retains short, unavailable and engineering runs.
- **Visible atlas-eligible records:** the existing atlas eligibility rule plus a nonempty returned participant string. At this milestone it matches the completed corpus's 437 conversation-record cohort exactly. Future eligible records may not yet be assessed by JEV; this is a reading-eligibility scope, not an assessment-completion filter. It does not imply semantic validity.
- **Technical checks:** started assessment/integration records and single-participant engineering records. These are separate from behavioural sampling.
- **Unstarted assessment slots:** planned slots from earlier assessment screens. A slot without inference is not a behavioural observation.
- Synthetic fixtures are counted as excluded and never enter these four scopes.

Each conversation/root/slot record counts once. Repeated representations of the same message ID within a record count once; shared nodes in a branch do not multiply with leaf paths. Multiple segments do not necessarily mean branching. A record with two terminal paths or a fork in its recorded message-parent graph is marked as branching. Cross-record independence is not established: matching IDs, source hashes or seeds cannot certify fresh draws. A campaign source hash is shared by several distinct roots and must not collapse them into one observation.

Model/family row memberships overlap for mixed conversations; do not sum those record totals. Message exposure is attributed to the model that actually generated each regular reply. Third-party interventions can carry X/Y labels; their event kind excludes them from regular participant and speaker-reply totals.

Visible means a nonempty returned string, matching the frozen corpus. A whitespace-only reply is retained and separately indicated, not silently removed. Empty or unavailable positions and technical flags remain visible. Neither `complete` nor an absence of recorded flags certifies successful historical execution.

Requested sampler metadata is resolved from recorded shared settings, nested `decoding`, and per-speaker overrides, in that order. Missing values stay unknown; different speaker values display as mixed. A source header can preserve a value missing from the earlier Analysis projection, so this view may show fewer unknown temperatures without changing that frozen matrix. Requested settings do not establish effective controls across providers.

Source blocks use an explicit recorded protocol hash when present. Historical collection blocks are labelled historical and can contain different conditions or prompt recipes. Missing hashes create distinct unrecorded-protocol blocks rather than an invented common protocol. Historical `planned_count` can describe returned positions, so it is not used as the number originally allocated. Original allocations need their source plans; observed zero cells are not automatically failed or unstarted allocations.

## Implementation and verification

`behaviorlab/design_coverage.py` builds the metadata projection. Read-only routes are `/api/design-coverage` and `/api/design-coverage/export`, with a JSON `filters` query parameter. The UI is in `behaviorlab/explorer_ui/coverage.js` and `.css`. The current proposed allocation is `designs/balanced-replication-v0.2.json`, independently versioned and explicitly non-executable. Version 0.1 is preserved. Candidate audit and precision reports open from the draft panel.

Tests exercise root/branch counting, duplicate nodes, guest-event exclusion, actual speaker exposure, unavailable runs, whitespace-only output, nested and per-speaker controls, scope separation, zero cells, pagination, invalid requests, local host restrictions, read-only projection, draft arithmetic and UI state retention. Browser checks and the real-inventory summary are recorded separately in `docs/evidence/model-design-coverage-validation.json`.
