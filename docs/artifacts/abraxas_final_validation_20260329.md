# Abraxas Final Validation Report — 2026-03-29

## Scope
- Validation-only pass; no subsystem expansion.
- Real local case evaluation with bounded deterministic extraction.

## Canonical artifacts
- Primary JSON artifact (full detail): `artifacts_seal/abraxas_validation/20260329T173520Z.final_validation.json`
- Companion markdown: `artifacts_seal/abraxas_validation/20260329T173520Z.final_validation.md`

## Case set
- CASE-01-seal-forecast-clean
- CASE-02-seal-shadow-edge
- CASE-03-operator-missing-run-context
- CASE-04-ledger-only-daily-run

## Cross-case metrics
- valid_run_binding: 50.0%
- valid_ledger_bridge: 0.0%
- detector_ready_context: 50.0%
- >=2_usable_detector_families: 50.0%
- meaningful_fusion: 50.0%
- usable_synthesis: 0.0%
- degraded_or_not_computable: 100.0%

## Final verdict
- `NEEDS_ONE_MORE_CORRECTIVE_PASS`

## Next corrective target
- Restore pipeline final-status context for bound runs so synthesis does not collapse to `NOT_COMPUTABLE` when detector/fusion surfaces are already successful.

## Provenance
- source: `operator_console.final_validation_pass`
- evaluation timestamp: `2026-03-29T17:35:20Z`
- rules: real-local-only, bounded deterministic extraction, thresholded verdict logic.
