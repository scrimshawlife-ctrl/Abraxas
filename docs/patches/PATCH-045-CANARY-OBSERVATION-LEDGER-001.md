# PATCH-045 — CANARY-OBSERVATION-LEDGER-001

## purpose
Record deterministic observation ledger entries from canary activation execution runs.

## authority boundary
Observation-only. No activation, no baseline mutation, no runtime config writes, no strategy execution, no scheduler registration, no promotion.

## observation role in system
Provides a stable ledger surface for post-execution analysis and traceability while preserving immutable lineage to execution artifacts.

## dedupe behavior
If a prior ledger is supplied, entries are deduped by `observation_id`; existing records are preserved and only new records are appended.

## replay + rollback preparation
Replayability and rollback keys are derived deterministically from execution status and artifact presence. No rollback is executed here.

## no activation guarantee
This patch never executes activation and never modifies existing execution records.

## next patch
PATCH-046 CANARY-ROLLBACK-PREP-001
