"""
Metrics Governance CLI

Command-line interface for metric promotion governance.

CRITICAL: Only this CLI may promote metrics from shadow to canonical status.
All promotions require evidence bundle verification.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from abraxas.core.provenance import hash_canonical_json
from abraxas.metrics.evidence import EvidenceBundle


def list_candidates(candidates_path: Path) -> None:
    """List all candidate metrics and their status."""
    if not candidates_path.exists():
        print("No candidate metrics found.")
        return

    with open(candidates_path, "r") as f:
        data = json.load(f)

    candidates = data.get("candidates", [])

    if not candidates:
        print("No candidate metrics found.")
        return

    print(f"\nCandidate Metrics ({len(candidates)} total)")
    print("=" * 80)

    for candidate in candidates:
        metric_id = candidate.get("metric_id", "unknown")
        status = candidate.get("status", "unknown")
        hypothesis = candidate.get("hypothesis_type", "unknown")
        description = candidate.get("description", "")

        print(f"\nMetric ID: {metric_id}")
        print(f"  Status: {status}")
        print(f"  Hypothesis: {hypothesis}")
        print(f"  Description: {description[:70]}...")


def list_evidence_bundles(evidence_dir: Path) -> None:
    """List all available evidence bundles."""
    evidence_system = EvidenceBundle(evidence_dir=evidence_dir)
    eligible = evidence_system.get_promotion_ready_metrics()

    if not eligible:
        print("\nNo promotion-eligible metrics found.")
        return

    print(f"\nPromotion-Eligible Metrics ({len(eligible)} total)")
    print("=" * 80)

    for item in eligible:
        print(f"\nMetric ID: {item['metric_id']}")
        print(f"  Bundle ID: {item['bundle_id']}")
        print(f"  Composite Score: {item['composite_score']:.3f}")
        print(f"  Created: {item['created_at']}")
        print(f"  Bundle Path: {item['bundle_path']}")


def verify_bundle(metric_id: str, bundle_id: str, evidence_dir: Path) -> bool:
    """
    Verify evidence bundle integrity.

    Args:
        metric_id: Metric ID
        bundle_id: Bundle ID
        evidence_dir: Evidence directory

    Returns:
        True if bundle is valid
    """
    evidence_system = EvidenceBundle(evidence_dir=evidence_dir)

    try:
        bundle = evidence_system.load_bundle(metric_id, bundle_id)
    except FileNotFoundError:
        print(f"✗ Evidence bundle not found: {metric_id}/{bundle_id}")
        return False

    # Verify hash integrity
    if not evidence_system.verify_bundle_integrity(bundle):
        print(f"✗ Bundle integrity check FAILED: hash mismatch")
        return False

    print(f"✓ Bundle integrity verified")

    # Display bundle details
    print(f"\nEvidence Bundle: {bundle_id}")
    print(f"  Metric ID: {metric_id}")
    print(f"  Created: {bundle['created_at']}")
    print(f"  Composite Score: {bundle['composite_score']:.3f}")
    print(f"  Promotion Eligible: {bundle['promotion_eligible']}")
    print(f"  Sample Size: {bundle['sample_size']}")

    print(f"\n  Gates Passed:")
    for gate, passed in bundle["gates_passed"].items():
        symbol = "✓" if passed else "✗"
        print(f"    {symbol} {gate}")

    print(f"\n  Evaluation Outputs:")
    print(f"    Lift (MAE Delta): {bundle['evaluation_outputs']['lift_metrics'].get('mae_delta', 0.0):.3f}")
    print(f"    Redundancy (Max Corr): {bundle['evaluation_outputs']['redundancy_metrics'].get('max_correlation', 0.0):.2f}")
    print(f"    Ablation (Perf Drop): {bundle['evaluation_outputs']['ablation_results'].get('performance_drop', 0.0):.2f}")
    print(f"    Stability (Cycles): {bundle['evaluation_outputs']['stability_results'].get('stable_cycles', 0)}")

    return bundle["promotion_eligible"]


def promote_metric(
    metric_id: str,
    bundle_id: str,
    evidence_dir: Path,
    candidates_path: Path,
    canonical_path: Path,
    promotion_ledger_path: Path,
) -> None:
    """
    Promote a metric from candidate to canonical status.

    CRITICAL: This is the ONLY allowed path for metric promotion.

    Args:
        metric_id: Metric ID to promote
        bundle_id: Evidence bundle ID
        evidence_dir: Evidence directory
        candidates_path: Candidate registry path
        canonical_path: Canonical metrics registry path
        promotion_ledger_path: Promotion ledger path
    """
    print(f"\n{'=' * 80}")
    print(f"Metric Promotion Request: {metric_id}")
    print(f"{'=' * 80}")

    # Step 1: Verify bundle
    print("\n[1/4] Verifying evidence bundle...")
    evidence_system = EvidenceBundle(evidence_dir=evidence_dir)

    try:
        bundle = evidence_system.load_bundle(metric_id, bundle_id)
    except FileNotFoundError:
        print(f"✗ PROMOTION REJECTED: Evidence bundle not found")
        sys.exit(1)

    if not evidence_system.verify_bundle_integrity(bundle):
        print(f"✗ PROMOTION REJECTED: Bundle integrity check failed")
        sys.exit(1)

    if not bundle["promotion_eligible"]:
        print(f"✗ PROMOTION REJECTED: Metric does not meet promotion criteria")
        print(f"  Composite Score: {bundle['composite_score']:.3f}")
        print(f"  Gates Passed: {sum(bundle['gates_passed'].values())}/{len(bundle['gates_passed'])}")
        sys.exit(1)

    print(f"✓ Evidence bundle verified and eligible")

    # Step 2: Load candidate spec
    print("\n[2/4] Loading candidate specification...")
    if not candidates_path.exists():
        print(f"✗ PROMOTION REJECTED: Candidate registry not found")
        sys.exit(1)

    with open(candidates_path, "r") as f:
        candidate_data = json.load(f)

    candidates = candidate_data.get("candidates", [])
    candidate = None
    for c in candidates:
        if c.get("metric_id") == metric_id:
            candidate = c
            break

    if not candidate:
        print(f"✗ PROMOTION REJECTED: Candidate not found in registry")
        sys.exit(1)

    print(f"✓ Candidate spec loaded: {candidate['description'][:50]}...")

    # Step 3: Update registries
    print("\n[3/4] Updating registries...")

    # Mark candidate as MERGED
    candidate["status"] = "MERGED"
    candidate["merged_into"] = metric_id
    candidate["evidence_bundle_hash"] = bundle["bundle_hash"]
    candidate["promoted_at"] = datetime.now(timezone.utc).isoformat()

    # Write updated candidate registry
    with open(candidates_path, "w") as f:
        json.dump(candidate_data, f, indent=2, sort_keys=True, default=str)

    # Add to canonical metrics (load or create)
    canonical_data = {"version": "1.0.0", "metrics": []}
    if canonical_path.exists():
        with open(canonical_path, "r") as f:
            canonical_data = json.load(f)

    canonical_entry = {
        "metric_id": metric_id,
        "description": candidate["description"],
        "inputs": candidate["proposed_inputs"],
        "outputs": candidate["proposed_simvar_targets"],
        "rune_contract": candidate["proposed_rune_contract"],
        "evidence_bundle_hash": bundle["bundle_hash"],
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "composite_score": bundle["composite_score"],
    }

    canonical_data["metrics"].append(canonical_entry)

    # Write canonical registry
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    with open(canonical_path, "w") as f:
        json.dump(canonical_data, f, indent=2, sort_keys=True, default=str)

    print(f"✓ Registries updated")

    # Step 4: Log to promotion ledger
    print("\n[4/4] Recording promotion to ledger...")
    promotion_ledger_path.parent.mkdir(parents=True, exist_ok=True)

    ledger_entry = {
        "type": "promotion",
        "metric_id": metric_id,
        "evidence_bundle_hash": bundle["bundle_hash"],
        "composite_score": bundle["composite_score"],
        "gates_passed": bundle["gates_passed"],
        "promoted_by": "metrics_governance_cli",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    ledger_entry["ledger_sha256"] = hash_canonical_json(ledger_entry)

    with open(promotion_ledger_path, "a") as f:
        f.write(json.dumps(ledger_entry, sort_keys=True, default=str) + "\n")

    print(f"✓ Promotion recorded to ledger")

    # Success
    print(f"\n{'=' * 80}")
    print(f"✓ METRIC PROMOTED SUCCESSFULLY")
    print(f"{'=' * 80}")
    print(f"Metric ID: {metric_id}")
    print(f"Composite Score: {bundle['composite_score']:.3f}")
    print(f"Evidence Bundle: {bundle['bundle_hash'][:16]}...")
    print(f"Status: SHADOW → CANONICAL")
    print(f"{'=' * 80}")


def main():
    """Run metrics governance CLI."""
    parser = argparse.ArgumentParser(
        description="Abraxas Metrics Governance CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List candidates
    list_cmd = subparsers.add_parser("list", help="List candidate metrics")
    list_cmd.add_argument(
        "--candidates",
        type=Path,
        default=Path("registry/metrics_candidate.json"),
        help="Path to candidate registry",
    )

    # List evidence bundles
    evidence_cmd = subparsers.add_parser("evidence", help="List evidence bundles")
    evidence_cmd.add_argument(
        "--evidence-dir", type=Path, default=Path("evidence"), help="Evidence directory"
    )

    # Verify bundle
    verify_cmd = subparsers.add_parser("verify", help="Verify evidence bundle")
    verify_cmd.add_argument("metric_id", help="Metric ID")
    verify_cmd.add_argument("bundle_id", help="Bundle ID")
    verify_cmd.add_argument(
        "--evidence-dir", type=Path, default=Path("evidence"), help="Evidence directory"
    )

    # Promote metric
    promote_cmd = subparsers.add_parser("promote", help="Promote metric to canonical")
    promote_cmd.add_argument("metric_id", help="Metric ID")
    promote_cmd.add_argument("bundle_id", help="Evidence bundle ID")
    promote_cmd.add_argument(
        "--evidence-dir", type=Path, default=Path("evidence"), help="Evidence directory"
    )
    promote_cmd.add_argument(
        "--candidates",
        type=Path,
        default=Path("registry/metrics_candidate.json"),
        help="Candidate registry path",
    )
    promote_cmd.add_argument(
        "--canonical",
        type=Path,
        default=Path("registry/metrics.json"),
        help="Canonical metrics registry path",
    )
    promote_cmd.add_argument(
        "--ledger",
        type=Path,
        default=Path(".aal/ledger/metric_promotions.jsonl"),
        help="Promotion ledger path",
    )

    args = parser.parse_args()

    if args.command == "list":
        list_candidates(args.candidates)
    elif args.command == "evidence":
        list_evidence_bundles(args.evidence_dir)
    elif args.command == "verify":
        verify_bundle(args.metric_id, args.bundle_id, args.evidence_dir)
    elif args.command == "promote":
        promote_metric(
            args.metric_id,
            args.bundle_id,
            args.evidence_dir,
            args.candidates,
            args.canonical,
            args.ledger,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
