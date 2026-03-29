# Abraxas Final Validation — Post run_id Propagation Repair (2026-03-29)

## Artifact References
- Primary JSON artifact: `artifacts_seal/abraxas_validation/20260329T183733Z.final_validation_post_run_id_propagation.json`
- Companion markdown: `artifacts_seal/abraxas_validation/20260329T183733Z.final_validation_post_run_id_propagation.md`
- Prior rerun baseline: `artifacts_seal/abraxas_validation/20260329T182252Z.final_validation_post_binding_envelope.json`

## Case Reuse
- `CASE-01-seal-forecast-clean`
- `CASE-02-seal-shadow-edge`
- `CASE-03-operator-missing-run-context`
- `CASE-04-ledger-only-daily-run`

## Deviations
- Case 02 remains closest equivalent: no distinct shadow run is operator-visible.
- Case 04 remains closest equivalent: ledger-only daily run remains query-edge in current operator surfaces.

## Cross-Case Metrics
- percent_operator_bound_runs: **50.0%**
- percent_invocation_run_id_present: **50.0%**
- percent_envelope_run_id_present: **0.0%**
- percent_exact_run_id_matches: **0.0%**
- percent_final_state_derivable_cases: **0.0%**
- percent_final_state_bindable_cases: **0.0%**
- percent_synthesis_ready_cases: **0.0%**
- percent_usable_synthesis_outputs: **0.0%**
- percent_degraded_or_not_computable_cases: **100.0%**

## Deltas vs Prior Rerun
- delta_operator_bound_runs: **0.0**
- delta_invocation_run_id_present: **+50.0**
- delta_envelope_run_id_present: **0.0**
- delta_exact_run_id_matches: **0.0**
- delta_final_state_derivable_cases: **0.0**
- delta_final_state_bindable_cases: **0.0**
- delta_synthesis_ready_cases: **0.0**
- delta_usable_synthesis_outputs: **0.0**
- delta_degraded_or_not_computable_cases: **0.0**

## Final Verdict
**STILL_HEAVILY_DEGRADED**

## Next Corrective Target
- Persist propagated invocation `run_id` into emitted pipeline envelope artifacts so operator envelope linkage can exact-match before synthesis.

## Provenance
- source: `operator_console.final_validation_post_run_id_propagation.v1`
- timestamp: `2026-03-29T18:37:33Z`
