# Topic Trajectories

Implemented 17 September 2026. Open **Topic Trajectories** in the Explorer sidebar, or use `#view=trajectories`.

The view connects the saved JEV score matrix to the actual path through each conversation. It introduces no inference and does not change the topic dictionaries, scores, source transcripts or notebooks.

## Reading a conversation

Filter by participant model, partner disclosure or task; search conversation titles, conditions and model IDs. Select a conversation from the paginated list. Its model badges, condition tags, exact recorded prompt and settings remain next to the analysis.

Each heatmap row is a topic question; each column is a position on the selected source path. Column headings show the recorded turn and speaker. Broad domains, experiential topics, conversation forms, stances and coverage checks can be viewed separately or together. Sort topics by mean score, first observed threshold crossing, or name. Colour and numbers retain continuous 0–100 scores.

Click a cell to select its topic and passage. A line chart shows the selected topic over time, with gaps for unknown values. The passage panel contains the exact visible output. **Read & annotate** opens the existing reader at the same message and branch; its Back button restores the trajectory selection. Existing notebook actions stay in the reader. The selected filters, branch, topic, threshold and passage are encoded in the URL.

The threshold switch offers 50, 80 and 90. Summaries show scored positions, positions at or above the threshold, first observed crossing, longest consecutive streak and observed re-entries. A re-entry requires a high score, one or more observed below-threshold scores, then another high score. Missing scores and external events interrupt comparisons and streaks. They are not treated as zero or as evidence of departure. First crossing is a **path position**, not necessarily the recorded turn number and not proof that the topic was absent in unavailable earlier content.

Alternative branches follow their real segment ancestry. They are never concatenated as though one dialogue experienced both futures. Shared nodes appear once on a path. External interventions occupy an explicit event column, separate from regular participants. Recorded caps and other quality flags remain visible.

## Scope and interpretation

The current discovery view includes **377 of the 437 assessed conversation records**. All **60 reserved validation conversations** are withheld, including neighbouring text and their score arrays. The separate 41 technical/short targets are outside this view. This restriction protects the reserved reading workflow; it does not certify that a future reviewer has never seen these conversations elsewhere in the lab.

JEV scores describe a target in its supplied context. Adjacent assessments share context; they are not independent measurements. Crossings, streaks and returns are descriptive score patterns, not validated topic adoption, causal influence or evidence of experience. Topics overlap. Independent semantic validation remains pending.

The service rechecks the selected source hash and exact message text against the scored matrix. Stale scores become unknown and their old text is not served as a current passage. It reads the existing analysis cache, so the first load after a server restart may take longer while receipts are checked. Refreshing source evidence can invalidate scores but never generates replacements.

`GET /api/topic-trajectories` and `/api/topic-trajectories/export` take a JSON `filters` query. The export includes the selected path, scores, summaries, source hash, matrix fingerprint and interpretation rules. It excludes reserved records, hidden reasoning and other conversations' text. It does not save a new research annotation.
