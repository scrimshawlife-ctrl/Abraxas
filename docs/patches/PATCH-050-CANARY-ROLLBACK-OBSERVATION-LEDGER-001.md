# PATCH-050 — CANARY-ROLLBACK-OBSERVATION-LEDGER-001

## purpose
Convert rollback execution results into deterministic rollback observation ledger entries.

## authority boundary
Observation-only. No rollback execution, no baseline mutation, no runtime config writes, no packet/execution mutation, no promotion, no scheduler actions.

## observation role
Provides deterministic audit continuity for rollback execution outcomes and lineage across packet and execution surfaces.

## replay/rollback derivation
- replayable when execution status is `completed`
- replay key derived from artifact hash when present
- rollback prepared remains false
- rollback key derived from artifact hash for completed executions only

## dedupe behavior
Observation entries dedupe by `observation_id` against prior ledger; existing entries are preserved and only new entries are appended.

## no-execution guarantee
This patch does not execute rollback and does not modify rollback execution artifacts.

## next
PATCH-051 — CANARY-CYCLE-CLOSURE-REPORT-001
