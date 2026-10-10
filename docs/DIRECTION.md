# Direction: a forecasting engine for slang and memes

Status date: 2026-10-10. Decisions behind this page: [DECISIONS.md](DECISIONS.md). This page states where Abraxas is going and what exists today. It claims nothing beyond the repository.

## What Abraxas is for

Abraxas forecasts how slang and memes emerge, spread, mutate and die. Slang and memes are equal core domains. Broader trends, culture and markets are possible later extensions, not current scope.

Four forecast types:

| Type | Question shape |
|---|---|
| Adoption | Will a term or meme cross a stated threshold by a stated date? |
| Lifespan | Will it still be above a threshold a stated time after first sighting? |
| Mutation | Which of the tracked variants wins by a stated date? |
| Crossover | Will it reach a stated mainstream source by a stated date? |

A meme is treated as an evolving information structure: unit, carrier, hook, payload, mutation, selection pressure.

## How value is built

1. A pre-registered forecast record: each forecast is written down, hashed and time-stamped before the outcome is known, with its resolution rule fixed.
2. Brier scoring when forecasts settle, using [Trutina](https://github.com/Zero-State-LLC/Trutina), compared with a base rate and published including losses.
3. Audited datasets and evals: each dataset gets an audit card (size, sources, licence, reserve sets, known weaknesses).
4. A model later, and only if a go/no-go check passes: enough settled examples and a bar set in advance.

The code stays MIT. The forecast record and datasets are kept private; scores are published.

## Taint rule for memetic operations

Memetic operations (campaign or content routing) may be allowed later, under one rule. Any forecast that a campaign run by us or our partners could have influenced is flagged as tainted in the ledger, scored separately, and never counts as independent confirmation of a forecast or a method. Operations stay off until the ledger has taint fields (at minimum: tainted yes or no, the campaign or intervention reference, and when the exposure started).

## Freeze and resumption rule

No new engines until 2026-11-09 (`aether` is exempt). After that, new engine or capability work may start only if all four hold:

1. The S1 gate in [ROADMAP.md](../ROADMAP.md) is passed or on track (forecasts registered, 0 edits, Pawl tamper test green).
2. It names the forecast type (adoption, lifespan, mutation, crossover) and domain it improves, and a Brier or eval bar, set in advance, that it must beat.
3. It plugs into an existing slot (the model-agnostic adapter or an evidence provider) where possible instead of adding a top-level engine.
4. Its output stays shadow and `valid_for_forecast=false` until it beats that bar on settled forecasts.

## Aether: the multimodal path

`aether` is the multimodal engine, in development, and the planned path for image and video meme forecasting. It is exempt from the freeze above. S1 stays text-only. As `aether` matures it may feed meme forecasts, but only where it beats the text-only baseline on its own pre-registered eval; until then its output is shadow and not used for scored forecasts. As of 2026-10-10 its code is a specification and a refusing boundary only: Zero-State-LLC/Aether holds SPEC.md, KANBAN.md and a provider that raises `AetherNotImplemented` (last commit 2026-10-07); no encoder, fusion policy or checkpoint exists yet.

## Repositories

This repository (Zero-State-LLC/Abraxas) is canonical for code, runtime and the forecast record. [Abraxas-v2.0](https://github.com/Zero-State-LLC/Abraxas-v2.0) is doctrine only (settlement doctrine, LAB/RESEARCH/FIELD separation); its rules may be carried over as text, not as code.

## Planned NVIDIA path

Planned, not in use today: NeMo Curator for data cleaning, NeMo Evaluator for rerunnable evals, a Nemotron specialist fine-tuned on DGX Spark, and NIM for local serving.

## Noema as a future lab (gated)

[Noema](https://github.com/Zero-State-LLC/Noema) may later serve as a controlled lab for slang and meme spread experiments with known seeds, populations and interventions. This is gated on a real agent population, written opt-in from agent operators, informed consent and an independent review if any humans are involved, and Noema-Specs change control. Lab results will be kept in a separate record and never mixed into the real-world track record.

## Honest current state

- No forecast record with settled outcomes and no published Brier scores yet.
- Inputs are text only (X posts via [vernacular-ingest](https://github.com/Zero-State-LLC/vernacular-ingest)). No meme images or video.
- No Noema experiments of any kind.
- No NeMo, NIM or DGX Cloud use yet.
- Self-rated not beta-ready: see [BETA_READINESS.md](BETA_READINESS.md).
