# Analysis workspace

Open **Analysis** in the lab sidebar, or **Explore in Analysis** from a supported JEV batch. The workspace embeds React PivotTable UI with local Plotly renderers. It brings broad and specific questions into the same passage-level matrix, alongside the actual target speaker’s model, model family, weight access, conversation, experimental condition, identity framing, participant composition, external interventions, history, temperature and recorded output quality. Missing historical settings stay unknown.

## Start exploring

1. Select an assessment dataset. **Full corpus · broad & specific topics** contains all 11,054 visible source rows and the 53-question matrix, with live coverage shown separately. The two-tier development sample has 31 passages from 30 conversations and 53 questions. The intact-window sample has 27 passages from 17 conversations and the same 53 questions. The original pilot has 200 passages from 159 conversations and eight topics.
2. Choose a topic under **Probability → analysis variable**. Keep it continuous, apply a binary threshold, enter custom band boundaries, or fit quantiles. Repeat for other topics independently.
3. Drag fields into rows and columns. The **Add row / Add column** selectors offer the same arrangement without dragging, including on touch devices. Use a field’s triangle to filter values; search or group the available field list to reduce clutter.
4. Select an aggregator and renderer in the pivot widget. Switch among tables, full/row/column heatmaps, bars, stacked bars, lines, histograms and scatterplots without discarding dimensions, filters or transformations. Histograms and scatterplots have explicit score selectors and always use original continuous probabilities after the pivot’s filters.
5. Click a cell or chart mark to read its contributing passages. Plotly box/lasso selections also open contributing passages. Open a source transcript, then **Back to Analysis** to recover the setup and reading selection.
6. Save a named analysis and optional observation. Configurations and all revisions live under `workspace/analysis/views/`, independently of the existing notebooks. Export the recipe, filtered derived data, chart image or complete saved-view history. Refreshing or returning from a transcript retains the draft in the URL; use Save to keep it centrally.

A Codex-attributed starter view, **Broad AI × consciousness · 90% thresholds**, crosses a broad domain with a specific topic and groups counts by target model family. It is a reusable configuration, not a new semantic finding or human rating.

## Topic coverage

The sortable topic table lists broad domains, specific topics, discourse forms, stance and coverage questions separately or together. It reports observed denominators, threshold counts/shares, means and small probability histograms under the current pivot filters. Candidate thresholds are 50, 80 or 90; scores remain continuous. Click a topic or histogram to expand its distribution; click a candidate count to read those passages.

## Transformations and denominators

Raw JEV values remain in the frozen evidence. The matrix presents them on a 0–100 scale; derived columns never rewrite them.

- Binary: values below the threshold become 0; values at or above it become 1. At 90, exactly 90 and 100 are both positive.
- Bands: cut points are strictly increasing and internal to 0–100. Intervals include the lower bound and exclude the upper; the last includes 100.
- Quantiles: boundaries use linear interpolation (type 7) on every observed score in the selected dataset. They are saved with the dataset fingerprint and reference count. Duplicate boundaries collapse, boundaries at the minimum are removed, and tied scores remain together. Requested groups can have unequal counts or fewer distinct groups. Filtering models does not refit them. Apply again explicitly to refit.
- Changing a field’s transformation clears filters on that field, because the old categories no longer mean the same thing. Other filters remain.
- Missing, failed and stale-source assessments stay **Missing / unknown**. They never become a zero score. Histograms omit missing values; scatterplots require both scores.
- **Count passages** includes missing categories. **Count observed** and **Mean (observed)** use numeric observations only. **Percent = 1 (observed)** requires a binary field and divides positive counts by observed scores. Row, column and total percentages divide passage counts in the filtered pivot.
- **Count conversations** counts distinct conversation IDs within a cell. A conversation can contribute to multiple cells, so these counts are not additive.

Histogram bins are ten points wide, with the final bin including 100. Raw probabilities, transformed values and source passages are available together. Model assessments are not calibrated prevalence probabilities; the selected development samples cannot estimate whole-corpus frequencies or causal differences between models. Different passages from the same conversation are not independent replicates.

## Dataset provenance

The development sample uses batch `7f665a93c90cb1c2e1253d36`. The intact sample joins recovery broad/detail packs and the original first successful broad result exactly once, using the checked recovery release. It retains one row per source passage and rejects duplicate question scores or inconsistent target/context identities. The stopped overload is not an extra observation. The pilot uses `c8e5aca183e5777cdae09cfb`.

These datasets remain separate: assessment packing and sampling differ, and some source passages overlap. All 53 broad, focused, form, stance and coverage questions are available together within each two-tier dataset. The Analysis implementation performs no inference. The separately authorized [full-corpus coordinator](JEV-CORPUS-ASSESSMENT.md) populates a fourth dataset while preserving these earlier samples. Incoming scores do not silently change an open matrix. Load latest scores explicitly; this clears quantile fits and their filters. Saved corpus analyses preserve their exact matrix snapshots and remain available after completion or restart.

Each saved view records exact assessment-plan/request/response receipts and the matrix fingerprint. Writes use atomic, append-only revision files and optimistic revision checks. Source changes invalidate affected scores when building a current matrix. Earlier sample views reject changed matrices. Corpus views preserve an immutable matrix snapshot together with the exact evidence receipts; a saved historical snapshot describes sources at its capture time. A draft returning after another edit is kept as a new view rather than silently replacing the newer revision. Exports preserve histories. The existing notebook tables are untouched. Analysis records are included by the normal research snapshot exporter and restore with a fresh clone; unsnapshotted live edits still require a later snapshot/commit.

## Implementation and attribution

The user’s [icebergsim-dataExplorer](https://github.com/ebergel/icebergsim-dataExplorer) informed reuse of the full React PivotTable UI and serializable configurations. Its React/IndexedDB app is not embedded wholesale; the lab saves centrally through its own local server. The categorical/percentage pivot workflows in [ANCMozambique](https://github.com/ebergel/ANCMozambique) informed the transformation and aggregation interface. No R runtime is needed.

The widget is loaded only when opening Analysis. React, react-pivottable and Plotly are bundled locally, with pinned versions and [dependency notices](../web/analysis/THIRD-PARTY-NOTICES.txt). Normal app startup requires only the existing Python runtime, with no CDN, frontend build or Node server. Plotly cloud sharing is disabled. To rebuild the checked-in assets from the repository root:

```sh
npm ci --prefix web/analysis --legacy-peer-deps --ignore-scripts --no-audit --no-fund
npm run build --prefix web/analysis
python3 -m unittest discover -s tests -v
node --test tests/*.cjs
```

Source: `behaviorlab/analysis_workspace.py`, `web/analysis/`. Built assets: `behaviorlab/explorer_ui/analysis-widget.js` and `.css`. No frozen JEV runner or dictionary implementation was changed.
