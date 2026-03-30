# Abraxas Final Validation — Post Binding/Envelope Repair (2026-03-29)

## Artifact References
- Primary JSON artifact: `artifacts_seal/abraxas_validation/20260329T182252Z.final_validation_post_binding_envelope.json`
- Companion markdown: `artifacts_seal/abraxas_validation/20260329T182252Z.final_validation_post_binding_envelope.md`
- Prior rerun baseline: `artifacts_seal/abraxas_validation/20260329T180715Z.final_validation_rerun.json`

## Case Reuse
- `CASE-01-seal-forecast-clean`
- `CASE-02-seal-shadow-edge`
- `CASE-03-operator-missing-run-context`
- `CASE-04-ledger-only-daily-run`

## Deviations
- Case 02 remains a closest equivalent because a distinct shadow run is still not operator-visible.
- Case 04 remains a closest equivalent because ledger-only daily run IDs are still not bindable via current operator run surfaces.

## Cross-Case Metrics
- percent_operator_bound_runs: **50.0%**
- percent_envelope_linked_cases: **0.0%**
- percent_final_state_derivable_cases: **0.0%**
- percent_synthesis_ready_cases: **0.0%**
- percent_usable_synthesis_outputs: **0.0%**
- percent_degraded_or_not_computable_cases: **100.0%**

## Deltas vs Prior Rerun
- delta_operator_bound_runs: **+50.0**
- delta_envelope_linked_cases: **0.0**
- delta_final_state_derivable_cases: **0.0**
- delta_synthesis_ready_cases: **0.0**
- delta_usable_synthesis_outputs: **0.0**
- delta_degraded_or_not_computable_cases: **0.0**

## Final Verdict
**STILL_HEAVILY_DEGRADED**

## Next Corrective Target
- Restore deterministic operator invocation `run_id` propagation into pipeline envelope so linkage can bind before synthesis.

## Provenance
- source: `operator_console.final_validation_post_binding_envelope.v1`
- timestamp: `2026-03-29T18:22:52Z`
