# Readiness Comparison Ledger (Read-Only)

## Purpose
Track historical snapshots that place Developer Readiness and Gap Closure Invariance projections side-by-side for operator visibility.

## Authority boundary
- Read-only observational surface.
- Non-promotive.
- Alignment state is descriptive, not policy authority.
- Promotion remains governed by canonical promotion-policy / attestation surfaces.

## Artifacts
- Latest: `out/reports/readiness_comparison.latest.json`
- Ledger: `out/reports/readiness_comparison_ledger.jsonl`

## Generation
```bash
python scripts/log_readiness_comparison.py
```

## Alignment states
- `ALIGNED`
- `DEV_READY_GAP_HOLD`
- `DEV_PARTIAL_GAP_READY`
- `BOTH_PARTIAL`
- `NOT_COMPUTABLE`
- `UNKNOWN`

These labels summarize observable projection posture only; they do not modify readiness thresholds, promotion decisions, CI authority, or gap-closure authority.
