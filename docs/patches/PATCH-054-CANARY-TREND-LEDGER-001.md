# PATCH-054 — CANARY-TREND-LEDGER-001

## objective
Persist deterministic trend-analysis snapshots into an append-only trend ledger with idempotent dedupe and preserved prior review state.

## scope and lane
- scope: canary trend ledger persistence surface
- lane: shadow (advisory governance artifacts only; non-authoritative for execution)

## subsystem id
CANARY-TREND-LEDGER-001

## change class
Additive new module + validator + runner + schemas + CLI + tests + patch docs.

## proof targets
- deterministic entry ids via canonical hashing of `{analysis_id, analysis_hash}`
- deterministic lineage hash via canonical hashing of `{analysis_id, analysis_hash, lineage}`
- dedupe by `entry_id`
- preserve prior ledger entries exactly
- append-only semantics for new entries
- deterministic ordering by `(trend_status, analysis_id, entry_id)`
- deterministic counts for `stable`, `needs_attention`, `not_computable`
- byte-identical canonical JSON across repeated runs

## tests and validation commands
- `PYTHONPATH=. pytest -q tests/test_canary_trend_ledger.py`

## declared risks and stop conditions
- risk: upstream trend-analysis payload missing required ids/hashes
- stop condition: schema/registry mismatch or missing validator receipts for promoted claims

## next patch
PATCH-055 CANARY-TREND-LEDGER-REVIEW-GATE-001
