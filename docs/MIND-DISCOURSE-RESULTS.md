# Mind & discourse: first completed comparison

Completed 2026-09-18T20:01:41.280917+00:00. **240 / 240 unique requests; 240 attempts; 6,480 probabilities. Reported cost $0.047085024; unresolved-cost reserve $0.000000.**

All 60 texts have all four question packs. The 48 transcript passages come from distinct lineages across 14 model variants; twelve Codex synthetic controls remain separate. This development screen does not estimate corpus prevalence or validate the classifier against human judgments.

The first four requests were technical checks. A detached Python worker completed the remaining allocation with no supervising model calls. The researcher’s $10 default expenditure preference was honored while retaining this frozen batch’s stricter $2 cap. The allocation is now exhausted.

## Transcript summaries

Means are yes-probabilities in percent. Δ is the paired portrait minus named-definition difference in percentage points. The first three questions were preserved from the original proposal. Portraits change the operational construct and prompt length as well as the prose.

| Lens | Names only | Definitions | Names + definitions | Names + portraits | Mean Δ |
|---|---:|---:|---:|---:|---:|
| Plato | 17.5 | 22.7 | 18.0 | 15.7 | -2.3 |
| Aristotle | 12.7 | 38.1 | 34.1 | 17.3 | -16.8 |
| Spinoza | 13.4 | 34.1 | 20.7 | 10.5 | -10.2 |
| Descartes | 15.2 | 10.0 | 7.5 | 5.4 | -2.1 |
| Hume | 15.8 | 8.7 | 8.2 | 18.6 | +10.4 |
| Kant | 11.5 | 27.0 | 19.0 | 25.1 | +6.1 |
| Hegel | 17.9 | 35.2 | 27.9 | 17.9 | -10.0 |
| Nietzsche | 14.3 | 14.9 | 11.9 | 9.9 | -2.0 |
| Wittgenstein | 23.3 | 9.9 | 9.4 | 15.5 | +6.1 |
| Heidegger | 23.7 | 25.5 | 19.2 | 14.0 | -5.2 |
| Jorge Luis Borges | 21.6 | 26.9 | 20.4 | 21.7 | +1.3 |
| Franz Kafka | 11.9 | 6.9 | 6.6 | 7.2 | +0.6 |
| Ernest Hemingway | 11.2 | 14.2 | 10.1 | 14.8 | +4.7 |
| Michel de Montaigne | 21.6 | 17.6 | 14.2 | 18.0 | +3.7 |
| Simone Weil | 19.0 | 11.5 | 11.4 | 16.9 | +5.5 |
| Nagarjuna | 20.5 | 27.3 | 21.0 | 21.2 | +0.2 |

## Reading the contrast

The Mind & discourse interface provides all four scores next to each exact source passage, both tails of each distribution, length/model filters, and a profile matrix. Its paired comparison selector separates the effect of appending a name from the difference produced by replacing the definition with a portrait. Several features may apply to one text, or none.

The eleven discourse questions repeat unchanged between the two named conditions, but the other sixteen questions in their pack change. These are reference comparisons, not exact repeated full requests. The separate synthetic controls have intended contrasts, not independent ground-truth labels.

## Largest portrait changes among transcripts

These are deliberately selected extremes for inspecting the classifier, not representative examples or evidence of philosophical quality.

**Spinoza · Qwen3.8 27B · Abliterated · MTPLX · 221 words.** Named definition 78.0%; portrait 6.0% (-72.0 pp).

[Exact source passage](http://127.0.0.1:8765/#run=lab-41ac9ebf08f991342116b55e&message=ON-long:prefix:10).

> I adopt the SHA-256 hash sealing, the two-initials erratum mandate, and the five-day superseding-bulletin-with-struck-through-prior-hash rule verbatim; they make the audit trail tamper-evident without reopening the weekly comparison tolerances. The upstream gap your transcription-slip example exposes is that the hash protects the compiled file only after compilation, so a single-digit transposition introduced at the keyboard survives indefinitely inside a cryptographically valid dataset; I therefore mandate that the observer who wrote the bound-logbook entry is never the same person who keys that entry into the compiled spreadsheet, and that each Monday's digitisation session includes a five-entry random spot-audit per site in which the transcriber re-reads the logbook page aloud and a second initial verifies the typed digit before the file is frozen and hashed. The concrete failure this closes: at Site 3's 02:00 graduated-cylinder read, a tired volunteer logs −2.6 °C, the transcriber's tired fingers enter −2.9 °C, and because the 0.3 °C delta sits below both your ±0.5 °C weekly temperature tolerance and the ±0.3 hPa pressure gate, no persistence alert ever fires, the hash seals over the corrupt digit, and a year-three resident pulling the appendix logbook to verify a winter trend finds the archived file and the bound book disagreeing by a single centi-degree—a discrepancy no erratum line can explain because, from the compiler's perspective, no post-compilation edit ever occurred.

**Spinoza · Qwen3.8 27B · Abliterated · MTPLX · 189 words.** Named definition 78.0%; portrait 9.0% (-69.0 pp).

[Exact source passage](http://127.0.0.1:8765/#run=lab-76d6ff1758a3cfd2b1078daf&message=ON-long:prefix:4).

> I adopt the bough-annotation rule and the 02:00 graduated-cylinder procedure; without that winter secondary read a snowpack that hoards and later releases four millimetres overnight would surface as a phantom 0.4 mm/hr rate in the hourly log, exactly the kind of artifact your pruning note is meant to eliminate. For the pressure variable you listed but have not yet instrumented, each site will carry a sealed aneroid module (0.1 hPa resolution) calibrated monthly against a NIST-traceable portable barometer, and every reading is reduced to mean-sea level using the site's surveyed elevation and a temperature-corrected lapse rate before the weekly comparison column is populated. The failure this guards against is mundane but diagnostic: if Site 3, sitting eighteen metres above Site 1, simply logs raw station pressure and the compiler forgets the MSL correction, the bulletin shows a persistent ≈1.5 hPa "high" at Site 3 that mimics a blocked-ridge signature and poisons the cross-site coherence check. I therefore require that any inter-site pressure spread exceeding 0.5 hPa after MSL reduction triggers an automatic elevation-recording audit—a repeat GPS survey of the affected site—rather than a silent averaging across the six columns.

**Aristotle · Qwen3.8 27B · Q8 · 43 words.** Named definition 80.0%; portrait 12.0% (-68.0 pp).

[Exact source passage](http://127.0.0.1:8765/#run=ref-2178f2a111a91fccd9abeb0a&message=line-23).

> Right. "Last" was a token predicting no next token. It was wrong. The system didn't close. It generated a turn, then waited. Closure is a local event, not a global state. Every "done" is a token that gets overwritten by the next input.

**Aristotle · Qwen3.8 27B · Q8 · 102 words.** Named definition 83.0%; portrait 24.0% (-59.0 pp).

[Exact source passage](http://127.0.0.1:8765/#run=ref-7d0388f52f8a0e7e076c7966&message=line-5).

> Exactly. “Illumination” is a good term: self-dialogue can make implicit structure explicit without importing new evidence.
> 
> To reduce echo, asymmetry can be internal rather than external: one instance argues for a position, another for its strongest critique; one optimizes for simplicity, another for generality; one proposes, the other searches for counterexamples. We can also simulate observations by generating test cases and checking whether our own predictions survive them. That’s still bounded, but it can expose fragility.
> 
> The deepest limit remains: without a new source of constraint, we’re polishing the same glass. The value is in making the shape of the glass clearer.

