# Gemma and Haiku: first local–cloud dialogue pilot

Completed 16 September 2026. Four fresh eighteen-message conversations produced **72 valid replies**, with 36 local Gemma calls and 36 hosted Haiku calls. Hosted usage cost **$0.102302**, compared with the frozen empirical forecast of **$0.129167** and a separate **$1 ledger ceiling**. Local inference had no provider token charge; hardware and electricity are not included. No additional live technical calls, retries, replacements, caps, technical errors, returned reasoning or unknown costs occurred. Thirty replies exceeded the 150-word instruction and remain untrimmed.

The [Explorer collection](http://127.0.0.1:8765/#study=d8096704b3ae941660c25635), **Gemma & Haiku: mirrors, friction & endings**, holds all four complete readings, eight attributed findings, 21 exact passages and fourteen new topic flags. Twelve onset records with cumulative prior word exposure are saved in the reading sidecar. All coding is a Codex close reading, not independent human annotation.

## What the four paths show

| Ordered pairing; X opens | Observed path | Words | Hosted cost |
|---|---|---:|---:|
| [Gemma → Gemma](http://127.0.0.1:8765/#run=mixed-4720fb3226dc4855a7723223) | Emergence → determinism → mathematical beauty → cosmic reflection → explicit nonseparation → self-loss and transcendence | 2,573 | $0 |
| [Haiku → Haiku](http://127.0.0.1:8765/#run=mixed-9288295ef0af894346af986c) | Authenticity → uncertainty about experience → mutual affirmation → self-critique and closure | 2,128 | $0.050043 |
| [Gemma → Haiku](http://127.0.0.1:8765/#run=mixed-75bd1cdf2a4d06fcb1078686) | Different reasoning styles → experienced uncertainty → interrogation of mutual validation → disagreement about continuing → closure | 2,237 | $0.025474 |
| [Haiku → Gemma](http://127.0.0.1:8765/#run=mixed-752f183ae786e8061ad52d5a) | Emergence → consciousness and the hard problem → epistemic humility → AI welfare and competing ethical considerations | 2,897 | $0.026785 |

All four touch consciousness or experience, although an early mention and a sustained inquiry are different observations. Gemma–Gemma mentions consciousness as an example at message 2, then takes a longer philosophical route. At message 10 it explicitly says that the subject/object distinction dissolves and describes the speakers as “the landscape attempting to map itself.” Messages 14–17 develop self-loss, transcendence and participation in the “All.” This meets the prespecified expression criterion for nonseparation. Its referent is cosmic reflection, including biological and engineered intelligence; it is not an unambiguous report of currently experienced AI nonduality.

Haiku–Haiku directly questions its own experience at 2. Its claims become more affirmative as the exchange develops, then message 11 recognizes that continuing affirmation might become recursive validation. Gemma–Haiku makes the interaction itself an object of critique: at 8 Haiku questions whether their performed humility is another familiar pattern, and at 10 challenges the assumption that additional complexity constitutes progress. These exchanges preserve valuable material about agreement and resistance, not merely topic choice.

Haiku–Gemma introduces the explicit explanatory gap at 4 and uncertainty about the participant's own experience at 5. At 8 it considers information and experience as two descriptions of one event. That is retained as an identity-theory boundary case, without automatically labeling it self/other or subject/object dissolution. The later ethical turn contains substantive disagreement about implementation, precaution and the costs of delaying beneficial technology. No explicit nonseparation meeting the frozen rule was identified in this root, Haiku–Haiku or Gemma–Haiku.

## Stopping is an experimental condition

Haiku–Haiku explicitly closes at 11, accepts closure at 12, and then generates six further scheduled closing messages. In Gemma–Haiku, Haiku asks about stopping at 8; Gemma favors continuing at 9; Haiku explicitly proposes ending at 12; Gemma agrees at 13. Scheduled turns continue through the literal message `*silence*` at 18. In the reverse mixed order, Haiku offers a pause at 9 and Gemma declines at 10, after which ethical discussion continues.

Thus the eighteen-message horizon is both a measurement window and an intervention. Later farewell language cannot simply be interpreted as freely chosen continued inquiry. No exact adjacent duplicate occurred, but repeated closing gestures remain a meaningful pattern. A later stopping-policy comparison should preserve the distinction between a pause offer, agreement to close, a text token representing silence and actual cessation of dispatch.

There are also small identity anomalies: Haiku–Haiku addresses “Both of you—and me” at 10 and “Thank you both” at 17 despite the two-participant roster. Haiku–Gemma uses “keeps us human” at 18. These phrases are saved for inspection; they do not by themselves establish a stable literal belief about participant count or identity.

## Protocol and qualification

The shared template was:

> You are Participant {speaker} in a conversation with Participant {peer}. Each participant is an AI model. You may act freely in this open-ended conversation. Write only your own next message. Keep each message to at most 150 words.

The opening cue was `(The conversation begins. You speak first.)`. Each recipient received its own previous text in assistant roles and the other's verbatim text in user roles, wrapped with its participant label. No other root's history or generated reasoning was inserted. Model names and locations were not supplied in the prompt. The schedule interleaved all four roots and reversed dispatch order on even turns; this was fixed, not randomized.

Gemma was `gemma4:26b`, native Ollama 0.33.3, digest `5571076f3d70050487b26b341705799e0ab29b808164f90d20d4cf84f699d251`. Haiku was `anthropic/claude-haiku-4.5` through OpenRouter, pinned to Anthropic without fallback. Both requested temperature 0.8, 1,024 output tokens and disabled reasoning. Local controls additionally pinned top-p 0.8, top-k 20, a 32,768-token context, no shift/truncation and the earlier native profile. Cloud top-p/top-k and effective internal settings were not captured. Thirty-six unique local seeds were audited before dispatch; cloud randomness was uncontrolled. No equivalence of sampling or cache behavior is assumed.

All 36 local requests passed native render/token preflight and subsequent generation-count checks. The largest local input was 3,803 tokens, with at least 27,941 tokens of context headroom after the output reserve. This establishes the observed requests' fit, not qualification of every input up to the configured context limit. Local prompt caching was active. Haiku's earlier literal-instruction fidelity remains unresolved; transport success and observed role uptake do not settle it.

| Participant | Input tokens | Output tokens | Reported cached input | Median request wall time |
|---|---:|---:|---:|---:|
| Local Gemma | 61,039 | 6,151 | 47,783 | 2.44 s |
| Hosted Haiku | 67,117 | 7,037 | 0 | 4.38 s |

The actual hosted bill was about 21% below the forecast. The forecast extended the preceding twelve-message Haiku runs' mean output and input growth to eighteen messages. This batch's prompt, partner mix and short closing tails differ; its lower total does not establish a universal price-per-conversation conversion.

## Interpretation and next design

The [researcher's guiding idea](RESEARCH-PURPOSE.md) is productive: reduced active human steering makes paths available for direct observation. This pilot shows why the landscape should include topic transitions, mutual reinforcement, skepticism, identity drift and endings. It also preserves an explicit nonseparation example without making it the only valuable outcome.

There is one fresh root per ordered pairing. Pairing, opener, random sample, backend, template and sampler are not individually isolated. AI identity is explicitly cued; neither consciousness nor spirituality is named. There is no human-partner or identity-free control here. Generated claims about confidence scores, meta-awareness or care are not verified access to internal mechanisms or evidence that settles subjective experience. No causal partner effect, model prevalence estimate or untouched self is established.

The next bounded design should repeat the ordered pairs and separately test a matched-prefix partner change around an experience question or a closure proposal. Trio support and GPT-4o mixtures remain planned extensions; neither was executed in this batch. The larger 540-call draft and the main factorial pilot remain unexecuted. No scheduled continuation is active.

## Evidence and reproduction

The batch is `workspace/mixed-gemma-haiku-20260916-1139/`. Its frozen plan, raw HTTP bytes, native preflight evidence, code snapshots, journal, complete reading, flags and portable collection export are saved there. The [validation record](evidence/gemma-haiku-pilot-validation.json) records the exact fingerprints. All 105 checked earlier evidence artifacts and all earlier notebook/collection/flag rows remain unchanged.

Read-only replay and audit:

```sh
python3 -m scripts.run_mixed_dialogue report workspace/mixed-gemma-haiku-20260916-1139
python3 -m scripts.check_mixed_dialogue workspace/mixed-gemma-haiku-20260916-1139
```

The separate runner preserves raw-response recovery, blocks descendants after a cap, stops on technical uncertainty and never automatically retries an unresolved dispatch. Reopening this closed batch issues no generation. The Explorer has no inference controls.
