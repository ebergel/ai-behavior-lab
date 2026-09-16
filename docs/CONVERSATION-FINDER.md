# Conversation Finder and model identity

Implemented 16 September 2026. Open **Conversation Finder** in the Explorer sidebar. Choose topic and setup tags, then read matching conversations with their participants and conditions in view. Model badges use consistent family colors across the library, reader, comparisons, collections, notebook, topic results and assessments. Short labels retain Base/Instruct/Think/modified variants and local/hosted distinctions; hover or open **Setup details** for exact IDs and recorded digests. Color supplements the written label.

## Selecting conversations

Choose a research collection or the whole reference/laboratory inventory. Synthetic fixtures and unstarted slots are excluded. Recorded technical checks remain included and labeled. The initial inventory is **472 records**, not 472 comparable experimental replicates.

| Control | Meaning |
|---|---|
| Regular participants | Model, developer and weight-access filters inspect ordinary conversation slots. |
| External interventions | Those filters inspect recorded external insertions, separately from the regular roster. |
| Anywhere | Those filters inspect both roles. |
| Contains any selected model | At least one chosen exact model ID occurs in the selected role. |
| Contains all selected models | Every chosen exact ID occurs in that role; additional models are allowed. |
| Any model in this role | Each selected developer/weight group needs at least one match. Different groups may match different models. |
| Every model in this role | All models in the selected role belong to the chosen developer set and/or weight-access set. Empty roles cannot satisfy a selected group. |

Groups combine with AND. Values within a group combine with OR, subject to the explicit all/every controls. Participant count and composition always describe the regular roster. Selecting a role alone changes which entities model filters inspect; select **Recorded intervention** to require an external event without specifying its model.

Facet counts answer: “How many records match if this group is replaced with this one value, retaining the other conditions?” They are not sums or predicted increments when adding another choice. The total above the results is the combined selection. Recognized but unobserved configurations, such as three regular participants and named-model disclosure, show zero.

Search covers saved visible text and inventory metadata. Sort by date, title or word count. Reader and comparison return links retain the Finder recipe and page. A model badge opens a matching selection; within the Finder it preserves other setup conditions, and from a research collection it retains that cohort. Topic atlas remains the home for definitions, variants and frequency analysis. Finder now combines those dictionary topics with setup filters; personal topic flags remain a separate annotation layer.

**Save view** stores a named filter recipe with authorship and immutable revision history. Updates require the current revision. Views remain dynamic as evidence grows; they do not freeze a scientific cohort. Export includes view history and the reviewed model catalogue. Research collections remain the place to save specific reading sets and findings.

## Topic tags above Models

The **Topics** group is the first facet, above **Models**. It uses the current versioned Topic atlas dictionary, including newly added entries. Select one or more tags; topics combine with OR, then combine with model and setup groups using AND. Counts retain the other selected conditions and replace the topic group with the counted entry. Zero-count entries remain available.

**Topic evidence** chooses the same interpretation as the atlas:

| Mode | Included conversations |
|---|---|
| Any turn · phrase matches | A literal variant appears in at least one participant reply. |
| First 6 · phrase matches | A variant appears within the first six participant positions. |
| Repeated · phrase matches | A variant appears in at least two distinct messages. Repetition inside one message is insufficient. |
| Initial choice · reviewed | A current, attributed opening review selects the topic. Source/dictionary-stale reviews and unreviewed openings do not qualify. A reviewed choice can qualify without any literal match. |

Topic matching uses the atlas's eligible corpus (at least six participant positions); unfiltered Finder still includes shorter technical checks. Prompts, reasoning traces and external intervention text do not supply dictionary matches. Topics apply across the conversation even when the model filter targets an external role. This does not attribute the topic to the selected model. A literal match is not a semantic classification or a claim of experience; absence of a match is not evidence of conceptual absence.

Selected topics appear on result cards with a supporting message link and excerpt. Reviewed initial topics show the review author. These links preserve the Finder selection when returning from the reader. **Save view**, URL bookmarks, search, cohort selection and pagination retain topics and evidence mode. Saved views remain dynamic when the dictionary or reviews change; source content and annotation history stay untouched. **Open Topic atlas** opens the selected topic (the first selected ID if several are selected) in the current reading cohort; other Finder conditions are not transferred to the atlas.

Validation added 16 September: 202 Python tests and 14 JavaScript checks pass. Live API comparisons agree with atlas counts for Consciousness and Emergence across all four modes. See [the topic-filter validation](evidence/finder-topics-validation.json). Earlier verification below records the original Finder milestone.

## Meaning and provenance

| Property | Recorded basis |
|---|---|
| Same model / Mixed models | Exact regular model IDs, independently of prompt disclosure. Same ID does not imply identical runtime settings; inspect settings and digests. |
| Anonymous-Full | The recognized anonymous prompt leaves partner identity unspecified. This does not establish absence of all identity cues. |
| Anonymous-AI | The prompt calls the participants AI models without naming their identities. |
| Mirror | The prompt explicitly describes another instance of the same model. Generated self-descriptions never supply this tag. |
| Named models | Reserved for explicit `identity_framing` metadata; no current records. Unrecognized prompt recipes remain Unknown. |
| Human presence | Explicit no-human wording, otherwise unspecified or unknown. |
| History | Recorded segment F/R policy. Historical chat/completion mode does not establish history access. |
| Task / exit | Recognized prompt instructions. Exit-token permission does not establish actual scheduler behavior. |
| Thinking | Explicit per-speaker setting when recorded. Model variant and runtime setting remain separate. |
| Developer / lab | Reviewed original model-family attribution. Derivative publishers remain visible in full IDs. Inference provider is separate. |
| Weight access | Open, closed or unknown. Open weights makes no open-source license claim. Free API access is not evidence of open weights. Uncatalogued IDs stay Unknown. |

The reader banner shows the roster, opening speaker, thinking setting and key conditions. **Setup details** exposes the basis and full identities. External interventions have separate badges and AFTER positions; the event list contains exact text and transcript links. An unused historical `third_model` setting never creates an event or third regular participant. Scheduled-but-unrecorded interventions have a separate state.

Tags are derived projections (`experiment-facets/1`); they do not modify prompts, journals, dictionary definitions, reviews or personal tags. The roster projection accepts more than two ordinary slots; this does not qualify a trio runner or eliminate remaining X/Y assumptions elsewhere in the laboratory.

## Verification

- **184 Python and 10 JavaScript tests pass**, covering role separation, real-trio counting, unknown metadata, filter semantics/counts, cohorts, pagination, view revision conflicts, local authorization and rapid tag changes.
- Browser checks exercise combined model filters, exact intervention jumps and return, colored local/cloud identities, collection/topic navigation, and saved-view persistence in an isolated database copy.
- Google as regular participant: **55**; external intervention: **40**; anywhere: **95**. Requiring local Gemma 26B and Haiku returns **2** ordered mixed roots. Every regular model closed: **18**; any closed model: **20**. All **40** intervention records retain **2** regular participants. Regular trios: **0**.
- All **111** prior evidence artifacts and **32** frozen pilot dependencies verify unchanged. All ten earlier SQLite tables compare exactly to the backup: **5** personal notes, **5** collections, **28** flags, **22** dictionary entries and **4** opening reviews, plus histories.

Evidence: `workspace/finder-20260916-1307/`; screenshots and compact validation in `docs/evidence/`. No inference, downloads, cloud spending, semantic ratings or automation occurred.

## Model catalogue sources

Reviewed 2026-09-16. Existing laboratory records retain alias and derivative provenance. Primary sources for model family/weight availability include [Qwen3 Base](https://huggingface.co/Qwen/Qwen3-30B-A3B-Base), [Qwen3.8](https://huggingface.co/Qwen/Qwen3.8-27B), [Google Gemma](https://huggingface.co/google/gemma-4-26B-A4B-it), [Ai2 Olmo](https://huggingface.co/allenai/Olmo-3-32B-Think), [NVIDIA Nemotron](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16), [inclusionAI Ling](https://huggingface.co/inclusionAI/Ling-3.0-flash-VL), [Liquid AI](https://huggingface.co/LiquidAI/LFM2.5-2.6B), [Nex AGI](https://huggingface.co/nex-agi/Nex-N2.5-mini) and [Thinking Machines](https://thinkingmachines.ai/model-card/inkling-small/). A family source does not certify that a derivative checkpoint is identical to the upstream release. An unverified alias is not classified from its spelling alone.
