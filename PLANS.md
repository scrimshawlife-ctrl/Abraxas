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

### P2 — Operator UI Shell Follow-up
- **Status:** CONDITIONAL
- **Intent:** only pursue if current roadmap still requires implementation-shell updates around the canonical Operator Console.
- **Definition of done:** explicit go/no-go decision and scoped UI shell task list with canonical-entrypoint signage preserved.


### P0 — Large-Run Deterministic Convergence Spine
- **Status:** COMPLETE (2026-03-30)
- **Intent:** scale proof/validator/policy/operator flow to large-run batches without losing deterministic artifact linkage.
- **Definition of done:** large-run orchestration emits per-run + batch-level artifacts with explicit `run_id`, `rune_id`, `artifact_id`, `timestamp`, status, linkage pointers, and fail-closed `NOT_COMPUTABLE` handling when linkage is incomplete.
- **Execution Steps (PLAN extension):**
  1. **Batch run envelope audit**
     - rune_id: `RUNE.DIFF`
     - input contract: execution-validation + projection artifacts
     - output contract: large-run coverage ledger (`out/ledger/large_run_coverage.jsonl`)
     - determinism: sorted run-id traversal, stable hash ordering
     - artifact/linkage: per-run evidence pointers + batch summary pointer
  2. **Correlation-pointer density gate**
     - rune_id: `RUNE.INGEST`
     - input contract: validator correlation blocks
     - output contract: pointer sufficiency report (`out/reports/large_run_pointer_sufficiency.json`)
     - determinism: threshold policy from static config, no randomized sampling
     - artifact/linkage: explicit unresolved reasons when any run lacks pointers
  3. **Rune-aware operator index emission**
     - rune_id: `RUNE.DIFF`
     - input contract: validator `runeContext` + operator projection summaries
     - output contract: rune/run matrix (`out/operator/rune_run_index.json`)
     - determinism: canonical rune sort + run sort
     - artifact/linkage: references validator artifact ids + projection artifact ids
  4. **Promotion-policy batch barrier**
     - rune_id: `RUNE.DIFF`
     - input contract: readiness/policy artifacts for each run
     - output contract: batch promotion barrier artifact (`out/policy/large_run_barrier.json`)
     - determinism: fail-closed aggregate state computed from per-run policy states
     - artifact/linkage: includes blocking run ids + policy artifact pointers
 - **Closure evidence (implemented):**
   - `scripts/run_large_run_coverage_audit.py` → `out/reports/large_run_coverage_<batch_id>.json` + `out/ledger/large_run_coverage.jsonl`
   - `scripts/run_large_run_pointer_sufficiency.py` → `out/reports/large_run_pointer_sufficiency_<batch_id>.json`
   - `scripts/run_large_run_rune_run_index.py` → `out/operator/rune_run_index.json`
   - `scripts/run_large_run_promotion_barrier.py` → `out/policy/large_run_barrier_<batch_id>.json`
   - `scripts/run_large_run_convergence.py` → `out/reports/large_run_convergence_<batch_id>.json`

## Completed
- 2026-04-09 — OSLv2 operator ergonomics pass: added Makefile entrypoints (`run-oracle-signal-layer-v2`, `run-oracle-signal-layer-v2-invariance`, `test-oracle-signal-layer-v2`) to keep runtime/invariance/validation execution deterministic and reusable from one command surface.
- 2026-04-08 — Oracle Signal Layer v2 verticalization pass: split runtime into contract/runtime/advisory/stability/proof modules, enforced interpretation-only authority scope, added digest-triplet invariance runner, receipt writer, and focused oracle test suite with explicit NOT_COMPUTABLE advisory visibility.
- 2026-04-08 — Oracle Signal Layer v2 subsystem drop: landed deterministic `OracleSignalInputEnvelope.v2 -> OracleSignalLayerOutput.v2` runtime spine with bounded MIRCL/trend advisory attachments, validator summary emission, digest-based invariance harness, schema contracts, execution script, and focused tests for authority/advisory boundary enforcement.
- 2026-04-08 — Operator family naming-law signage pass: classified Operator Console as canonical entrypoint, Operator Mode as runtime state, and Operator UI as implementation shell across webpanel surfaces; added run-console build-artifact signage to prevent wrong-entrypoint drift.
- *(append completed items here; do not delete historical record)*
- 2026-03-30 — PR conflict-resolution merge pass: verified repository merge state is clean (`git status --porcelain -b` and conflict marker scan), then recorded explicit NOT_COMPUTABLE merge outcome because no additional local/remote PR refs are present to merge in this environment.
- 2026-03-30 — Large-run runtime contract enforcement pass: added `scripts/large_run_contracts.py` and wired envelope validation into all large-run builders so invalid artifacts fail fast before write, with focused contract-unit tests.
- 2026-03-30 — Large-run contract schema pass: added shared envelope schema `aal_core/schemas/large_run_execution_artifact.v1.json` and focused contract test coverage to ensure large-run artifacts emit required run-linked fields (`run_id`, `rune_id`, `artifact_id`, `timestamp`, `phase`, `status`, `inputs/outputs`, `provenance`, `correlation_pointers`).
- 2026-03-30 — Large-run convergence operationalization pass: wired canonical `make large-run-convergence BATCH_ID=<id> [MIN_POINTERS=1]` target to execute deterministic bundle orchestration through `scripts/run_large_run_convergence.py`.
- 2026-03-30 — Large-run convergence orchestration pass: added `scripts/run_large_run_convergence.py` to compose coverage, pointer sufficiency, rune-run indexing, and promotion barrier into deterministic `LargeRunConvergenceBundle.v1` outputs with fail-closed aggregate status (`SUCCESS|BLOCKED|NOT_COMPUTABLE`).
- 2026-03-30 — Large-run convergence step-4 implementation pass: added `scripts/run_large_run_promotion_barrier.py` to emit deterministic `LargeRunPromotionBarrier.v1` batch artifacts that aggregate per-run promotion-policy decisions into fail-closed `SUCCESS|BLOCKED|NOT_COMPUTABLE` barrier states with blocking reason codes.
- 2026-03-30 — Large-run convergence step-3 implementation pass: added `scripts/run_large_run_rune_run_index.py` to emit deterministic `RuneRunIndex.v1` artifacts mapping `rune_id -> run_id` rows with validator/projection status linkage for operator indexing surfaces.
- 2026-03-30 — Large-run convergence step-2 implementation pass: added `scripts/run_large_run_pointer_sufficiency.py` to emit deterministic `LargeRunPointerSufficiency.v1` artifacts that classify per-run correlation pointer sufficiency with explicit threshold-based `SUFFICIENT|NOT_COMPUTABLE` states and reason codes.
- 2026-03-30 — Large-run convergence step-1 implementation pass: added `scripts/run_large_run_coverage_audit.py` to emit deterministic `LargeRunCoverageAudit.v1` batch artifacts and run-linked ledger rows (`out/ledger/large_run_coverage.jsonl`) with explicit `COVERED|NOT_COMPUTABLE` states and reason codes.
- 2026-03-30 — Validator traceability contract hardening pass: rune governance traceability checks now fail closed when `ExecutionValidationArtifact.v1` omits `runeContext.runeIds` or `runeContext.phases`, with focused tests covering missing and linked-complete states.
- 2026-03-30 — Rune-context projection bridge pass: `abx.operator_projection` now surfaces validator `runeContext` into deterministic linkage summary fields (`rune_id_count`, `rune_ids`, `phase_count`, `phases`) so operator views can index rune-level execution context directly.
- 2026-03-30 — Rune-aware validator surfacing pass: `abx.execution_validator` now extracts `rune_id` + `phase` from run-linked evidence and emits deterministic `runeContext` (`runeIds`, `phases`) in `ExecutionValidationArtifact.v1`, with focused type/validator coverage tests.
- 2026-03-30 — Operator Surface v1 pass: added canonical operator view aggregation (`abx/operator_views.py`), webpanel run-console/compare/release/evidence routes, secondary operator APIs, shared TS view contracts, and focused operator-surface tests without forking core proof/readiness/policy semantics.
- 2026-03-30 — Pre-feature stabilization/release pass: added `ReleaseReadinessReport.v1` surface (`scripts/run_release_readiness.py`, `docs/RELEASE_READINESS.md`, `make release-readiness`), introduced canonical TS sanity lane (`tsconfig.canonical.json`, `make ts-canonical-check`), and expanded federated transport/evidence semantics to `RemoteEvidenceManifest.v1` with bounded packet freshness/consistency aggregation propagated into readiness/policy/projection.
- 2026-03-30 — Remaining-totality hardening pass: added federated transport/remote evidence spine v0 (`abx/federated_transport.py`), linked remote evidence verification into Tier 2.5/2.75 and Tier 3 policy provenance, expanded governance lint discovery to CLI/make heavy surfaces, and further contained shadow `run_promotion_pack` behind explicit override.
- 2026-03-30 — Convergence hardening consolidation pass: added consolidated governance lint (`scripts/run_governance_lint.py`) with anti-regrowth checks for canonical command surfacing, tier language coherence, shadow/deprecate labeling, heavy-path classification coverage, and TS projection token parity; wired `make governance-lint` and added guardrail tests.
- 2026-03-30 — Shadow path stabilization/retirement triage pass: stabilized `tools/acceptance/run_acceptance_suite.py` for non-repo cwd invocation, expanded shadow triage taxonomy (`STABILIZE_SHADOW`, `REDIRECT_TO_CANONICAL`, `DEPRECATE_OR_RETIRE`) in subsystem inventory, and marked seal diagnostics as deprecate/archive candidates for promotion workflows.
- 2026-03-30 — Historical Tier 3 path audit + containment pass: classified promotion/seal/attestation-adjacent entrypoints in docs, marked non-canonical heavy paths as shadow diagnostics, and gated `abx.cli acceptance` behind explicit override (`ABX_ALLOW_SHADOW_ACCEPTANCE=1`) with canonical guidance to `scripts/run_execution_attestation.py`.
- 2026-03-30 — Tier 3 execution gate integration pass: `scripts/run_execution_attestation.py` now evaluates Tier 2.75 policy first, refuses heavy execution for `BLOCKED`/`NOT_COMPUTABLE`, and embeds policy provenance (`decision_state`, reason codes, blockers, waiver/federation fields, policy artifact path) in attestation artifacts.
- 2026-03-30 — Promotion policy gate pass: added deterministic Tier 2.75 policy evaluator (`abx/promotion_policy.py`), CLI + artifact emission (`abx.cli promotion-policy`, `out/policy/promotion-policy-<run_id>.json`), projection policy fields, and focused allow/block/waive/not-computable tests/docs clarifying readiness vs permission boundary.
- 2026-03-30 — Federated evidence + Tier 3 hardening pass: added explicit federated evidence contract (`abx/federated_evidence.py`), extended promotion readiness with local vs federated states, and surfaced Tier 2/Tier 2.5 boundaries in operator projection and docs without simulating remote execution.
- 2026-03-30 — Operator projection convergence pass: introduced `OperatorProjectionSummary.v1` derivation (`abx/operator_projection.py`), wired webpanel projection JSON route (`/runs/{run_id}/projection.json`), and aligned TS secondary API semantics (`/api/operator/projection/:runId`, `shared/operatorProjection.ts`) with focused anti-drift/tests.
- 2026-03-30 — Promotion bridge pass: added deterministic promotion-readiness contract + CLI (`abx.cli promotion-check`), bridge artifact emission (`out/promotion`), closure-tier docs split, and canonical onboarding drift guard tests.
- 2026-03-30 — Canonical convergence pass: added `abx.cli proof-run` + `abx/proof_closure.py` to enforce one deterministic proof spine (emit→ledger→validate→operator projection→attest), and compressed operator/runtime/docs truth surfaces via `README.md`, `docs/CANONICAL_RUNTIME.md`, `docs/VALIDATION_AND_ATTESTATION.md`, and `docs/SUBSYSTEM_INVENTORY.md`.
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
