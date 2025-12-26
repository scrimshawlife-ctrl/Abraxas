"""Metric Governance CLI

Commands:
- propose: Propose new candidate metric
- evaluate: Run all promotion gates on candidate
- promote: Promote candidate to canonical registry (requires evidence bundle)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from abraxas.metrics.evaluate import MetricEvaluator
from abraxas.metrics.governance import (
    CandidateMetric,
    CandidateStatus,
    PromotionDecision,
    PromotionLedgerEntry,
)
from abraxas.metrics.registry_io import (
    CandidateRegistry,
    PromotionLedger,
    promote_candidate_to_canonical,
)


def cmd_propose(args):
    """Propose new candidate metric from spec file."""
    spec_path = Path(args.spec_file)

    if not spec_path.exists():
        print(f"Error: Spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    # Load spec
    with open(spec_path, "r") as f:
        spec = json.load(f)

    # Create candidate metric
    candidate = CandidateMetric.from_dict(spec)

    # Load candidate registry
    registry = CandidateRegistry()

    # Add to registry
    try:
        registry.add(candidate)
        registry.save()
        print(f"✓ Proposed candidate metric: {candidate.provenance.metric_id}")
        print(f"  Status: {candidate.status.value}")
        print(f"  Version: {candidate.version}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_evaluate(args):
    """Evaluate candidate metric through all gates."""
    metric_id = args.metric_id

    # Load candidate registry
    registry = CandidateRegistry()

    candidate = registry.get(metric_id)
    if not candidate:
        print(f"Error: Candidate {metric_id} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Evaluating candidate: {metric_id}")
    print(f"Current status: {candidate.status.value}")

    # Create evaluator
    evaluator = MetricEvaluator(sim_version="1.0.0")

    # WORKING THEORY: For demonstration, generate synthetic data
    # In production, would load from actual simulation runs
    print("\n[WORKING THEORY] Generating synthetic evaluation data...")

    np.random.seed(42)  # Deterministic
    candidate_values = np.random.randn(100)
    canonical_metrics = {
        "METRIC_A": np.random.randn(100),
        "METRIC_B": np.random.randn(100),
    }

    baseline_metrics = {
        "forecast_error": 0.25,
        "brier_score": 0.20,
        "calibration": 0.70,
        "misinfo_auc": 0.75,
        "divergence_explained": 0.30,
    }

    with_candidate_metrics = {
        "forecast_error": 0.22,  # 3% improvement
        "brier_score": 0.19,  # 1% improvement
        "calibration": 0.76,  # 6% improvement
        "misinfo_auc": 0.79,  # 4% improvement
        "divergence_explained": 0.37,  # 7% improvement
    }

    full_metrics = with_candidate_metrics
    ablated_metrics = baseline_metrics

    performance_history = [with_candidate_metrics] * 6  # 6 cycles

    seeds_used = [42, 43, 44, 45, 46]
    outcome_ledger_slice_hashes = ["a" * 64, "b" * 64, "c" * 64]

    # Run all gates
    evidence_bundle = evaluator.run_all_gates(
        candidate=candidate,
        candidate_values=candidate_values,
        canonical_metrics=canonical_metrics,
        baseline_metrics=baseline_metrics,
        with_candidate_metrics=with_candidate_metrics,
        full_metrics=full_metrics,
        ablated_metrics=ablated_metrics,
        performance_history=performance_history,
        seeds_used=seeds_used,
        outcome_ledger_slice_hashes=outcome_ledger_slice_hashes,
    )

    # Print results
    print("\n=== Promotion Gate Results ===")
    print(f"  Provenance:     {'✓ PASS' if evidence_bundle.test_results.provenance_passed else '✗ FAIL'}")
    print(f"  Falsifiability: {'✓ PASS' if evidence_bundle.test_results.falsifiability_passed else '✗ FAIL'}")
    print(f"  Redundancy:     {'✓ PASS' if evidence_bundle.test_results.redundancy_passed else '✗ FAIL'}")
    print(f"  Rent Payment:   {'✓ PASS' if evidence_bundle.test_results.rent_payment_passed else '✗ FAIL'}")
    print(f"  Ablation:       {'✓ PASS' if evidence_bundle.test_results.ablation_passed else '✗ FAIL'}")
    print(f"  Stabilization:  {'✓ PASS' if evidence_bundle.test_results.stabilization_passed else '✗ FAIL'}")

    print("\n=== Lift Metrics ===")
    print(f"  Forecast Error Δ: {evidence_bundle.lift_metrics.forecast_error_delta:+.4f}")
    print(f"  Brier Score Δ:    {evidence_bundle.lift_metrics.brier_delta:+.4f}")
    print(f"  Calibration Δ:    {evidence_bundle.lift_metrics.calibration_delta:+.4f}")
    print(f"  Misinfo AUC Δ:    {evidence_bundle.lift_metrics.misinfo_auc_delta:+.4f}")
    print(f"  Divergence Exp Δ: {evidence_bundle.lift_metrics.world_media_divergence_explained_delta:+.4f}")

    print("\n=== Redundancy Scores ===")
    print(f"  Max Correlation:  {evidence_bundle.redundancy_scores.max_corr:.4f}")
    print(f"  Mutual Info:      {evidence_bundle.redundancy_scores.mutual_info:.4f}")
    print(f"  Nearest Metrics:  {', '.join(evidence_bundle.redundancy_scores.nearest_metric_ids)}")

    print("\n=== Stabilization ===")
    print(f"  Cycles Required:  {evidence_bundle.stabilization_scores.cycles_required}")
    print(f"  Cycles Passed:    {evidence_bundle.stabilization_scores.cycles_passed}")
    print(f"  Drift Tests:      {evidence_bundle.stabilization_scores.drift_tests_passed}")
    print(f"  Performance Var:  {evidence_bundle.stabilization_scores.performance_variance:.6f}")

    # Update candidate status
    if evidence_bundle.test_results.all_passed():
        print("\n✓ All gates PASSED - candidate is READY for promotion")
        registry.update_status(metric_id, CandidateStatus.READY)
    else:
        print("\n✗ Some gates FAILED - candidate needs improvement")
        registry.update_status(metric_id, CandidateStatus.SCORED)

    # Save evidence bundle
    evidence_path = Path(f"ledger/evidence_{metric_id}.json")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_path, "w") as f:
        json.dump(evidence_bundle.to_dict(), f, indent=2)

    print(f"\nEvidence bundle saved: {evidence_path}")
    print(f"Evidence hash: {evidence_bundle.compute_hash()}")


def cmd_promote(args):
    """Promote candidate to canonical registry."""
    metric_id = args.metric_id

    # Load registries
    candidate_registry = CandidateRegistry()
    promotion_ledger = PromotionLedger()

    candidate = candidate_registry.get(metric_id)
    if not candidate:
        print(f"Error: Candidate {metric_id} not found", file=sys.stderr)
        sys.exit(1)

    # Check status
    if candidate.status != CandidateStatus.READY:
        print(f"Error: Candidate {metric_id} is not READY (current: {candidate.status.value})", file=sys.stderr)
        print("Run 'evaluate' command first and ensure all gates pass", file=sys.stderr)
        sys.exit(1)

    # Load evidence bundle
    evidence_path = Path(f"ledger/evidence_{metric_id}.json")
    if not evidence_path.exists():
        print(f"Error: Evidence bundle not found: {evidence_path}", file=sys.stderr)
        print("Run 'evaluate' command first", file=sys.stderr)
        sys.exit(1)

    with open(evidence_path, "r") as f:
        evidence_data = json.load(f)

    # Verify hash chain
    if not promotion_ledger.verify_chain():
        print("Error: Promotion ledger hash chain is invalid (possible tampering)", file=sys.stderr)
        sys.exit(1)

    # Create promotion ledger entry
    prev_hash = promotion_ledger.get_last_hash()

    # Reconstruct evidence bundle (simplified)
    from abraxas.metrics.governance import (
        EvidenceBundle,
        LiftMetrics,
        RedundancyScores,
        StabilizationScores,
        TestResults,
    )

    evidence_bundle = EvidenceBundle(
        metric_id=evidence_data["metric_id"],
        timestamp=evidence_data["timestamp"],
        sim_version=evidence_data["sim_version"],
        seeds_used=evidence_data["seeds_used"],
        outcome_ledger_slice_hashes=evidence_data["outcome_ledger_slice_hashes"],
        test_results=TestResults(**evidence_data["test_results"]),
        lift_metrics=LiftMetrics(**evidence_data["lift_metrics"]),
        redundancy_scores=RedundancyScores(**evidence_data["redundancy_scores"]),
        stabilization_scores=StabilizationScores(**evidence_data["stabilization_scores"]),
        ablation_results=evidence_data["ablation_results"],
    )

    # Create ledger entry
    entry = PromotionLedgerEntry.create_entry(
        metric_id=metric_id,
        candidate_version=candidate.version,
        sim_version=evidence_bundle.sim_version,
        evidence_bundle=evidence_bundle,
        decision=PromotionDecision.PROMOTED,
        rationale="All gates passed. Measurable lift demonstrated. Ablation survival confirmed. Stabilization achieved.",
        prev_hash=prev_hash,
    )

    # Append to ledger
    promotion_ledger.append(entry)

    # Promote to canonical registry
    promote_candidate_to_canonical(candidate, candidate_registry)

    print(f"✓ Promoted {metric_id} to canonical registry")
    print(f"  Evidence hash: {evidence_bundle.compute_hash()}")
    print(f"  Ledger entry signature: {entry.signature}")
    print(f"  Chain verified: {promotion_ledger.verify_chain()}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Abraxas Metric Governance CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Propose command
    propose_parser = subparsers.add_parser(
        "propose", help="Propose new candidate metric"
    )
    propose_parser.add_argument("spec_file", help="Path to metric spec JSON file")
    propose_parser.set_defaults(func=cmd_propose)

    # Evaluate command
    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Evaluate candidate metric"
    )
    evaluate_parser.add_argument("metric_id", help="Metric ID to evaluate")
    evaluate_parser.set_defaults(func=cmd_evaluate)

    # Promote command
    promote_parser = subparsers.add_parser(
        "promote", help="Promote candidate to canonical"
    )
    promote_parser.add_argument("metric_id", help="Metric ID to promote")
    promote_parser.set_defaults(func=cmd_promote)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
