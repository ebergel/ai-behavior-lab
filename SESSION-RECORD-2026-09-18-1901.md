# Session record — precise research-unit labels

Recorded: 2026-09-18T19:01:10-03:00 · America/Argentina/Cordoba (UTC−03:00).
Scope: the researcher's follow-up that “Passage (legacy term)” remained confusing and widely used in dialogs.

## Completed

- Retired the standalone Passage dictionary entry. Dictionary v5 has 39 entries, including 23 research entities; old passage URLs redirect to Message, and passage remains a search alias.
- Applied message terminology to current whole-reply assessment samples, population banners, Gem plots, JEV queues, Mind & discourse tables, Analysis and source navigation. Synthetic controls have separate text labels and matrix headings.
- Reader actions distinguish Save message, Save intervention and Save excerpt. Saved notebook quotations may contain a whole message or an explicit excerpt; quoted source text and note content are unchanged.
- Library inventory is labeled runs because it includes conversations and technical checks. Mind & discourse uses its verified source conversations; unrestricted Analysis, Gem and JEV use source runs. No counts or eligibility rules changed.
- Old pivot Count passages / Count conversations recipe labels normalize on load to Count messages / Count source runs, preserving dimensions, filters and counts. Stable transport keys, route enums, IDs and saved recipes remain compatible.
- Updated the dictionary, population and research-unit documentation and the continuation log. Rebuilt the Analysis bundle and restarted the app through App Hub.

## Verification

- 362 Python tests passed; 102 JavaScript tests passed. UI JavaScript syntax and whitespace checks passed.
- Browser: an old passage URL resolves to Message; Mind & discourse displays 48 messages from 48 conversations, while the 12 synthetic controls remain separate and the matrix labels them Control text.
- Browser: an old Count passages recipe renders Count messages and the same 27-message intact-window total; Gem Finder displays the 1,000-message combined sample from 376 source runs.
- Browser: JEV intact-window recovery displays 27 messages and 17 source runs, with message queue and sampled-message labels.
- No inference, notebook edits, evidence changes, scientific denominator recalculation or frozen rubric/payload changes. Original instrument wording is explicitly labeled where shown. No raw transcript text was replaced.

## Remaining scope

The library participant-message/event eligibility audit remains a separate research task. Historical reports, exact frozen questions, saved researcher prose and source evidence retain original terminology. They are not silently rewritten by a display migration.
