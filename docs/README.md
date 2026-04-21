# Abraxas Documentation Index

Technical map of canonical, operational, and historical documentation surfaces.

This index is intentionally aligned with the root [README](../README.md) and uses the same maturity vocabulary:
**Implemented**, **Partial**, **Experimental**, **Planned**.

---

## Start Here

1. [../README.md](../README.md) — repository front door, quickstart, maturity boundaries.
2. [CANONICAL_RUNTIME.md](CANONICAL_RUNTIME.md) — canonical runtime proof spine.
3. [VALIDATION_AND_ATTESTATION.md](VALIDATION_AND_ATTESTATION.md) — validator and attestation surfaces.
4. [SUBSYSTEM_INVENTORY.md](SUBSYSTEM_INVENTORY.md) — subsystem maturity inventory.
5. [RELEASE_READINESS.md](RELEASE_READINESS.md) — release-readiness baseline and policy posture.

---

## Canon / Governance

- [CANONICAL_RUNTIME.md](CANONICAL_RUNTIME.md) — canonical runtime + proof lifecycle.
- [VALIDATION_AND_ATTESTATION.md](VALIDATION_AND_ATTESTATION.md) — validation/attestation boundary definitions.
- [SUBSYSTEM_INVENTORY.md](SUBSYSTEM_INVENTORY.md) — maturity status by subsystem.
- [RELEASE_READINESS.md](RELEASE_READINESS.md) — readiness model and release gate context.
- [ABRAXAS_KERNEL_CONTRACT.md](ABRAXAS_KERNEL_CONTRACT.md) — kernel-level contract framing.

---

## Architecture / System Maps

- [overlay_contract.md](overlay_contract.md) — overlay contract behavior.
- [specs/dual_lane_architecture.md](specs/dual_lane_architecture.md) — shadow vs forecast-active lane architecture.
- [specs/simulation_architecture.md](specs/simulation_architecture.md) — simulation architecture.
- [specs/simulation_mapping_layer.md](specs/simulation_mapping_layer.md) — mapping layer design.

---

## Operator Workflows

- [oracle_signal_layer_v2_runtime.md](oracle_signal_layer_v2_runtime.md) — runtime operator flow for OSL v2.
- [oracle_signal_layer_v2_invariance.md](oracle_signal_layer_v2_invariance.md) — invariance workflow reference.
- [oracle_signal_layer_v2_receipts.md](oracle_signal_layer_v2_receipts.md) — runtime/validator receipt surfaces.
- [acceptance/README.md](acceptance/README.md) — acceptance workflow entry.
- [seal/SEAL_VALIDATION_GUIDE.md](seal/SEAL_VALIDATION_GUIDE.md) — seal validation usage.

---

## Validation / Attestation / Closure

- [VALIDATION_AND_ATTESTATION.md](VALIDATION_AND_ATTESTATION.md) — canonical boundary definitions.
- [artifacts/SCHEMA_INDEX.md](artifacts/SCHEMA_INDEX.md) — artifact schema index.
- [audit/osl_v2_evidence.md](audit/osl_v2_evidence.md) — evidence audit example.
- [ORACLE_SIGNAL_LAYER_V2_DROP.md](ORACLE_SIGNAL_LAYER_V2_DROP.md) — runtime proof drop note.

---

## Subsystems

- [SUBSYSTEM_INVENTORY.md](SUBSYSTEM_INVENTORY.md) — system-level subsystem status.
- [specs/SHADOW_STRUCTURAL_METRICS_INTEGRATION.md](specs/SHADOW_STRUCTURAL_METRICS_INTEGRATION.md) — shadow structural metrics integration spec.
- [specs/shadow_structural_metrics.md](specs/shadow_structural_metrics.md) — shadow metrics behavior.

> Note: authoritative subsystem manifests/registries live under `.abraxas/`, not `docs/`.

---

## Schemas / Contracts

- [artifacts/SCHEMA_INDEX.md](artifacts/SCHEMA_INDEX.md) — high-level schema catalog.
- [AUDIT_REPORT_SCHEMA.json](AUDIT_REPORT_SCHEMA.json) — audit-report schema surface.
- [api/openapi.yaml](api/openapi.yaml) — API schema.
- [openapi.yaml](openapi.yaml) — additional OpenAPI surface.

---

## Archive / Legacy / Historical

- [branch_consolidation.md](branch_consolidation.md) — branch cleanup notes.
- [MERGE_CONFLICT_ANALYSIS.md](MERGE_CONFLICT_ANALYSIS.md) — historical merge conflict analysis.
- [notion_scan_2026-03-27.md](notion_scan_2026-03-27.md) — historical Notion scan.
- [notion_execution_plan_2026-03-27.md](notion_execution_plan_2026-03-27.md) — historical execution plan.
- [coding_chunks_plan_2026-03-27.md](coding_chunks_plan_2026-03-27.md) — historical chunk plan.

---

## Contribution / Development

- Root contribution run path:
  - `pytest tests/gap_closure`
  - `python scripts/run_gap_closure_cycle.py --run-id RUN-GAP-FIRST-0001 --mode sandbox --workspace-only`
  - `python scripts/validate_gap_closure_artifacts.py --run-id RUN-GAP-FIRST-0001`
- Governance guardrails:
  - `python scripts/run_governance_lint.py`
  - `make registry-check`
- Repository policy and subsystem governance live under `.abraxas/`.

---

## Truth boundaries

- **Implemented**: deterministic gap closure runtime/validator/logger/report path and associated tests/scripts.
- **Partial**: readiness and promotion remain explicitly gated (`HOLD`/`BLOCK`) when evidence thresholds are unmet.
- **Experimental**: many audit/report scripts and exploratory docs in `docs/specs`, `docs/plan`, and `scripts/`.
- **Planned**: continued convergence/hardening of broad script/doc surfaces into tighter operator runbooks.
