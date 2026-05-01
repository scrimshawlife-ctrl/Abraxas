# PATCH-048 — CANARY-ROLLBACK-PACKET-001

## purpose
Generate deterministic rollback packets from rollback review recommendations approved for rollback review.

## authority boundary
Rollback-packet generation only. No rollback execution, no activation/deactivation, no baseline mutation, no runtime config writes, no promotion, no scheduler actions.

## packet structure
Each packet includes rollback plan, safety, evidence, lineage, review placeholders, and strict non-execution authority flags.

## review-only nature
Packets are emitted in `pending_review` state and do not execute rollback.

## lineage tracking
Packet lineage links recommendation, rollback prep, and observation/execution hashes; missing lineage hashes are deterministically computed from matched objects when needed.

## skip behavior
Non-approved recommendations and missing/invalid dependencies are emitted as deterministic skipped records with explicit reasons.

## no rollback execution rule
This patch never executes rollback and never mutates upstream artifacts.

## next patch
PATCH-049 CANARY-ROLLBACK-EXECUTOR-001
