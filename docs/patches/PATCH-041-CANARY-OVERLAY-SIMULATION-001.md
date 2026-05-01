# PATCH-041 — CANARY-OVERLAY-SIMULATION-001

## purpose
Simulation-only counterfactual analysis for canary overlays using existing forecast and score artifacts. No overlay application is performed.

## authority boundary
- No runtime overlay application
- No baseline mutation
- No runtime config writes
- No promotion
- No execution/scheduler operations
- No external API calls

## simulation method
For each overlay, match forecasts by `source_key` against `forecast.signal_sources` and `forecast.source_families`.
Compute:
- `baseline_error = mean(brier_score)`
- `simulated_error = mean(brier_score * (1 + simulated_delta))`
- `delta_error = simulated_error - baseline_error`

Outputs are rounded to 6 decimals and sorted by `(source_key, overlay_id)`.

## limitations
Current simulation does not evaluate probability quality directly; it uses coverage-weighted and error-weighted counterfactual scoring only.

## interpretation rules
- `delta_error < 0` => `improved`
- `delta_error > 0` => `worsened`
- `delta_error == 0` => `neutral`
- no matched forecasts or no usable scores => `not_computable`

## next patch
PATCH-042 CANARY-REVIEW-GATE-001
