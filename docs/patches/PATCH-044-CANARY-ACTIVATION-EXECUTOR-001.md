# PATCH-044 — CANARY-ACTIVATION-EXECUTOR-001

## Purpose
Consume `CanaryActivationPacketRun.v1` and emit deterministic `CanaryActivationExecutionRun.v1` records for sandboxed canary activation execution receipts.

## Authority boundary
Allowed: packet validation, deterministic execution records, optional sandbox receipt writes, canonical JSON output.
Forbidden: baseline mutation, runtime/global config writes, scheduler registration, promotion, production activation/execution, network calls.

## Why this is still not promotion
Executor output is receipt-only and scoped to `environment=canary`. It does not alter production state, does not promote overlays, and does not mutate baseline weights.

## Input artifact
`CanaryActivationPacketRun.v1`

## Output artifact
`CanaryActivationExecutionRun.v1`

## Sandbox receipt behavior
If `sandbox_root` is provided, one canonical receipt JSON is written per execution under:
`{sandbox_root}/canary_activation_receipts/{execution_id}.json`
If absent, execution remains in-memory with `artifact_path=null` and deterministic `artifact_hash`.

## Determinism guarantees
- Caller-provided `created_at` and `scope_id`
- Canonical JSON hashing/signature rules
- Deterministic sorting of executions and skipped records
- Idempotent output for identical input+args

## Skip/block reasons
- `invalid_packet_run`
- `invalid_packet`
- `not_approved_for_execution`
- `invalid_overlay_payload`
- `missing_required_lineage`
- `sandbox_apply_failed:<detail>`
- `authority_boundary_violation:<detail>`

## PATCH-045 handoff
PATCH-045: `CANARY-OBSERVATION-LEDGER-001` consumes `CanaryActivationExecutionRun.v1` and records post-activation observation windows/outcomes without promotion authority.
