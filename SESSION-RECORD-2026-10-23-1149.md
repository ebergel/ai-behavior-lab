# Session record — Ghost HTML card

Recorded: 2026-10-23T11:49:52.436684-03:00 (America/Argentina/Cordoba).
Scope: adapt the public research milestone into a paste-ready Ghost HTML card for t333t.com.

## Completed

- Added a reproducible builder and identical HTML/text card exports under docs/reviewer-milestone-20261022.
- Embedded the complete report and data in a sandboxed iframe, isolating CSS and JavaScript from the host theme. Added automatic height and section-navigation messages, checked against the specific frame source.
- Added Ghost installation instructions and a public standalone fallback link. Original report remains unchanged.

## Verified

In a local browser fixture with deliberately contrasting host styles: interactive topic group and measure controls updated the chart and table (12 focused topics); frame height adjusted from 11,405 to 11,040 pixels; Gem axis control changed values; workload slider changed to 540 conversations; internal navigation scrolled the parent page to the findings section. Host button retained its crimson styling, there was no horizontal page overflow, and no console errors were recorded. JavaScript syntax checks passed during preparation.

## Limits and next action

Not tested in the live t333t.com Ghost installation. No Ghost post was created or published. User should paste the entire text export into one HTML card and preview the web post. Email cannot retain interactive scripts/frames; provide the report link. Pasted content is a frozen snapshot and must be replaced to update it. GitHub publication is handled after this record; this record does not itself assert deployment success.
