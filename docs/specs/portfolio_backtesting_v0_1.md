# Portfolio Backtesting v0.1

## Purpose

Single-case wins are fragile. Portfolio backtesting ties candidate evaluation to **case sets** defined by horizon, segment, narrative, and selectors. This forces improvement to generalize across families of cases instead of one-off wins.

## Why Portfolios Exist

- **Anti-overfitting**: A candidate must improve *portfolio aggregates*, not isolated hits.
- **Deterministic gates**: Score deltas are computed with a consistent shape across portfolios.
- **Promotion integrity**: No regressions in protected portfolios.

## Portfolio Definitions

Portfolios live at:

```
data/backtests/portfolios/portfolios_v0_1.yaml
```

Each portfolio declares:
- `horizons` (e.g., H72H, H30D, H1Y)
- `segments` (e.g., core)
- `narratives` (e.g., N1_primary, N2_counter)
- `case_selectors` (e.g., trigger kind filters)
- `protected` (no-regress or high-importance)

## Candidate Target Binding

Each `MetricCandidate` carries an explicit `target`:

```
target:
  portfolios: ["short_term_core"]
  horizons: ["H72H","H30D"]
  score_metrics: ["brier","calibration_error"]
  improvement_thresholds: {"brier": -0.003}
  no_regress_portfolios: ["long_horizon_integrity"]
  mechanism: "..."
```

### MW / AAlmanac / Integrity

- **AAlmanac term candidates** target short-term portfolios and brier/calibration.
- **MW synthetic saturation + integrity** target long-horizon integrity with coverage/CRPS/trend metrics.
- **SSI dampening param tweaks** require stronger coverage gains and enforce no-regress on short-term core.

## Score Aggregation (Normalized Shape)

Portfolio scoring uses a single normalized shape:

```
{
  "brier_avg": float|None,
  "log_avg": float|None,
  "calibration_error": float|None,
  "coverage_rate": float|None,
  "trend_acc": float|None,
  "crps_avg": float|None,
  "abstain_rate": float
}
```

If a metric is missing, it is `None` (never inferred).

## Promotion Gate Implications

Promotion requires:
- `sandbox_result.pass_gate == true`
- All target portfolios **PASS**
- No-regress portfolios **PASS**
- Stabilization window satisfied
- Rent manifest draft present (metrics/operators)

This makes “new metrics improve accuracy” measurable in portfolio form.

