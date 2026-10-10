# Direction: a forecasting engine for slang and memes

Status date: 2026-10-10. This page states where Abraxas is going and what exists today. It claims nothing beyond the repository.

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
