# Population in view

The library, Mind & discourse, Gem Finder, JEV Topic Atlas and Analysis show a common population banner. It separates the inventory, the selected dataset and the currently filtered subset. Counts update with the view's existing filters; this adds no inference or evidence mutations.

| Stage | Meaning |
| --- | --- |
| Lab library | Started reference and laboratory conversation records, with their existing recorded participant-message counts. Synthetic engineering fixture records are reported separately. Unstarted assessment slots are excluded. |
| This sample / dataset | The full selected assessment sample or dataset, before its browsing filters. Each target is a selected passage, not a question, request, rating or wording condition. |
| Current subset | All matching targets or records after the view's population filters, before pagination. Source record counts and the share of the sample are shown where applicable. |

An unknown count is displayed as **—**. An empty result is **0**. Different datasets can overlap; their target counts must not be added together. Source record counts do not establish independent conversation lineages or experimental replicates.

## View-specific scope

- **Library, Run atlas and Results:** the middle stage is the selected library scope (all, reference, laboratory or synthetic fixtures). Collection, model, condition, signal, topic flag, tag and text filters determine the current subset. Page size is labeled separately.
- **Mind & discourse:** transcript passages and Codex-authored synthetic control texts are separate samples. Topic threshold, source model, length and search restrict targets. Feature family, feature choice, wording and sorting do not reduce the target sample. The selected wording is context, not a population filter. Requests, feature counts and cost remain under **Assessment details**.
- **Gem Finder:** the selected original/expansion/combined sample is the base. Model, leading broad-topic profile, reading queue, text, length and active bin restrict the subset. Hidden-score mode preserves the existing bin bypass. A separately opened unscored reader example is identified in the sample detail.
- **JEV Topic Atlas:** the selected batch is the base; comparison queue, probability bin and text search determine the full passage queue. Topic selection alone in “All passages” does not filter targets. The topic overview and histogram continue to describe the full batch; the banner explicitly distinguishes these from the filtered reading queue.
- **Analysis:** dataset rows form the base. The raw topic threshold applies before transformations; current pivot exclusions then determine the subset. Selecting a pivot cell for close reading is reported as a separate reading selection. Organizing topic selectors or changing transforms alone does not create a population restriction.

## Verified examples, 18 September 2026

The live library has **472** nonsynthetic records and **11,245** recorded participant messages, plus **60** separate synthetic fixture records. These are inventory counts, not behavioral prevalence estimates.

Mind & discourse has **48** transcript targets and **12** separate synthetic control texts. Consciousness ≥80 retains **3/48** transcript targets (6.3%); ≥90 retains **1/48**. Its 240 completed requests are four wordings over 60 texts, not 240 distinct targets.

Full-corpus Analysis contains **11,054** eligible target passages from **468** source records. Its default pivot exclusions leave **11,013** targets from **437** records. Adding Consciousness ≥80 leaves **2,111** targets from **272** records. Message eligibility, dataset selection and current filters explain why these totals differ from the library's recorded messages.

The implementation reuses existing catalog/message counts, frozen samples and view-specific selection functions. Research transcripts, classifier definitions, receipts and notebook rows are unchanged.
