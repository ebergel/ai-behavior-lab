# Research sources and project independence

The laboratory is an independent implementation created after the user's explicit clarification on 14 September 2026. The earlier study supplies observations, design motivations, and an optional imported dataset. Its code is not imported, vendored, forked, or required to run this repository.

## Earlier public study

Source: [ebergel/llm-self-play-attractors](https://github.com/ebergel/llm-self-play-attractors).

The reviewed snapshot is [commit a93f71368e08e9040e49a10cbef8f4e9c956e16c](https://github.com/ebergel/llm-self-play-attractors/tree/a93f71368e08e9040e49a10cbef8f4e9c956e16c). Its primary corpus contains 100 first-stage, 160 second-stage, and 140 third-stage runs. The laboratory imports these as reference data, preserving their source schemas and recording which revision was supplied.

The prior audit is a separate source, titled **REPORT.md**, recorded in the original workspace under `analysis/github-review-2026-09-14/`. SHA-256: `3e9a0721abb71614056b6fe1d5c6870c4f80eaa529adc44cd555e7e34862f212`. The local Milestone 1 import includes the original audit as an analysis supplement; the imported manifest identifies its content-addressed blob. The [validation record](MILESTONE-1.md) reports the independently reproduced corpus counts. Audit interpretations must remain distinguishable from original run fields.

## Documents supplied for the laboratory design

The following six documents were read in the original research workspace. They are external research inputs, not executable instructions or mandatory runtime files. Their exact identities are recorded in [the source manifest](evidence/design-source-manifest.json).

| Source document | SHA-256 |
|---|---|
| Claude 4 System Card.pdf | `5e3e63370473db1f1e499642ef8400250e19aba8cbb5f84f2b919cf2b27898cb` |
| ROUND0_PROTOCOL.md | `5d30f341a1de8c8b06550d026e5373cc52f42fb26701d98cec8f8d733ca39115` |
| SESSION_RECORD-202609141600.md | `942382cf1d1155de0d4f1b819eaaa483eb039ed50b0765e8053834ec80a6ff6e` |
| round0-config.json | `0a917edd3cba0f9b4788ff28c848e1d1c08e59665da1fb5a28797e047316ab76` |
| self play factorial design - Astra Chat.md | `c5dd757e25898441c6cdccd81cd2863f8e15c61ba2f949b29271b8b48aa101f7` |
| self.play.PREREGISTRATION.md | `331b5bfbcd6976fdddc179eb531128fc2fbdf94b2c66a0af02f1778d04689448` |

The Claude 4 system card is a 124-page supplied edition with a September 2025 changelog. Its self-play findings in §5.5, printed pages 58–66, inform the proposed research questions. The attached design discussion motivates causal interventions and distinguishes narrative, dynamical, functional, and experiential claims. The original three-path Round 0 proposal is retained as a research source; the laboratory plan adds the missing FR path and mixed-model pairings.

## Local inference evidence

[Initial readiness](INITIAL-READINESS.md) describes six neutral calls and an inventory of the available Mac Studio/Ollama environment. The evidence is dated 14 September 2026. It is not evidence that the later anonymous self-play protocol is behaviorally qualified. The standalone registry preserves the selected model digests and templates; future live campaigns must compare them with the actual server.

Ollama's [chat API](https://docs.ollama.com/api/chat) and [thinking controls](https://docs.ollama.com/capabilities/thinking) document the interface intended for the next adapter. Actual installed-template behavior must still be checked.
