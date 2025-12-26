"""
Worked Example: Emergent Metrics Shadow Evaluation

Demonstrates the full lifecycle of an emergent metric from proposal to shadow
evaluation (without promotion).

This example:
1. Analyzes synthetic outcome ledger data
2. Proposes a candidate metric to explain world_media_divergence variance
3. Runs the metric in SHADOW mode across multiple simulation cycles
4. Evaluates the metric but does NOT promote it to canonical status
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from abraxas.metrics.emergence import MetricEmergence
from abraxas.metrics.evidence import EvidenceBundle
from abraxas.sim.ledger import OutcomeLedger


def generate_synthetic_ledger(
    ledger: OutcomeLedger, num_cycles: int = 100, seed: int = 42
) -> None:
    """
    Generate synthetic outcome ledger with unexplained variance.

    Creates a world_media_divergence metric with high variance that
    could benefit from a decomposition metric.
    """
    random.seed(seed)

    for cycle in range(num_cycles):
        # Simulate canonical metrics
        base_divergence = 0.5 + 0.3 * random.random()

        # Introduce unexplained variance (synthetic signal)
        if cycle % 7 == 0:  # Weekly spike pattern
            base_divergence += 0.4 * random.random()

        canonical_metrics = {
            "world_media_divergence": base_divergence,
            "forecast_confidence": 0.7 + 0.2 * random.random(),
            "symbolic_drift_rate": 0.1 + 0.1 * random.random(),
        }

        # Shadow metrics would be computed here but not affect state
        shadow_metrics = {}

        ledger.append_outcome(
            cycle=cycle,
            canonical_metrics=canonical_metrics,
            shadow_metrics=shadow_metrics,
            rune_bindings=["ϟ₁", "ϟ₂", "ϟ₃"],
            seed=seed + cycle,
        )


def run_emergence_analysis() -> dict[str, any]:
    """
    Run metric emergence analysis on synthetic ledger.

    Returns:
        Proposed candidate metric
    """
    # Initialize emergence module
    emergence = MetricEmergence(
        ledger_path=".aal/ledger/outcomes_example.jsonl",
        output_path="registry/metrics_candidate_example.json",
    )

    # Run emergence (analyze patterns)
    candidates = emergence.run_emergence(limit=1000)

    print(f"✓ Emergence analysis complete: {len(candidates)} candidate(s) proposed")

    if candidates:
        candidate = candidates[0]
        print(f"  Metric ID: {candidate['metric_id']}")
        print(f"  Hypothesis: {candidate['hypothesis_type']}")
        print(f"  Description: {candidate['description']}")
        print(f"  Status: {candidate['status']}")

    # Write candidates to registry
    emergence.write_candidates(candidates)

    return candidates[0] if candidates else None


def simulate_shadow_execution(
    candidate: dict[str, any], ledger: OutcomeLedger, num_cycles: int = 50, seed: int = 100
) -> list[float]:
    """
    Simulate shadow metric execution across multiple cycles.

    CRITICAL: Shadow metric values are logged but do NOT affect state transitions.

    Args:
        candidate: Candidate metric spec
        ledger: Outcome ledger
        num_cycles: Number of cycles to simulate
        seed: Random seed

    Returns:
        Shadow metric values across cycles
    """
    random.seed(seed)
    shadow_values = []

    print(f"\n✓ Running shadow metric '{candidate['metric_id']}' for {num_cycles} cycles")

    for cycle in range(num_cycles):
        # Compute canonical metrics (these affect state)
        canonical_metrics = {
            "world_media_divergence": 0.5 + 0.3 * random.random(),
            "forecast_confidence": 0.7 + 0.2 * random.random(),
        }

        # Compute shadow metric (observe-only, no state feedback)
        # This is a placeholder - real implementation would use candidate spec
        shadow_metric_value = 0.3 + 0.2 * random.random()
        if cycle % 7 == 0:
            shadow_metric_value += 0.15  # Detects the weekly spike pattern

        shadow_values.append(shadow_metric_value)

        # Log to ledger (shadow metrics separate from canonical)
        ledger.append_outcome(
            cycle=1000 + cycle,
            canonical_metrics=canonical_metrics,
            shadow_metrics={candidate["metric_id"]: shadow_metric_value},
            rune_bindings=["ϟ₁", "ϟ₂"],
            seed=seed + cycle,
        )

    print(f"  Shadow metric mean: {sum(shadow_values) / len(shadow_values):.3f}")
    print(f"  Shadow metric std dev: {(sum((v - sum(shadow_values)/len(shadow_values))**2 for v in shadow_values) / len(shadow_values))**0.5:.3f}")

    return shadow_values


def evaluate_shadow_metric(
    candidate: dict[str, any], ledger: OutcomeLedger, shadow_values: list[float]
) -> dict[str, any]:
    """
    Evaluate shadow metric performance.

    Computes lift, redundancy, ablation, and stability metrics.
    Does NOT promote the metric.

    Args:
        candidate: Candidate metric spec
        ledger: Outcome ledger
        shadow_values: Shadow metric values

    Returns:
        Evaluation results
    """
    print(f"\n✓ Evaluating shadow metric '{candidate['metric_id']}'")

    # Simulated evaluation metrics (real implementation would compute these)
    evaluation_results = {
        "lift": {
            "mae_delta": 0.03,  # 3% forecast error improvement
            "brier_delta": 0.015,  # 1.5% Brier score improvement
            "misinfo_auc_delta": 0.02,  # 2% AUC improvement
        },
        "redundancy": {
            "max_correlation": 0.72,  # Below 0.85 threshold (non-redundant)
            "euclidean_distance": 0.28,
        },
        "ablation": {
            "performance_drop": 0.08,  # 8% performance drop when removed (proves value)
        },
        "stability": {
            "stable_cycles": 7,  # 7 consecutive stable cycles
            "coefficient_variation": 0.09,  # 9% CV (below 10% threshold)
            "drift_detection_rate": 0.65,  # 65% synthetic drift detection
        },
    }

    print("  Lift Metrics:")
    print(f"    MAE Delta: {evaluation_results['lift']['mae_delta']:.3f}")
    print(f"    Brier Delta: {evaluation_results['lift']['brier_delta']:.3f}")
    print("  Redundancy Metrics:")
    print(f"    Max Correlation: {evaluation_results['redundancy']['max_correlation']:.2f}")
    print("  Ablation:")
    print(f"    Performance Drop: {evaluation_results['ablation']['performance_drop']:.2f}")
    print("  Stability:")
    print(f"    Stable Cycles: {evaluation_results['stability']['stable_cycles']}")
    print(f"    CV: {evaluation_results['stability']['coefficient_variation']:.2f}")

    return evaluation_results


def create_evidence_bundle_example(
    candidate: dict[str, any], evaluation_results: dict[str, any]
) -> dict[str, any]:
    """
    Create evidence bundle for the candidate metric.

    Evidence bundles are required for promotion but this example stops short
    of actual promotion.

    Args:
        candidate: Candidate metric spec
        evaluation_results: Evaluation outputs

    Returns:
        Evidence bundle
    """
    print(f"\n✓ Creating evidence bundle for '{candidate['metric_id']}'")

    evidence_system = EvidenceBundle(evidence_dir="evidence_example")

    # Simulated inputs
    ledger_slice = [{"cycle": i, "data": "..."} for i in range(100)]
    registry_snapshots = {
        "metrics_registry": "sha256_metrics_abc123",
        "simvars_registry": "sha256_simvars_def456",
        "runes_registry": "sha256_runes_ghi789",
    }
    seeds = [42, 43, 44, 45, 46]

    bundle = evidence_system.create_bundle(
        metric_id=candidate["metric_id"],
        candidate_spec=candidate,
        ledger_slice=ledger_slice,
        evaluation_results=evaluation_results,
        registry_snapshots=registry_snapshots,
        seeds=seeds,
    )

    print(f"  Bundle ID: {bundle['bundle_id']}")
    print(f"  Composite Score: {bundle['composite_score']:.3f}")
    print(f"  Promotion Eligible: {bundle['promotion_eligible']}")
    print("  Gates Passed:")
    for gate, passed in bundle["gates_passed"].items():
        print(f"    {gate}: {'✓' if passed else '✗'}")

    # Write bundle to disk
    bundle_path = evidence_system.write_bundle(bundle)
    print(f"  Bundle written to: {bundle_path}")

    return bundle


def main():
    """Run full emergent metrics example."""
    print("=" * 70)
    print("Abraxas Emergent Metrics: Shadow Evaluation Example")
    print("=" * 70)

    # Step 1: Generate synthetic ledger
    print("\n[1/5] Generating synthetic outcome ledger...")
    ledger = OutcomeLedger(ledger_path=".aal/ledger/outcomes_example.jsonl")
    generate_synthetic_ledger(ledger, num_cycles=100, seed=42)
    print(f"✓ Generated 100 cycles with unexplained variance in world_media_divergence")

    # Step 2: Run emergence analysis
    print("\n[2/5] Running metric emergence analysis...")
    candidate = run_emergence_analysis()

    if not candidate:
        print("✗ No candidates proposed. Exiting.")
        return

    # Step 3: Run shadow metric execution
    print("\n[3/5] Running shadow metric execution...")
    shadow_values = simulate_shadow_execution(candidate, ledger, num_cycles=50, seed=100)

    # Verify shadow isolation
    print("\n[4/5] Verifying shadow metric isolation...")
    isolation_ok = ledger.verify_shadow_isolation()
    if isolation_ok:
        print("✓ Shadow isolation verified: shadow metrics do NOT affect canonical metrics")
    else:
        print("✗ WARNING: Shadow isolation violated!")

    # Step 4: Evaluate shadow metric
    print("\n[5/5] Evaluating shadow metric performance...")
    evaluation_results = evaluate_shadow_metric(candidate, ledger, shadow_values)

    # Step 5: Create evidence bundle (but do NOT promote)
    bundle = create_evidence_bundle_example(candidate, evaluation_results)

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Candidate Metric: {candidate['metric_id']}")
    print(f"Hypothesis Type: {candidate['hypothesis_type']}")
    print(f"Status: {candidate['status']} → SHADOW (not promoted)")
    print(f"Shadow Cycles Executed: 50")
    print(f"Evidence Bundle Created: Yes")
    print(f"Promotion Eligible: {bundle['promotion_eligible']}")
    print("\nNOTE: Metric remains in SHADOW status. Promotion requires governance approval.")
    print("=" * 70)


if __name__ == "__main__":
    main()
