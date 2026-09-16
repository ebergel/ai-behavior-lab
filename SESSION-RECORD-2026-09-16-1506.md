# Session record — Topic tags in Conversation Finder

Timestamp: 2026-09-16T15:06:50.056716-03:00
Scope: add Topic as a selectable search criterion above Models, using the Topic atlas dictionary.

## Completed

Added the **Topics** facet above **Models**, with all current dictionary entries, readable labels, selected states and contextual counts. Topics combine with OR, then combine with other facet groups using AND. **Topic evidence** chooses any-turn, first-six or repeated literal matches, or current attributed initial-topic reviews. The index reuses the atlas scanner, eligibility rules and review freshness checks. Topic matching covers the whole conversation independently of the model-role filter; it does not attribute the topic to that selected model.

Result cards show the selected matching topics, an evidence excerpt and direct supporting-message links. Reviewed initial choices show the review author. Topic selections and evidence mode persist in filter URLs, saved views, search, cohorts and transcript return. A shortcut opens the selected dictionary entry in Topic atlas. Existing definitions, flags and notes stay separate. Short technical records remain in unfiltered Finder but do not gain atlas topic matches.

Updated the Finder, Topic atlas, Explorer and continuation guides. The existing Explorer service was restarted on port 8765 to load the new read-only API integration; model engines and WebUI were untouched. No inference, spending, downloads or scheduling occurred.

## Verification

202 Python tests and 14 JavaScript checks pass. New tests cover all four evidence modes, exact passage links, atlas count agreement, model/cohort/search combinations, role independence, zero-count and unavailable topics, duplicate mentions, dictionary/source refresh, stale reviews, saved-view persistence, UI ordering and route preservation. Browser checks confirm the clickable topic/model combinations, supporting-passage return, the empty reviewed Consciousness case and attributed Emergence result.

Live count comparisons agree with Topic atlas: Consciousness = 204 any-turn, 155 first-six, 165 repeated and zero reviewed initial choices; Emergence = 115, 83, 79 and two respectively. Consciousness plus Haiku yields four records. These are existing discovery counts, not new semantic ratings. The reviewed Haiku-to-Gemma Emergence proposal links Y2 and retains Codex authorship.

All rows in fourteen SQLite tables match the pre-change backup. All 111 earlier source artifacts and 32 frozen pilot dependencies verify unchanged; the pilot journal hash remains `3c7da636c58d0626a32ba6fa4770578dee4d73c522e92fe962a0cd759c8c8f90`. Saved-view persistence was tested in an isolated temporary database; no testing notes, reviews or views were added to the main notebook.

Evidence and backup: `workspace/finder-topics-20260916-1501/`. Portable verification: `docs/evidence/finder-topics-validation.json`. Screenshot: `docs/evidence/finder-topics-20260916.jpg`. The browser is left on Consciousness plus Haiku in the any-turn phrase-match mode.

## Pending

The prospective opening/partner runner qualification and finite freeze remain pending. This turn implements the requested navigation layer only.
