# Session record — multivariate Analysis workspace

Recorded: 2026-09-17T16:38:54.555933-03:00
Timezone: America/Argentina/Cordoba
Scope: the researcher’s “go next” authorization to implement the embedded pivot/visualization workspace, probability transformations and saved analyses.

## Completed and verified

- Added Analysis to the lab sidebar and supported JEV batches. The full React PivotTable UI retains drag/drop dimensions, value filters, aggregators, ordering and renderer switching. Added touch-friendly row/column selectors.
- Tables, full/row/column heatmaps, bars, stacked bars, lines, original-score histograms and scatterplots share the filtered passage matrix. Cells/marks open contributing passages and source transcripts; Back restores the configuration and selection.
- Added continuous, binary, custom-band and quantile transformations. Exact threshold boundaries, missing values, frozen quantile references and ties have dedicated tests. Source probability scores are unchanged. Quantile cutpoints and reference fingerprints save with each analysis.
- Joined broad/detail intact-window packs and the original reused success into 27 distinct passage rows, without counting failed/recovery attempts as extra observations. The 31-passage expanded qualification (53 questions) and 200-passage pilot (eight topics) remain separate selectable datasets.
- Added target-speaker model metadata, family/weight access, experimental conditions, identity, composition, external-intervention fields, history, recorded temperature/top-p and quality metadata. Historical missing fields stay unknown.
- Saved one Codex-attributed starter recipe: **Broad AI × consciousness · 90% thresholds**, ID `67d7f5dc00dea92409b96b2e`, revision 1. This is an interface configuration, not a human reading or a new behavioral finding.
- Added central atomic revision storage, conflict checks, matrix/provenance fingerprints, recipe/CSV/history export and chart downloads. No browser-local database is needed. Widget dependencies are pinned, bundled locally and lazy-loaded, with license notices.
- Tests: **246 Python tests, 34 JavaScript checks** passed. Browser checks confirmed transformations, multiple renderers, exact three-passage cell drill, an 18-passage histogram-bin drill, 31-passage nested-dimension grand total, source/back navigation, model filtering with unchanged 3/18 Consciousness quantile cuts, and saved configuration restoration.
- appHub owns the restarted local server on port 8765. It is serving the new Analysis routes.
- Research snapshot export included a complete separate restore/reindex test. All **2,165 prior files** are byte-identical; the sole added evidence file is the starter analysis recipe. New snapshot: **2,166 files**, SHA-256 `69746736c5fcdd6bc7108b62ce6da418d3d596e9a00b3997696f354f9a3600d6`. Prior snapshot retained in `/tmp/lab-research-before-analysis-20260917`.
- All fourteen existing notebook tables remain unchanged: `b6b38ae993980bae033b17091a2c07da323c8497a1d1f6197d9e7747529476b0`. No frozen JEV software, dictionaries, requests, responses or existing readings were modified.
- GitHub visibility verified **PRIVATE** for `ebergel/ai-behavior-lab`; this session prepares the tested code/data update for commit and push. The Git history records the final publication state.

## Scope and remaining work

No inference calls, model downloads, automatic scheduler, remote-access setup or public release occurred. These are assessed development samples, not a whole-corpus analysis or calibrated model-preference estimates. Full-corpus dispatch still needs its separately frozen paced runner and finite authorization. Independent semantic validation remains pending. Analysis can be used immediately to explore distributions, threshold sensitivity, cross-topic associations and exact underlying passages.

See `docs/ANALYSIS-WORKSPACE.md`, `docs/evidence/analysis-workspace-validation.json` and the updated continuation guide. Source inspiration: the researcher’s `icebergsim-dataExplorer` and `ANCMozambique` projects; this lab uses its own server for central persistence.
