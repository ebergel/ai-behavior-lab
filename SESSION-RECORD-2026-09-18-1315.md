# Session record · Lab dictionary

Recorded: 2026-09-18T13:15:34-03:00
Timezone: America/Argentina/Cordoba (UTC−03:00)
Scope: implement the user’s requested dictionary of definitions, technical specifications and practical interpretations, beginning with every Gem Finder measure.

## Completed

- Added **Lab dictionary** as a first-class sidebar section, searchable by words, synonyms and technical content; 17 terms in three groups.
- Documented all seven measures: conversational surprise, conceptual contribution, creative connection, expressive force, conceptual complexity, substance and specificity, and topic-profile distance.
- Each measure includes a definition, practical reading, lower/higher interpretation, clearly labeled illustrative example, technical specification, limitations and related terms.
- Six JEV entries load their exact questions, five criteria and shared scope from the canonical frozen rubric. The read-only export includes its version and file SHA-256.
- Supporting entries distinguish scaled expected levels, level probabilities/confidence, semantic topic probabilities, Pearson r and n, plot ranges, missing values, passages/context, lineages, profile leads and personal gem judgments.
- Added direct definition links to matrix measure names, focused plots, individual rating panels and neighboring-profile details. Related-term navigation retains the return link to the complete Gem view.
- Documented the guide and updated continuation notes. Enabled Dictionary view links in task cards without changing any saved task.

## Verified

- 313 Python and 62 JavaScript tests passed (375 total). The 16 relevant JavaScript tests also passed after the final navigation adjustment.
- Canonical rubric consistency, reference resolution, API origin enforcement, safe HTML, search/category selection, invalid return-state handling, empty/unknown terms, and full Gem return-state preservation were checked.
- Live browser: inspected visual layout; opened all seven measure entries; searched the synonym ‘outlier’; opened a definition from the matrix, followed a related term and returned to the filtered matrix. Codex-example filter, observed ranges, the selected Haiku passage and its 42 matrix highlights were retained. Focused-plot links and six individual assessment links were present.
- App Hub restarted the existing local server successfully; the Dictionary is live on port 8765.
- Frozen scoring software hashes still exactly match the saved pilot plan. The pilot remains 100 passages, with 8,371 profile-reference passages.
- Confirmed GitHub repository ebergel/ai-behavior-lab remains PRIVATE before saving this update.

## Evidence boundary

No inference calls or costs; no notebook, task, transcript, assessment or research-snapshot mutations. The examples in the Dictionary are explanatory illustrations, not scored evidence or human ratings. The original topic vocabulary remains separate. Existing session records are preserved.

## Next phase / proposals

The Dictionary is extensible to other laboratory concepts. This milestone documents existing measures; it does not validate them or change their scores. Researcher example collection and independent measurement qualification remain pending. A future scoring change requires a separately frozen rubric and assessment version.
