# TimesFM 2.5 Shadow lab (Path A)

Shadow-only local adapter and DE-LU Energy Charts smoke. **Not Canon. Not Forecast. No TimesFM 3.0.**

Operator stamp: Danny human-yes 2026-09-06 PT.

## Locks

| Field | Value |
| --- | --- |
| Model | `google/timesfm-2.5-200m-transformers` |
| License | Apache-2.0 |
| `hf_revision` | `5a9806b9b291fad9233b5249d88263f1846304d3` |
| Lane | SHADOW |
| Influence | NONE |
| `valid_for_forecast` | `false` (always) |
| Semantics | `generative_prior_not_objective_probability` |
| Evidence | local JSON under `out/timesfm_shadow/` only |
| Rune | `RUNE.TIMESFM_FORECAST` is a code-only stub string |

Mean and quantile series are a generative prior. This slice never writes `BIAS_DELTA` `objective_probability`.

## Unit tests (CI)

Weights are not downloaded in CI.

```bash
PYTHONPATH=. pytest -q tests/test_timesfm_shadow_lab.py
make test-timesfm-shadow
```

## Optional CPU smoke

Install optional deps once, then let Hugging Face cache the pinned 2.5 revision. CPU-only. This command is **not** a CI gate.

```bash
pip install -e '.[timesfm]'
PYTHONPATH=. python -m abraxas.sources.timesfm_shadow \
  --out-dir out/timesfm_shadow \
  --horizon 24 \
  --seed 20260906 \
  --hf-revision 5a9806b9b291fad9233b5249d88263f1846304d3
```

The smoke path:

1. `GET https://api.energy-charts.info/price?bzn=DE-LU` via `HTTPSnapshotAdapter` (cache fallback).
2. Parse the `unix_seconds` / `price` window.
3. Run zero-shot TimesFM 2.5 on CPU with the pinned revision.
4. Write `TimesFMShadowForecast.v0` under `out/timesfm_shadow/` and assert the locks.

First run downloads weights once. Later runs reuse the local HF cache. No spend APIs. No Notion Receipt writes.

## T1-T2 Shadow Notion projection (no Notion writes)

Local projector only. It reads a `TimesFMShadowForecast.v0` packet and writes
`timesfm_shadow_notion_projection.v0`. Forecast authority does not change.
`valid_for_forecast` stays `false`. History timestamps and values are not copied.

Schema: [`schemas/timesfm_shadow_notion_projection.v0.json`](../../schemas/timesfm_shadow_notion_projection.v0.json)

```bash
PYTHONPATH=. python -m abraxas.sources.timesfm_shadow_projection \
  --packet tests/fixtures/timesfm_shadow/timesfm_shadow_forecast.v0.golden.json \
  --out out/timesfm_shadow/timesfm_shadow_notion_projection.v0.json
PYTHONPATH=. pytest -q tests/test_timesfm_shadow_projection.py
```

T3 Notion database write is out of band (Boof).

## Hold

- No Canon mint.
- No Forecast lane.
- No TimesFM 3.0.
- No new bots.
- No phenomenology claims.
- Missing live-smoke receipts stay `partial` / `attestation_pending`.
