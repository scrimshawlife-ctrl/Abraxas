# Abraxas Operational Calibration Report — 2026-03-29

## Scope
Calibration-only pass against real local cases; no subsystem expansion.

## Real cases used
1. `CASE-01-seal-forecast-clean` (artifacts_seal seal result/view/trend packs)
2. `CASE-02-seal-shadow-edge` (shadow lane task from seal result pack)
3. `CASE-03-operator-missing-run-context` (`selected_run_id=None` runtime view)
4. `CASE-04-ledger-only-daily-run` (`DAILY-2026-01-01-001` from out/ledger with no operator artifact binding)

> Note: only one full artifact-pack run (`seal`) is present in operator-visible run surfaces. The remaining cases are real but context-limited.

## Stack output capture summary
Across all four cases in current repository state:
- `selected_run_id` resolved to `None` in `build_view_state(...)`
- detector families: `NOT_COMPUTABLE`
- fusion: `NOT_COMPUTABLE`
- synthesis: `NOT_COMPUTABLE`
- synthesis next step: `Select run to compute synthesis output.`

## Per-case calibration notes
- **CASE-01**
  - Useful: seal results/trend artifacts are coherent (`forecast ok`, zero trend errors/skips).
  - Weak: operator stack cannot bind this run into run-scoped detector/synthesis compute surfaces.
- **CASE-02**
  - Useful: shadow lane (`shadow:sei`) edge behavior is observable in artifacts.
  - Weak: same run-binding gap prevents differentiated detector/fusion output.
- **CASE-03**
  - Useful: guardrails correctly degrade to explicit `NOT_COMPUTABLE` without fabricated success.
  - Weak: coarse not-computable bucket masks missing-context subtypes.
- **CASE-04**
  - Useful: confirms ledger holds real daily runs.
  - Weak: ledger runs are not currently bridged into operator run artifact surfaces.

## Cross-case summary
- **Strongest subsystem**: results/trend artifact generation coherence.
- **Weakest subsystem**: operator run binding to run-scoped artifact/validator surfaces.
- **Most reliable detector family**: not assessable under missing run binding.
- **Least useful detector family**: all equal under current `NOT_COMPUTABLE` collapse.
- **Routing quality**: present but not meaningfully validated without bound run contexts.
- **Synthesis quality**: correct guardrail behavior (`NOT_COMPUTABLE`) but low discriminative calibration value in current state.

## Top 3 upgrade targets (evidence-grounded)
1. Restore operator-visible run artifact + validator pairs for recent real runs (`*.artifact.json` + validator outputs).
2. Add bridge/ingestion from existing ledger daily runs into operator run surfaces.
3. Add synthesis not-computable subcodes to distinguish data absence vs compute failure.

## Generated calibration artifacts
- `artifacts_seal/abraxas_calibration/20260329T064212Z.calibration_report.json`
- `artifacts_seal/abraxas_calibration/20260329T064212Z.calibration_report.md`
