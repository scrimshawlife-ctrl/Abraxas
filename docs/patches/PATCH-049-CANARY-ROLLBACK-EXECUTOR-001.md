# PATCH-049 — CANARY-ROLLBACK-EXECUTOR-001

## purpose
Execute rollback packets in sandbox or in-memory modes only, emitting deterministic rollback execution receipts.

## authority boundary
Rollback execution is sandbox-only/in-memory only. No production mutation, no baseline mutation, no runtime config writes, no promotion, no scheduler actions.

## sandbox-only rollback execution rule
Only `pending_review` packets with `recommend_approve_for_rollback_review` are executable; all others are skipped or blocked with explicit deterministic reasons.

## in-memory mode
When `sandbox_root` is not provided, no files are written and deterministic in-memory receipt hashes are emitted.

## sandbox receipt mode
When `sandbox_root` is provided, receipts are written under `sandbox_root/canary_rollback_receipts/{execution_id}.json` only.

## path safety model
Resolved receipt targets must remain inside the resolved sandbox receipt directory. Path escape attempts are blocked.

## deterministic hashing rules
Execution IDs are deterministic and exclude `created_at`, `artifact_path`, and `receipt_path`. Receipt hashes and execution hashes use canonical JSON.

## no production mutation guarantee
Executor never mutates production/runtime state and performs no destructive filesystem actions.

## next patch
PATCH-050 CANARY-ROLLBACK-OBSERVATION-LEDGER-001
