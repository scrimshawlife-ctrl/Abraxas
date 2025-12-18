"""CLI interface for OAS (Operator Auto-Synthesis) pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from abraxas.core.registry import OperatorRegistry
from abraxas.decodo.models import DecodoEvent
from abraxas.oasis.canonizer import OASCanonizer
from abraxas.oasis.collector import OASCollector
from abraxas.oasis.ledger import OASLedger
from abraxas.oasis.miner import OASMiner
from abraxas.oasis.proposer import OASProposer
from abraxas.oasis.stabilizer import OASStabilizer
from abraxas.oasis.validator import OASValidator
from abraxas.slang.engine import SlangEngine
from abraxas.slang.operators.builtin_ctd import CTDOperator


def load_config() -> dict[str, Any]:
    """Load OAS configuration."""
    config_path = Path(".aal/config/oasis.yaml")

    # Default config
    default_config = {
        "stabilization_cycles_required": 3,
        "min_entropy_delta": -0.05,
        "min_false_cringe_delta": -0.10,
        "max_time_regression_pct": 10,
        "quarantine_mode": True,
    }

    if not config_path.exists():
        return default_config

    # For simplicity, we'll use JSON instead of YAML (avoid extra dependency)
    # In production, would use yaml library
    try:
        import yaml

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return {**default_config, **config}
    except ImportError:
        # Fallback to JSON
        json_path = Path(".aal/config/oasis.json")
        if json_path.exists():
            with open(json_path, "r") as f:
                config = json.load(f)
            return {**default_config, **config}
        return default_config


def run_pipeline(
    start: str | None = None,
    end: str | None = None,
    sources: list[str] | None = None,
    input_file: str | None = None,
) -> dict[str, Any]:
    """
    Run the full OAS pipeline.

    Args:
        start: Start timestamp filter
        end: End timestamp filter
        sources: Source filters
        input_file: Input JSON file with events

    Returns:
        Summary of pipeline execution
    """
    print("🔧 Initializing OAS Pipeline...")

    # Load configuration
    config = load_config()
    print(f"📋 Config: {config}")

    # Initialize components
    collector = OASCollector()
    miner = OASMiner()
    proposer = OASProposer()
    validator = OASValidator(
        min_entropy_delta=config["min_entropy_delta"],
        min_false_cringe_delta=config["min_false_cringe_delta"],
    )
    stabilizer = OASStabilizer(cycles_required=config["stabilization_cycles_required"])
    registry = OperatorRegistry()
    canonizer = OASCanonizer(registry=registry)
    ledger = OASLedger()
    engine = SlangEngine(enable_oasis=True)

    print("✅ Components initialized")

    # Load events
    print("📥 Loading events...")
    if input_file:
        with open(input_file, "r") as f:
            event_dicts = json.load(f)
        events = [DecodoEvent(**e) for e in event_dicts]
    else:
        # In production, would fetch from Decodo API
        print("⚠️  No input file specified. Using empty event list.")
        events = []

    print(f"   Loaded {len(events)} events")

    # Collect frames
    print("🎯 Collecting ResonanceFrames...")
    frames = collector.collect_from_events(events)
    print(f"   Generated {len(frames)} frames")

    # Detect clusters
    print("🔍 Detecting slang clusters...")
    clusters = engine.detect_clusters(frames)
    print(f"   Detected {len(clusters)} clusters")

    # Mine patterns
    print("⛏️  Mining patterns...")
    patterns = miner.mine(clusters, frames)
    print(f"   Mined {len(patterns)} patterns")

    # Propose candidates
    print("💡 Proposing operator candidates...")
    candidates = proposer.propose(patterns, clusters, frames)
    print(f"   Proposed {len(candidates)} candidates")

    # Validate and stabilize
    print("✓ Validating candidates...")
    adopted = 0
    rejected = 0
    staging = 0

    for candidate in candidates:
        print(f"   Candidate: {candidate.operator_id} ({candidate.label})")

        # Validate
        report = validator.validate(candidate, frames, engine.operators)

        if not report.passed:
            print(f"      ❌ Validation failed")
            decision = canonizer._reject(candidate, "Validation failed", report.metrics_after)
            rejected += 1
            continue

        print(f"      ✓ Validation passed")

        # Check stability
        stab_state = stabilizer.check_stability(candidate, [report])

        if not stab_state.stable:
            print(
                f"      ⏳ Not yet stable ({stab_state.cycles_completed}/{stab_state.cycles_required})"
            )
            staging += 1
            continue

        print(f"      ✓ Stable")

        # Canonize
        decision = canonizer.canonize(candidate, report, stab_state)

        if decision.adopted:
            print(f"      ✅ ADOPTED as canonical")
            adopted += 1
        else:
            print(f"      ❌ Rejected: {decision.reason}")
            rejected += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Events:            {len(events)}")
    print(f"Frames:            {len(frames)}")
    print(f"Clusters:          {len(clusters)}")
    print(f"Patterns:          {len(patterns)}")
    print(f"Candidates:        {len(candidates)}")
    print(f"Adopted:           {adopted}")
    print(f"Rejected:          {rejected}")
    print(f"Staging:           {staging}")
    print("=" * 60)

    # Ledger summary
    ledger_summary = ledger.get_summary()
    print(f"\n📖 Ledger: {ledger_summary['total_entries']} entries")
    print(f"   Adoptions: {ledger_summary['adoptions']}")
    print(f"   Rejections: {ledger_summary['rejections']}")

    return {
        "events": len(events),
        "frames": len(frames),
        "clusters": len(clusters),
        "patterns": len(patterns),
        "candidates": len(candidates),
        "adopted": adopted,
        "rejected": rejected,
        "staging": staging,
        "ledger": ledger_summary,
    }


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OAS (Operator Auto-Synthesis) Pipeline CLI"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run OAS pipeline")
    run_parser.add_argument("--start", help="Start timestamp filter")
    run_parser.add_argument("--end", help="End timestamp filter")
    run_parser.add_argument("--sources", nargs="+", help="Source filters")
    run_parser.add_argument("--input", help="Input JSON file with events")

    # Ledger command
    ledger_parser = subparsers.add_parser("ledger", help="Inspect OAS ledger")
    ledger_parser.add_argument(
        "--summary", action="store_true", help="Show ledger summary"
    )
    ledger_parser.add_argument("--tail", type=int, help="Show last N entries")

    # Registry command
    registry_parser = subparsers.add_parser("registry", help="Inspect operator registry")
    registry_parser.add_argument(
        "--status", choices=["canonical", "staging", "legacy", "deprecated"], help="Filter by status"
    )

    args = parser.parse_args()

    if args.command == "run":
        try:
            run_pipeline(
                start=args.start, end=args.end, sources=args.sources, input_file=args.input
            )
            return 0
        except Exception as e:
            print(f"❌ Pipeline failed: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            return 1

    elif args.command == "ledger":
        ledger = OASLedger()
        if args.summary:
            summary = ledger.get_summary()
            print(json.dumps(summary, indent=2))
        elif args.tail:
            entries = ledger.read_all()
            for entry in entries[-args.tail :]:
                print(json.dumps(entry, indent=2))
        else:
            entries = ledger.read_all()
            print(f"Total entries: {len(entries)}")
        return 0

    elif args.command == "registry":
        registry = OperatorRegistry()
        if args.status:
            entries = registry.registry.list_by_status(args.status)
            print(f"Operators with status '{args.status}': {len(entries)}")
            for entry in entries:
                print(f"  - {entry.item_id} (v{entry.version})")
        else:
            print(f"Total operators: {len(registry.registry.entries)}")
            for entry in registry.registry.entries.values():
                print(f"  - {entry.item_id} (v{entry.version}, {entry.status})")
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
