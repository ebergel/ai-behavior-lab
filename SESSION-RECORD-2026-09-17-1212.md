# Session record — JEV topic list and two-tier design

Recorded: 2026-09-17T12:12:27.889972-03:00  
Timezone: America/Argentina/Cordoba  
Scope: requested sortable topic overview and research design discussion; no inference.

## Completed and verified

- Added Cards/List view, topic-name/definition search and nine sortable columns: topic, scored targets, candidates, candidate share, mean/median probability, uncertainty, candidates without phrase matches and saved readings.
- Topic names select the active topic; candidate, uncertain and no-phrase counts open the corresponding passage queues. Overview search/sorting and source-return navigation retain their URL state.
- Statistics use topic-specific scored denominators. Unknown values remain unknown and sort last; topics can overlap. Hidden-judgment mode hides semantic values and ranking while permitting alphabetical topic sorting.
- Live browser checks verified both candidate sort directions, mean sorting, search, 42-passage Emergence uncertainty queue, source return, cards/list switching and hidden judgments. Table scroll remains within its panel without horizontal page overflow.
- All 222 Python tests and 24 JavaScript checks passed. Three new JavaScript tests cover scored denominators and overlapping topics, zero-versus-unknown sorting, and bookmark/hidden-judgment state.
- All 403 frozen JEV plan/request/response/integration files match the research snapshot. All fourteen original notebook tables match it exactly. Frozen runner files and the research snapshot were not edited. No reviews were written; nine live saved readings remain intact.
- Wrote `docs/TWO-TIER-TOPIC-DESIGN.md`, updated the JEV guide and continuation notes, and saved browser evidence in `docs/evidence/jev-topic-list.jpg` and validation JSON.

## Proposals, not results

- Broad-domain analysis and experiential analysis should cover the same eligible corpus, without exclusively gating the second tier on positives from the first.
- Drafted 24 broad domains and content/form distinctions. Proposed an open-ended development reading to discover omissions, explicit corpus/lineage/denominator rules, threshold sensitivity and independent reference coding.
- The existing eight-topic pilot and its frozen 23-entry dictionary are unchanged. No new vocabulary was installed and no whole-corpus assessment, model comparison or calibration was run.
- Recommended next step: finite coverage-development reading and corpus inventory, followed by a separately frozen adapter qualification and aggregate budget. The completed pilot's allocation remains exhausted.

## Preservation and deferred work

No model calls or new cost. No remote-access work or scheduled continuation. The existing research snapshot retains seven Codex JEV readings; two later researcher readings remain in the live runtime and were not resnapshotted during this UI task. Original notebook content remains unchanged. Private repository publication continues the user's prior authorization; no public release is requested.
