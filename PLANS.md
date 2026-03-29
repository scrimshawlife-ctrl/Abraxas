# AAL-Core Active Plan Surface

This file is the append-first execution queue for implementation runs.

## Operating Contract
- Keep updates incremental; avoid rewriting historical entries.
- Add new tasks under the active queue with date + owner + status.
- Move finished items to `Completed` with closure notes and linkage references.

## Active Queue

### P0 — Validator Artifact Linkage Closure
- **Status:** ACTIVE
- **Intent:** ensure rune execution artifacts link cleanly into validator/ledger surfaces.
- **Definition of done:** linkage fields populated or explicitly marked unresolved with reasons.

### P0 — Proof-Run Correlation Pointer Completion
- **Status:** ACTIVE
- **Intent:** complete correlation pointer propagation across run outputs.
- **Definition of done:** all execution artifacts include correlation pointer set semantics (present, empty, or unresolved reason).

### P1 — Rune-Aware Validator Surfacing
- **Status:** ACTIVE
- **Intent:** surface rune_id and phase-aware status in validator-facing summaries.
- **Definition of done:** validator layer can index or display per-rune execution outcomes.

### P1 — Execution Artifact Generation Integration
- **Status:** ACTIVE
- **Intent:** route execution-producing paths through a shared rune artifact envelope.
- **Definition of done:** new execution paths use wrapper-generated schema-aligned artifacts.

### P2 — Operator UI Spine Follow-up
- **Status:** CONDITIONAL
- **Intent:** only pursue if current roadmap still requires operator-facing execution trace surfaces.
- **Definition of done:** explicit go/no-go decision and scoped UI task list.

## Completed
- *(append completed items here; do not delete historical record)*
- 2026-03-29 — Governance surface verification run completed: confirmed required enforcement files (`/AGENTS.md`, `/PLANS.md`, `/aal_core/runes/catalog.v0.yaml`, `/aal_core/schemas/rune_execution_artifact.v1.json`, `/aal_core/runes/executor.py`) exist and are repository-visible for deterministic plan-gated execution.
- 2026-03-28 — ABX-Rune compliance probe path added (`aal_core/runes/compliance_probe.py`) with deterministic `RUNE.INGEST` artifact emission to `artifacts_seal/runs/compliance_probe/<run_id>.artifact.json`.
- 2026-03-28 — Correlation-linkage compliance probe added via `--linkage-mode` (`absent|present|not_computable`) with deterministic local test linkage provenance and explicit structural handling for empty/non-computable linkage.
- 2026-03-28 — Real linkage resolution probe pass added via `--linkage-mode resolve` in `aal_core/runes/compliance_probe.py`; deterministic repo-visible scan over `artifacts_seal` and `out/ledger` now attempts evidence-backed population of `ledger_record_ids`, `ledger_artifact_ids`, and `correlation_pointers` with explicit unresolved handling when no match is found.
- 2026-03-28 — Validator-surfacing closure bridge probe added via `--validator-surface-probe` in `aal_core/runes/compliance_probe.py`; emits validator-facing bridge artifact with explicit surface state (`SURFACED_TO_VALIDATOR_OUTPUT`, `UNSURFACED_STRUCTURALLY_AVAILABLE`, `NOT_COMPUTABLE`) while preserving run/artifact/rune/status/linkage fields from the compliance artifact.
- 2026-03-28 — Closure-grade readiness audit pass added via `scripts/run_closure_readiness_audit.py`; deterministic artifact classification now maps proof-chain status across visibility, linkage preservation, validator surfacing, correlation sufficiency, continuity, and promotion-evidence sufficiency to finite remediation hints.
- 2026-03-28 — Closure remediation ordering pass added via `scripts/run_closure_remediation_order.py`; consumes closure readiness audit artifact and emits deterministic blocker/prerequisite/downstream/cleanup patch queue with dependency notes and a single recommended first patch.
- 2026-03-28 — Executed `PATCH.CLOSURE.001` from closure remediation order: compliance probe now writes deterministic run-linked ledger rows to `out/ledger/compliance_probe_linkage.jsonl`, enabling validator `correlation.ledgerIds` continuity for probe runs without introducing additional queued patches.
- 2026-03-28 — Executed `PATCH.CLOSURE.002` from closure remediation order: resolve-mode compliance artifacts now carry deterministic non-empty `correlation_pointers` tied to probe-ledger continuity records, improving pointer sufficiency without implementing downstream patches.
- 2026-03-28 — Executed `PATCH.CLOSURE.003` from closure remediation order: `scripts/run_closure_readiness_audit.py` now applies an explicit promotion-readiness gate requiring `continuity` + `pointer_sufficiency` evidence (with supporting visibility/linkage/surfacing checks), yielding deterministic `SATISFIED|PARTIAL|BLOCKED|MISSING` classification without implementing downstream patches.
- 2026-03-28 — Closure scope-classification pass added via `scripts/run_closure_scope_classification.py`; deterministic artifact now separates probe-path confirmation from generalized non-probe proof surfaces and explicitly enumerates uncovered or blocked scope surfaces.
- 2026-03-28 — Generalized closure coverage pass added via `aal_core/runes/generalized_coverage_probe.py`; emits one deterministic non-probe run with run/artifact linkage to ledger + validator outputs so generalized scope can be measured without widening subsystem scope.
- 2026-03-28 — Closure stabilization attestation pass added via `scripts/run_closure_generalized_attestation.py`; emits deterministic milestone checkpoint `closure_generalized_attestation.v1.json` with evidence hashes, confirming run ids, satisfied closure conditions, and non-blocking follow-up separation.
- 2026-03-28 — Closure regression guard pass added via `tests/test_closure_generalized_regression_guard.py`; deterministic checks now protect generalized scope confirmation, attestation generation, and non-probe validator linkage structure for the attested closure milestone.
- 2026-03-28 — Closure milestone finalization pass: CI now executes `tests/test_closure_generalized_regression_guard.py` via `.github/workflows/abx_familiar_canary.yml`, and canonical note artifact recorded at `docs/artifacts/closure_generalized_milestone_note.v1.json`.
