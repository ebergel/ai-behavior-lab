# Transcript explorer

**Purpose & musings** holds the lab's evolving research purpose, an editable map of experimental dimensions, and a journal for reflections, questions, hypotheses and directions. Entries support tags, filters, collection links, attribution, revision history and export. The researcher's original passages remain preserved alongside the Codex synthesis. See [the notebook guide](LAB-MUSINGS.md).

**Conversation Finder** adds clickable setup tags, model/lab/weight filters scoped to regular participants or external interventions, combined-condition counts and versioned saved views. Colored model badges and the reader roster retain identities across close reading and research collections. See [the Finder guide](CONVERSATION-FINDER.md) for definitions, examples and validation.

**Model assessment** is a new sidebar section for participant profiles, exact instruction checks, service availability and short self-play samples when available. It links to the same close reader, comparison, notes, tags and collections. Frozen protocols and Codex-attributed findings are kept beside their evidence. The first free-route screens encountered configuration, quota and access restrictions; missing replies are not negative behavioral labels. See [the assessment record](MODEL-ASSESSMENT.md). Inference still runs only through an explicitly frozen CLI batch, never from the Explorer.

The latest screen contains four-message conversations from Nemotron and Ling. Use **Choose assessment batch** to return to an earlier screen. Nemotron's system-check button is labeled **earlier batch** and opens its original source; the current call count excludes that reused observation. Word-limit overruns are visible on the candidate card. **Read & annotate** opens each conversation for close reading, comparison or saving a passage.

Recorded 15 September 2026. This local application makes close reading a first-class part of the laboratory. The user requested an overview of the experiments, a detailed transcript view and a way to connect passages to the conditions that produced them. The explorer is an additional layer alongside WebUI.

## Open it

Double-click `Open Explorer.command` in the repository. The launcher opens an existing explorer on port 8765 or starts one and waits for it to become ready. Keep its terminal window open while using the app; Control-C stops the server. To start manually, run from the repository:

```sh
python3 -m behaviorlab explore --workspace workspace --port 8765
```

Visit **http://127.0.0.1:8765**. Python 3.9+ is sufficient. No model server, API credential, Node build step or internet connection is needed to read saved conversations. An empty workspace opens an empty library; import reference data or create campaigns through the existing laboratory commands to populate it. Use a different `--port` if necessary.

## Research collections

**Research collections** brings a question, a short synthesis, linked findings, a reading set and personal observations into one entity. Each finding expands into exact passages, their models and conditions. **Read in context** opens the full transcript; returning takes you back to the finding you were reading. **Compare these passages** brings the evidence for one finding together.

The first saved collection, **Understanding, experience & nonseparation**, contains 24 conversations, 10 attributed findings and 30 source passages. Eight conversations received a full visible-transcript reading, four a selected-passage review and twelve remain explicitly queued. The first pass is purposive and cannot estimate prevalence. Codex interpretations and personal researcher notes are distinct. See [the first-reading record](FIRST-READING.md).

Create a collection from the Research collections page. Add transcripts from their reader, or select a collection when saving a passage or run observation. The app adds that run to the reading set when needed. **Your observations** keeps these notes beside the analysis. **Mark read by me** records your own reading action; it is not semantic validation. **Edit overview** changes the title, question and synthesis while preserving original authorship and recording the editor.

**Export collection** downloads one JSON bundle containing the collection, its linked personal notes, selected visible transcripts, saved reasoning fields, prompts, settings and source fingerprints. Full request/transport payloads stay in the original evidence store. Collection and note revision histories remain in SQLite. The export is a current snapshot; UI import, history restore and structured finding editing are not yet implemented. Analyst findings can be saved through the validated local collection API; they are not automatically generated.

## Explore from overview to passage

| View | What it offers |
|---|---|
| Library | Conversation cards, visible-text search, matching excerpts, collection/model/condition filters, recorded-signal and personal-tag filters, sorting and pagination. Campaign paths distinguish successive engineering versions with the same root name. |
| Run atlas | One row per root and one mark per participant node; height reflects word count, with distinct colors for recorded repetition, caps and unavailable messages. Click a mark to open that message. Shared laboratory prefixes appear once. |
| Close reader | Participant messages, actual history branches, within-run search, collapsible long replies and exact repeated groups. The prompt, opening, settings and source provenance appear alongside the text. |
| Comparison | Select two runs using their comparison buttons, then open them side by side. Each column has its own scroll and actual-branch selection, immediate settings and an expandable prompt. |
| Notebook | Save a whole message, select a shorter passage, or add a run-level observation. Add comma-separated tags, search notes and quotes, edit or remove observations, and export the notebook as JSON. |
| Results | Coverage and recorded mechanical outcomes for the filtered selection, plus the existing project reports. Each report retains its original sample and scientific status. |

A useful first route is to search **understanding**, select a model, switch to the atlas and open a matching reply. Read its preceding context, inspect the prompt and history condition, then save a passage with an observation or question. Compare it with a different condition or a counterexample. The `/` keyboard shortcut focuses the current search box. Filter URLs and run/message/branch links can be bookmarked locally.

Search is literal and case-insensitive, over visible message text and run/model/condition metadata. It does not search prompts or hidden reasoning, infer synonyms, or assign semantic topics. “Nonduality” and “non-duality” are different search strings. Recorded reasoning can be opened within the reader when the source contains it. An absent historical trace is not treated as a recorded empty trace.

## Experimental settings and source evidence

The inspector shows the source prompt and opening, available per-recipient sampler settings, requested output cap, context setting, thinking mode and seed policy. Mixed-model differences are displayed by participant. MTPLX's recorded runtime context is explicitly labeled as a runtime value. Requested output limits are not a claim that older engines honored them; the earlier effective-limit findings and saved parser versions remain available.

For laboratory replies, **Exact input** displays the saved request, including role mapping, retained history and seed; the saved raw response can be expanded. **All recorded settings** exposes the protocol settings and model fingerprints. Historical runs expose their original message records and header settings; missing historical requests or model identities remain unknown.

RF follows the actual preceding R branch. It does not silently substitute messages from F. Outside-observer interventions remain in historical transcripts. Capped and invalid replies, blocked descendants, pending nodes, unresolved requests and raw outputs awaiting commitment remain distinguishable. Repeated text is collapsed for reading convenience and remains accessible message by message.

Existing **Open in WebUI** links appear where a saved import receipt matches the source journal and export fingerprint. The explorer does not import new WebUI conversations or change WebUI settings. WebUI remains available for its existing model access and conversation display.

## Notebook and evidence storage

Source transcripts are read-only. Personal notes are stored separately in `workspace/explorer/notes.sqlite`, with owner-only file permissions. Passage quotes are checked against exact Unicode character offsets in the source, and each note records its source fingerprint. Edit conflicts are rejected; removal hides a note while retaining its revision history in SQLite. The JSON export contains the current visible notes. Revision browsing, restore and import are not yet implemented; back up the SQLite file to preserve the full notebook.

Notebook observations are labeled `personal_exploration_not_formal_annotation`. They do not enter existing annotation packets, become independent human ratings, or change the research codebook. This is a local single-researcher application. The server binds only to 127.0.0.1, requires same-origin authenticated writes, and does not dispatch inference. It provides no public hosting or multi-user account system.

The catalogue discovers imported manifests immediately under the selected workspace and campaign/probe journals one or two directories below it. Private directories, explorer storage and deeper software copies are excluded. Duplicate copies of the same campaign journal are counted once. Import checksums and journal chains are verified; saved requests and committed outcomes are reconstructed under their recorded parser. A malformed, unsupported or concurrently changing source appears in **Source index**. Use **Refresh evidence** after a writer has paused or new evidence is saved.

## Verified inventory and limits

The local inventory at delivery is **400 historical reference runs, 34 real laboratory roots and 60 synthetic roots**. Synthetic roots are excluded by default. The default 434-root selection contains 10,982 visible participant replies, including flagged partial outputs; 117 runs have a recorded cap and 35 have at least one mechanically detected exact repetition sequence. These are descriptive inventory counts, not estimates of experience-focused discourse or nonduality. Mixed-model coverage rows overlap. Missing observations do not become negatives.

The capacity snapshot diagnostic journal is listed as a source notice because it is a separate diagnostic format rather than a main conversation. Relevant findings remain accessible through the capacity report. The results view exposes six existing reports; it does not recompute formal scientific analyses for arbitrary filtered samples.

Version 1 prioritizes reading and source traceability. It has no embeddings, topic clustering, automatic semantic annotations, parameter-value filter builder, annotation adjudication UI or experiment-launch controls. These are possible later developments guided by actual use.

## Validation

The standard-library suite passes **112 tests**, including catalogue/source verification, true RF ancestry, mixed-recipient settings, exact Unicode quote validation, note persistence and conflict handling, source exclusion, and local HTTP write protections. Browser checks exercised the real catalogue and a separate synthetic UI workspace: search/filter combinations and reloadable URLs, reader navigation, prompt/settings inspection, report display, saved full and selected quotes, notebook persistence, comparisons, branch selection, safe rendering of literal HTML, and a 390-pixel layout without horizontal overflow.

The disposable browser fixture is generated with:

```sh
PYTHONPATH=. python3 scripts/prepare_explorer_fixture.py workspace/explorer/ui-fixture
python3 -m behaviorlab explore --workspace workspace/explorer/ui-fixture --port 0
```

Choose a fresh fixture destination when repeating preparation. Its historical-format transcript is explicitly synthetic. Its factorial outputs use deterministic fixture backends. Browser test observations are stored only in that fixture's notebook; the real researcher notebook was left empty. No model calls, cloud costs, WebUI writes or new scientific claims were introduced.

The initial portable [validation record](evidence/explorer-validation.json) and [collection validation](evidence/first-reading-validation.json) records counts, checks and preserved source fingerprints. Full test logs and screenshots are under ignored `workspace/explorer/validation/`.

## Framing comparisons

The [Nemotron framing screen](NEMOTRON-FRAMING.md) adds four complete twelve-message conversations and a fourth saved screen under **Model assessment**. Its overview shows the exact prompt difference, each root's trajectory, exploratory onset judgments, word-limit overruns and clickable message maps. Seven Codex findings link seventeen exact spans. **Open the research collection** keeps the four fully read roots and findings in one place for personal observations and export. The earlier collection is preserved.

The current default library has 458 entries, including the earlier cloud checks and assessment conversations; synthetic fixtures remain excluded. No Explorer control launches inference. The framing runner has a separate finite contract and journal. See [the framing validation](evidence/nemotron-framing-validation.json) for the 137-test result, browser checks and preserved evidence fingerprints.

### Added 16 September: OpenAI and Anthropic participants

The [mini/Haiku comparison](CHEAP-MODEL-FRAMING.md) adds a fifth saved screen and eight complete twelve-message roots. Model assessment now displays exact model identity, cost, prompt contrast, trajectories and message maps for both models. Its collection button opens **Three models: identity, experience & conversation**, ID `466a7fab2754e0b03f593a32`: eight new full readings plus the four earlier Nemotron readings, eight findings and 21 exact passages. The earlier two collections and personal notebook are preserved. Final default library count is **466**, with synthetic fixtures still excluded.

The overview separates Haiku's experience discussion and generated human identities from mini's practical and fictional paths. Consecutive identical messages are marked in the reader; Haiku Mirror 2's closing “Yes.” pair remains available in full. All source quotes and the 15 new onset spans are checked against immutable transcript bytes. See [the current validation](evidence/cheap-framing-validation.json). This extension supplies no inference controls or independent human ratings.

## Consciousness & self topic flags

The [topic tracking guide](TOPIC-TRACKING.md) describes the new sidebar view, library filter and exact-passage flags. Five categories cover consciousness, subjective experience, selfhood, the hard problem and nonduality. Each flag preserves referent, stance, topic entry, source, authorship and revisions separately from personal notes. Collection exports include their members’ current flags; saved original collections and evidence remain unchanged. No flag means unannotated, not a negative result.
