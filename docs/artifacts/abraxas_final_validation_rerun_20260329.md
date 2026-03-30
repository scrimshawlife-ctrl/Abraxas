# Abraxas Final Validation Re-Run — 2026-03-29

## Artifact References
- Primary JSON artifact: `artifacts_seal/abraxas_validation/20260329T180715Z.final_validation_rerun.json`
- Companion markdown: `artifacts_seal/abraxas_validation/20260329T180715Z.final_validation_rerun.md`
- Prior baseline: `artifacts_seal/abraxas_validation/20260329T173520Z.final_validation.json`

## Case Reuse + Deviations
- Reused case IDs: `CASE-01-seal-forecast-clean`, `CASE-02-seal-shadow-edge`, `CASE-03-operator-missing-run-context`, `CASE-04-ledger-only-daily-run`.
- Deviations were explicit and bounded:
  - Case 02 remained a same-run closest equivalent because no distinct operator-visible shadow run exists.
  - Case 04 remained a query-edge closest equivalent because ledger-only daily run IDs are still not bindable through current operator run surfaces.

## Cross-Case Metrics
- percent_pipeline_final_state_resolved: **0.0%**
- percent_synthesis_ready_true: **0.0%**
- percent_usable_synthesis_output: **0.0%**
- percent_cases_degraded_or_not_computable: **100.0%**

## Delta vs Prior Validation
- delta_synthesis_usefulness_percent: **0.0**
- delta_degraded_rate_percent: **0.0**

## Final Verdict
**STILL_HEAVILY_DEGRADED**

## Next Corrective Target
- Restore operator run binding + pipeline envelope linkage so `pipeline_final_state` resolves before synthesis evaluation.

## Provenance
- source: `operator_console.final_validation_rerun.v1`
- timestamp: `2026-03-29T18:07:15Z`
