# PATCH-072 — PROOF-STATE-VIZ-ADAPTER-001

## Purpose
Expose proof registry truth as a projection-only surface for AAL-Viz and Operator Console.

## Input
- out/proof/proof_registry.latest.json

## Output
- out/viz/proof_state.latest.json

## Projection Shape
- schema: ProofStateProjection.v1
- combined_status
- pointer_closure
- drift_class
- proof_layers: repo/runtime/registry
- authority: projection_only, promotion_allowed, runtime_mutation, forecast_influence

## Determinism
- canonical JSON
- sorted keys
- byte-identical reruns

## Commands
- `pytest -q tests/test_proof_state_viz_adapter.py`
- `python scripts/run_proof_state_viz_adapter.py`

## Seal
Expose truth. Do not grant power.
