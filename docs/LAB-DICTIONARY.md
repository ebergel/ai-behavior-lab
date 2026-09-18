# Lab dictionary

The Dictionary is a first-class Explorer section at `#view=dictionary`. Its current scope is **39 terms**: all eight Gem Finder axes, six terms for interpreting numbers, 23 research entities and units, and two terms for researcher readings and navigation. It is the lab's shared vocabulary and measurement guide, distinct from the Topic atlas’s evolving topic vocabulary.

## Research entities & units

Open `#view=dictionary&category=entities&term=conversation` for the linked evidence hierarchy and assessment relationship. Separate entries cover conversations, runs, messages, turns, excerpts, branches, transcripts, external interventions, lineages, campaigns, studies, analysis targets, context, samples, datasets, subsets, units of analysis, assessments, features, scores, requests/attempts, synthetic controls and source artifacts.

The former `passage` entry has been removed. `#view=dictionary&term=passage` redirects to **Message**, and searching for passage still finds that definition. Existing lineage bookmarks with the former `evidence` category migrate to `entities`; other term IDs, Gem links and return state stay intact. Version `dictionary-2026-09-18-v5` uses message throughout explanatory measurement prose; exact assessment questions retain their explicitly labeled original wording. Definitions document the actual current methods and keep unknown counts, technical runs, synthetic evidence and statistical independence distinct.

The visual map links **Conversation → Message → Optional excerpt** and **Selected object → Assessment → Feature scores**. Each entry supplies a definition, practical meaning, counting/method rules, limitations and implementation references. [Research entities](RESEARCH-ENTITIES.md) records the terminology and its application to the reading and analysis screens. This dictionary addition does not rename scientific payloads, recalculate counts or implement the pending run/message eligibility audit.

Each measure includes a plain definition, practical interpretation, lower/higher-value descriptions, an explicitly illustrative example, technical specification, limitations, related terms and implementation provenance. The six JEV entries reproduce the exact assessment question, five rubric criteria and shared scope directly from `behaviorlab/gem_rubric.json`; the guide does not maintain a second copy of the scoring rubric. The computed topic-profile entry specifies its 24-dimensional RMS distance, nearest-per-lineage selection and mean across five neighbors.

## Use

- Open **Lab dictionary** from the main sidebar, or **Measure dictionary** in Gem Finder.
- Click a matrix measure name for its definition. Focused plots, individual assessment panels and the neighboring-profile panel also link to the relevant entry.
- Search definitions, synonyms, rubrics and methods; filter by section. Every selected term and search has a bookmarkable URL.
- Follow related terms without losing the return link. **Return to your Gem view** preserves filters, plot mode, axis ranges, selected message, bin and hidden-score setting.
- Export the complete guide as JSON. Task cards can link to the Dictionary view.

The six ratings use expected ordinal levels scaled to 0–100. They are not probabilities that a passage is extraordinary. Topic-profile distance uses distance units against a frozen reference; display filters do not recompute that reference. Word count is an observed eighth axis with a natural count scale; its entry explains length effects and the distinction from tokenizer tokens. Supporting entries distinguish these from topic probabilities, provider confidence, Pearson correlation, unknown values and personal judgments.

Illustrative examples are authored explanations, not newly scored passages or additional corpus evidence. The guide keeps factual accuracy, historical originality and personal value separate from what each rating actually measures. Independent human qualification of the provisional Gem rubric remains pending.

## Implementation and extension

`behaviorlab/lab_dictionary.json` holds editorial explanations and stable term IDs. `behaviorlab/lab_dictionary.py` enriches the six measure entries from the canonical rubric and includes its version and file SHA-256. `GET /api/dictionary` is read-only and does not need a pilot workspace. The UI lives in `explorer_ui/dictionary.js` and `dictionary.css`.

Add future concepts as entries with definitions, methods, practical meanings, boundaries, related IDs and sources. A scientific change to the scoring rubric needs a separately frozen version; an explanatory guide edit does not rerate any existing passage.

This change makes no inference calls or notebook writes. It leaves the research snapshot and frozen scoring files unchanged.

## Verification · 18 September 2026

313 Python and 62 JavaScript tests passed. Tests cover canonical rubric consistency, complete measure coverage, valid references, safe rendering, search and category combinations, unavailable terms, export/API origin enforcement, and preservation of the complete Gem return state. Live-browser checks cover sidebar access, measure selection, synonym search, matrix links and the return path to the selected filtered matrix.

The length-axis extension passed 313 Python and 66 JavaScript tests. Its version is `dictionary-2026-09-18-v2`; the six frozen scoring rubrics are unchanged.

The expansion update (`dictionary-2026-09-18-v3`) clarifies that the original sample has one target per lineage while the expansion permits three across both samples. Word count and correlation definitions now apply to both development samples; the frozen assessment rubric is unchanged. See [Gem expansion](GEM-EXPANSION.md).

The research-entities update (`dictionary-2026-09-18-v4`) adds 22 entries, revises the existing passage and lineage explanations, and organizes the 24 entity/unit definitions into their own section. The six frozen scoring rubrics remain unchanged.

The terminology update (`dictionary-2026-09-18-v5`) retires passage as a standalone entry, redirects old links to Message and uses precise message/excerpt/control labels across the active interface. Validation: 362 Python tests and 102 JavaScript tests passed; the live browser verified the old dictionary URL, separate message/control populations and old pivot count recipes.
