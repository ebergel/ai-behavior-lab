# Purpose, musings & ideas board

Purpose & musings is the first workspace item and the default landing page. Its three tabs keep the lab's direction, reflections and actionable work together:

- **Working purpose** — the evolving research charter and experimental space.
- **Musings** — attributed questions, hypotheses and reflections, with earlier wording preserved.
- **Ideas & tasks** — a board with **Ideas → Next → In progress → Done**.

The Current focus strip appears above all three tabs. It shows up to three active cards and three Next cards, in their board order, with a link to the complete board. Empty In progress means no work has been marked active. A status change records a planning decision; it does not launch an experiment or schedule future work.

## Using the board

Capture an idea with one sentence. A workstream is optional: **Exploration tools**, **Experiments**, or **Research synthesis**. The first two reflect the researcher's parallel tracks of tool development and experimental data generation; synthesis connects both through interpretation and independent review.

Open any card to add notes, the next action, a definition of finished, a blocker and links. Search covers the title, notes, completion criteria, blocker and completion note. Workstream and search filters combine. The Archived switch displays recoverable archived cards.

Use **Move to** on a card to change its column; these controls work with mouse, keyboard or touch. The **↑** button moves it to the top of its column, also changing its order in Current focus. Done requires a short completion note. A completed card can be reopened; its earlier completion remains in history. Archive and restore also create revisions.

**Create task** on a musing opens an editable task draft. Saving captures that musing's exact current body, author and revision, its earlier source attribution, and a link to the live entry. Later revisions of either entity do not rewrite the captured source. Task authorship remains distinct from musing authorship.

The link picker connects musings, research collections, designs/reports and lab views. Paste a lab transcript URL to link a conversation or exact message and branch. These links are stored as validated local identities, so they work after restoration on another computer. The transcript reader has a **Back to Ideas & tasks** link to the originating card. Unsaved pasted links become navigable after validation on save.

## Initial priorities

The five starter cards are **Codex planning summaries**, not researcher quotations or completed research:

- **Next:** define the Gem Finder rubric; qualify the replication candidates.
- **Ideas:** independent topic-score review; freeze a balanced factorial experiment; remote access after router/hardware setup.

The existing remote-access plan in `TODO.md` remains parked. Scientific qualifications, independent readings, design decisions and finite inference allocations remain requirements of their respective tasks. Choosing Next does not satisfy them.

## Storage, history and restoration

Cards and their revisions are stored in separate `lab_tasks` and `lab_task_history` tables in the existing `workspace/explorer/notes.sqlite` notebook. The prior notebook tables and source transcripts are preserved. Every save checks the expected revision; a stale edit is rejected rather than overwriting another edit. The original task author cannot be reassigned. Seed insertion is idempotent and never replaces an edited or archived seed.

**Export planning & history** downloads the purpose, musings, cards and their complete revision histories. It is a planning export; passage notes and other research annotations retain their existing exports. The private `research/` snapshot includes both new tables through the existing generic notebook exporter and restores them with exact row values. Live edits are immediately local; publishing another GitHub snapshot remains a separate operation.

Routes: `#view=purpose`, `#view=purpose&section=journal`, `#view=purpose&section=tasks`, and `#view=purpose&section=tasks&task=ID`. Empty hashes open Working purpose. Explicit library links use `#view=library`; older filtered transcript links keep working.

The API preserves existing local-origin and write-token protections. There are no external services, model calls or new dependencies in this feature.
