#!/usr/bin/env python3
"""Performance Tuning Plane v0.1 - Demo Script.

Demonstrates canary workflow:
1. PERF_SUMMARIZE - compute metrics from ledger
2. PERF_TUNE_PROPOSE - propose candidate IR
3. PERF_TUNE_CANARY - deploy to canary
4. PERF_TUNE_PROMOTE - promote if gates pass
5. PERF_TUNE_REVOKE - rollback if needed
"""

from abraxas.tuning import (
    create_default_ir,
    propose_tuning,
    apply_ir_atomically,
    check_rent_gates,
    compute_rent_metrics,
)
from abraxas.runes.operators.tuning_layer import (
    apply_perf_summarize,
    apply_perf_tune_propose,
    apply_perf_tune_canary,
    apply_perf_tune_promote,
    apply_perf_tune_revoke,
)

def main():
    print("=" * 70)
    print("PERFORMANCE TUNING PLANE v0.1 - CANARY WORKFLOW DEMO")
    print("=" * 70)
    print()

    run_ctx = {"run_id": "DEMO_TUNING_001"}

    # Step 1: Summarize
    print("1. ABX-PERF_SUMMARIZE (ϟ₂₄) - Compute metrics from ledger")
    summary = apply_perf_summarize(window_hours=168, run_ctx=run_ctx)
    print(f"   Summary hash: {summary['summary_hash'][:16]}...")
    print(f"   Total bytes saved: {summary['metrics']['total_bytes_saved']}")
    print()

    # Step 2: Propose
    print("2. ABX-PERF_TUNE_PROPOSE (ϟ₂₅) - Generate candidate IR")
    proposal = apply_perf_tune_propose(summary=summary, run_ctx=run_ctx)
    print(f"   Predicted improvement: {proposal['predicted_improvement']:.3f}")
    print(f"   Risk score: {proposal['risk_score']:.2f}")
    print(f"   Rationale: {proposal['rationale']}")
    print()

    # Step 3: Canary
    print("3. ABX-PERF_TUNE_CANARY (ϟ₂₆) - Deploy to canary")
    canary_result = apply_perf_tune_canary(
        proposal_ir=proposal['proposal_ir'],
        run_ctx=run_ctx
    )
    print(f"   Status: {canary_result['status']}")
    print(f"   Canary path: {canary_result['canary_path']}")
    print()

    # Step 4: Simulate canary run and collect metrics
    print("4. Simulating canary run (would run real workload here)")
    metrics_before = summary['metrics']
    metrics_after = summary['metrics']  # In real use, would collect new metrics
    print("   (Using same metrics for demo purposes)")
    print()

    # Step 5: Promote (if gates pass)
    print("5. ABX-PERF_TUNE_PROMOTE (ϟ₂₇) - Check rent gates")
    promote_result = apply_perf_tune_promote(
        metrics_before=metrics_before,
        metrics_after=metrics_after,
        run_ctx=run_ctx
    )
    print(f"   Promoted: {promote_result['promoted']}")
    print(f"   Gate results: {promote_result['gate_results']}")
    print()

    # Step 6: Revoke (if needed)
    if not promote_result['promoted']:
        print("6. ABX-PERF_TUNE_REVOKE (ϟ₂₈) - Rollback")
        revoke_result = apply_perf_tune_revoke(run_ctx=run_ctx)
        print(f"   Revoked: {revoke_result['revoked']}")
        print()

    print("=" * 70)
    print("✓ Canary workflow complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
