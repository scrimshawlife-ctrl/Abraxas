# Abraxas Calibration Diff Report — 2026-03-29 (Post-Binding Restoration)

## Case reuse
Reused the same case IDs from the prior calibration pass:
1. `CASE-01-seal-forecast-clean`
2. `CASE-02-seal-shadow-edge`
3. `CASE-03-operator-missing-run-context`
4. `CASE-04-ledger-only-daily-run`

Deviation:
- Prior per-case JSON artifact was not available locally during this pass.
- Before-state values were approximated from the committed calibration report (`docs/artifacts/abraxas_calibration_report_20260329.md`), which recorded flat NOT_COMPUTABLE behavior across cases.

## Before vs after metrics
- Run binding valid (`BOUND|PARTIAL_BOUND`): **0.0% → 100.0%**
- Ledger linked (`LINKED|PARTIAL_LINKED`): **0.0% → 25.0%**
- Detector usable (non-NOT_COMPUTABLE): **0.0% → 0.0%**
- Fusion meaningful: **0.0% → 0.0%**
- Synthesis usable: **0.0% → 0.0%**

## What improved
- Operator-visible run binding moved from missing to present (primarily `PARTIAL_BOUND`) across all reused cases.
- Flat not-computable degradation now carries explicit subcodes, improving causal specificity for triage.
- Ledger bridge progressed to partial linkage in the ledger-backed daily-run case.

## What remained unchanged
- Detector families remain NOT_COMPUTABLE for all cases.
- Fusion remains degraded due upstream detector non-computability.
- Synthesis remains NOT_COMPUTABLE for the same upstream reasons.

## Dominant remaining bottleneck
- **NC_MISSING_REQUIRED_CONTEXT**

## System state
- **heavily_degraded** (binding improved, but detector/fusion/synthesis usability has not yet moved)

## Recommended next upgrade target
- Restore validator outputs + correlation-pointer projection for partially bound runs so detector input prerequisites become computable.

## Generated diff artifacts
- `artifacts_seal/abraxas_calibration/20260329T162218Z.calibration_diff.json`
- `artifacts_seal/abraxas_calibration/20260329T162218Z.calibration_diff.md`
