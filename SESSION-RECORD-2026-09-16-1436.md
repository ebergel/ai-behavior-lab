# Session record — Opening and partner development study

Timestamp: 2026-09-16T14:36:36.561034-03:00
Scope: accepted next step from the lab vision: develop the opening/partner study from existing evidence, build a comparison workspace, and specify prospective tests.

## Completed

- Created research collection **Opening & partner: who sets the direction?**, ID `f15547eb8cf7b85d4bcb413c`, revision 1, with twelve roots and five findings. Two protocol blocks remain separate: four Gemma–Haiku pilot roots and eight paid mini/Haiku framing roots.
- Added eight Codex opening reviews after reading framing messages 1–6 (48 new message readings). Reused four existing pilot reviews unchanged and rechecked their proposal/uptake evidence. Prior full readings retain their original scope and authorship.
- Recorded nine Y2 proposals, two X1 proposals and one X3 proposal. Mini's mirror examples differ between fiction and contextual understanding; both anonymous Haiku examples initially negotiate identity/setup. These are retrospective development readings, not preference estimates or causal partner effects.
- Added **Participant identity & setup** as a separate provisional dictionary entry. Explicit rationales retain ambiguity about identity challenges as topic proposals and functional versus experiential preference language. Dictionary entries now total 23; current opening reviews total 12.
- Added **Study workbench** for up to four opening windows from any research collection. It shows model identities, proposer/uptake source links, protocol blocks, setting differences/unknowns, exact prompts, complete opening text and export. Bookmarkable reader links retain comparison selections and default personal observations to the source collection.
- Linked an attributed Codex research question from Purpose & musings to this collection. Existing researcher passages and musings remain unchanged.
- Wrote `docs/OPENING-PARTNER-STUDY.md` and `docs/OPENING-PARTNER-DESIGN.md`, updated continuation/Explorer guides, and exposed the prospective design through the workbench.

## Prospective design, not executed

Read-only inventory confirms installed `qwen3:4b` (4.0B total parameters) and `gemma4:e4b` (8.0B total parameters). These are tractable but not size-matched candidates. Serving qualification has not been transferred from the earlier larger pair.

The design specifies five repetitions of A–A/A–B/B–A/B–B with eight messages each (160 calls), then ten predetermined mirror-root opening slots × two responding models × three independent single-response draws (60 calls). At most eight separately labeled technical checks bring the maximum to 228 local calls. No download or cloud fallback is included. Missing source slots retain omissions without replacements; repeated draws are clustered by source opening. A separate versioned runner, technical/scoring qualification, seed allocation/audit and executable freeze are the next implementation milestone. No calls in this proposed allocation have run.

## Verification and preservation

198 Python tests and ten existing JavaScript checks pass; edited scripts pass syntax checks. New tests cover distinct opener/proposer identities, stale reviews, unknown settings, protocol grouping, invalid selections, missing sources/windows, read-only behavior and local API/export access. Browser checks cover selection limits, block selection, setting differences, equal recorded mini mirror conditions, reader navigation/full reload, collection-linked observation defaults and the design dialog. No browser test note was saved.

All preexisting rows in fourteen SQLite tables remain byte-identical. Additions: one collection/history row, eight opening reviews/history rows, one dictionary entry/history row, and one Codex musing/history row. Five personal notes, 28 topic flags, all earlier collections (including the researcher's expanded 25-run first collection), four pilot reviews and prior musings are preserved.

111 earlier source artifacts and 32 frozen pilot dependencies verify unchanged. Pilot journal SHA-256 remains `3c7da636c58d0626a32ba6fa4770578dee4d73c522e92fe962a0cd759c8c8f90`. No new inference, spending, downloads, independent human ratings or automation occurred. Explorer remains on port 8765; other model/WebUI services were not restarted.

Evidence and backup: `workspace/opening-partner-20260916-1421/`. Portable verification: `docs/evidence/opening-partner-validation.json`; overview and close-reading screenshots are adjacent. The preparatory script was first tested against copied notebook databases, including an implementation error fixed there before applying the complete reading to the main notebook.
