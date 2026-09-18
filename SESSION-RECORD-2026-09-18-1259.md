# Session record · Gem Finder scatterplot matrix

Recorded: 2026-09-18T12:59:04.316088-03:00 · America/Argentina/Cordoba (UTC−03:00).

Scope: The researcher requested a full scatterplot matrix to inspect relationships among all Gem Finder measures. This session is a UI refinement of the completed pilot, not a new scoring experiment.

## Completed

- Added a plot-view switch between the full matrix and the existing pair/distribution view.
- Matrix: seven measures, 42 ordered scatterplots and seven diagonal histograms. Every cell follows the current model, topic-profile lead, reading queue, text and histogram-bin selection.
- Added descriptive paired Pearson correlations and observed-pair counts. Zero is observed, absent/stale scores are omitted per pair, and correlation stays unavailable for fewer than three pairs or a constant measure.
- Added full 0–100 or observed axis ranges. Observed bounds round outwards to ten-unit boundaries and remain consistent per measure across the matrix. Empty and constant data retain finite display ranges. Range labels remain visible; profile distance retains distance units.
- Points link to exact passages and the selected passage is highlighted across all 42 scatterplots. A cell's r / arrow header opens its larger pair view. Plot mode, ranges, selection and filters survive source-reader navigation.
- Active histogram bins now retain their original measure when enlarging another pair, with an explicit Axis filter chip. Direct horizontal-axis changes retain the prior behavior of clearing the bin. Hidden-score mode hides the matrix and its controls.
- Dense points may overlap; the view explains this and provides pair enlargement. Keyboard activation is implemented for cell headers; the larger plot/list provides individual-passage keyboard navigation.
- Updated the Gem Finder guide and continuation record.

## Verified

- **367 automated checks passed: 310 Python, 57 JavaScript.** Five new tests exercise correlation and missingness, empty/constant/endpoint ranges, full matrix dimensions, retained bin semantics, filtering, score hiding and escaped text.
- Live browser: 49 cells / 4,200 plotted points for the complete 100-passage sample; seven diagonal distributions; no document overflow at the observed 1,191-pixel viewport.
- Observed ranges show surprise 0–80 and profile distance 0–20, with other measures 0–100 in this sample.
- Browser: a 27-passage expressive-force bin produces 1,134 points, and remains a 27-passage selection when a different pair is enlarged. A two-passage GPT-4o subset displays r unavailable / n=2. An empty search shows no plotted points or nonfinite geometry.
- Verified the isolated Haiku turn-10 point opens that exact passage and highlights its 42 matrix occurrences. Dense coincident/nearby points can intercept pointer selection; enlargement and point tooltips support inspection.
- Verified hidden mode removes matrix/score controls and returning from the full transcript restores the matrix, observed-range setting and selected passage.
- No new inference, notebook writes or changes to frozen scoring software, requests, responses or the research snapshot. The existing pilot remains complete and its finite allocation exhausted.

## Next phase

Researcher example collection and rubric evaluation remain the next research tasks. The correlations visualize existing descriptive associations; they are not significance tests, construct validation or a new result about model populations. Private GitHub publication of this UI refinement follows the checks; public release and scheduled work remain unrequested.
