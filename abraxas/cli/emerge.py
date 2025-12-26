#!/usr/bin/env python3
"""
Metric Emergence CLI

Command-line interface for running metric emergence discovery.

Usage:
    python -m abraxas.cli.emerge --from-ledger START_HASH:END_HASH
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from abraxas.metrics.emergence import MetricEmergence


def parse_hash_range(hash_range_str: str) -> tuple[str, str]:
    """
    Parse hash range from START_HASH:END_HASH format.

    Args:
        hash_range_str: Hash range string

    Returns:
        Tuple of (start_hash, end_hash)
    """
    parts = hash_range_str.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid hash range format: {hash_range_str}. Expected START_HASH:END_HASH"
        )
    return (parts[0], parts[1])


def main():
    """Run metric emergence CLI."""
    parser = argparse.ArgumentParser(
        description="Abraxas Metric Emergence Discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--from-ledger",
        type=str,
        required=True,
        help="Hash range for ledger slice (START_HASH:END_HASH)",
    )

    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=Path(".aal/ledger/outcomes.jsonl"),
        help="Path to outcome ledger (default: .aal/ledger/outcomes.jsonl)",
    )

    parser.add_argument(
        "--canonical-metrics",
        type=Path,
        default=Path("registry/metrics.json"),
        help="Path to canonical metrics registry (default: registry/metrics.json)",
    )

    parser.add_argument(
        "--runes-registry",
        type=Path,
        default=Path("abraxas/runes/registry.json"),
        help="Path to runes registry (default: abraxas/runes/registry.json)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("registry/metrics_candidate.json"),
        help="Output path for candidate registry (default: registry/metrics_candidate.json)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum ledger entries to analyze (default: 1000)",
    )

    args = parser.parse_args()

    # Parse hash range
    try:
        hash_range = parse_hash_range(args.from_ledger)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    start_hash, end_hash = hash_range

    print("=" * 80)
    print("METRIC EMERGENCE DISCOVERY")
    print("=" * 80)
    print(f"Ledger: {args.ledger_path}")
    print(f"Hash Range: {start_hash[:16]}... → {end_hash[:16]}...")
    print(f"Limit: {args.limit} entries")
    print(f"Output: {args.output}")
    print("")

    # Initialize emergence system
    emergence = MetricEmergence(
        ledger_path=args.ledger_path,
        canonical_metrics_path=args.canonical_metrics,
        runes_registry_path=args.runes_registry,
        output_path=args.output,
    )

    # Run emergence
    print("[1/3] Loading ledger slice...")
    try:
        candidates = emergence.run_emergence(hash_range=hash_range, limit=args.limit)
    except Exception as e:
        print(f"✗ Error during emergence: {e}")
        sys.exit(1)

    print(f"✓ Analyzed ledger entries")
    print("")

    # Display discovered candidates
    print("[2/3] Discovered candidate metrics:")
    if not candidates:
        print("  (No candidates discovered)")
    else:
        for candidate in candidates:
            metric_id = candidate["metric_id"]
            hypothesis = candidate["hypothesis_type"]
            description = candidate["description"]
            print(f"  • {metric_id}")
            print(f"    Hypothesis: {hypothesis}")
            print(f"    Description: {description}")
            print("")

    # Write candidates
    print("[3/3] Writing candidates to registry...")
    try:
        emergence.write_candidates(candidates)
        print(f"✓ {len(candidates)} candidates written to {args.output}")
    except Exception as e:
        print(f"✗ Error writing candidates: {e}")
        sys.exit(1)

    print("")
    print("=" * 80)
    print(f"EMERGENCE COMPLETE")
    print("=" * 80)
    print(f"Proposed Metrics: {len(candidates)}")
    print(f"Status: All candidates are PROPOSED (shadow-only)")
    print("")
    print("Next steps:")
    print("  1. Review candidates: python -m abraxas.cli.metrics_governance list")
    print("  2. Evaluate candidates (run shadow metrics, collect evidence)")
    print("  3. Promote via governance: python -m abraxas.cli.metrics_governance promote")
    print("=" * 80)


if __name__ == "__main__":
    main()
