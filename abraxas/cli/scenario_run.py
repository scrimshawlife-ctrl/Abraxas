"""
CLI: Scenario Run

Command-line interface for scenario envelope runner.
Loads priors, executes scenarios, writes cascade sheets and contamination advisories.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.artifacts.scenario_cascade_sheet import generate_scenario_cascade_sheet
from abraxas.artifacts.scenario_contamination_advisory import (
    generate_scenario_contamination_advisory,
)
from abraxas.scenario.runner import run_scenarios
from abraxas.sod.runner import run_sod_bundle


def load_last_snapshot(snapshot_path: Path) -> Optional[Dict[str, Any]]:
    """Load last scenario snapshot if exists."""
    if not snapshot_path.exists():
        return None

    try:
        with open(snapshot_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_snapshot(snapshot_path: Path, data: Dict[str, Any]) -> None:
    """Save scenario snapshot."""
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with open(snapshot_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def has_changed(current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> bool:
    """Check if current result differs from previous (deterministic comparison)."""
    if previous is None:
        return True

    # Compare envelope outputs (simple hash-based comparison)
    current_hash = hash(json.dumps(current, sort_keys=True))
    previous_hash = hash(json.dumps(previous, sort_keys=True))

    return current_hash != previous_hash


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_latest_json(directory: Path, pattern: str) -> Optional[Dict[str, Any]]:
    if not directory.exists():
        return None
    candidates = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    return load_json_file(candidates[0])


def main():
    """Run scenario envelope analysis."""
    parser = argparse.ArgumentParser(
        description="Abraxas Scenario Envelope Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--paper_ids",
        type=str,
        help="Comma-separated paper IDs (e.g., PMC12281847,PMC10250073)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "md", "both"],
        default="both",
        help="Output format",
    )
    parser.add_argument(
        "--delta_only",
        type=str,
        choices=["true", "false"],
        default="true",
        help="Only write if changed from last run",
    )
    parser.add_argument(
        "--mri", type=float, help="Override MRI (Memetic Resonance Index, [0,1])"
    )
    parser.add_argument(
        "--iri", type=float, help="Override IRI (Intervention Responsiveness Index, [0,1])"
    )
    parser.add_argument(
        "--tau_latency", type=float, help="Override tau_latency ([0,1])"
    )
    parser.add_argument(
        "--tau_memory", type=float, help="Override tau_memory ([0,1])"
    )
    parser.add_argument(
        "--tier",
        type=str,
        choices=["psychonaut", "analyst", "enterprise"],
        default="psychonaut",
        help="Skepticism mode tier for contamination advisory",
    )
    parser.add_argument(
        "--focus_cluster",
        type=str,
        help="Optional cluster to focus cascade sheet on",
    )
    parser.add_argument(
        "--weather_snapshot",
        type=Path,
        help="Path to weather report JSON (defaults to latest out/reports/weather_report_*.json)",
    )
    parser.add_argument(
        "--dm_snapshot",
        type=Path,
        help="Path to D/M metrics snapshot JSON (defaults to data/runs/dm_snapshot.json)",
    )
    parser.add_argument(
        "--almanac_snapshot",
        type=Path,
        help="Path to almanac snapshot JSON (defaults to data/almanac/almanac_snapshot.json)",
    )

    args = parser.parse_args()

    # Build simulation priors
    # In future, these would come from paper registry + mapping table
    # For now, use CLI overrides or defaults
    base_priors = {
        "MRI": args.mri if args.mri is not None else 0.5,
        "IRI": args.iri if args.iri is not None else 0.5,
        "tau_memory": args.tau_memory if args.tau_memory is not None else 0.5,
        "tau_latency": args.tau_latency if args.tau_latency is not None else 0.3,
    }

    weather_snapshot = (
        load_json_file(args.weather_snapshot)
        if args.weather_snapshot
        else load_latest_json(Path("out/reports"), "weather_report_*.json")
    )
    dm_snapshot = (
        load_json_file(args.dm_snapshot)
        if args.dm_snapshot
        else load_json_file(Path("data/runs/dm_snapshot.json"))
    )
    almanac_snapshot = (
        load_json_file(args.almanac_snapshot)
        if args.almanac_snapshot
        else load_json_file(Path("data/almanac/almanac_snapshot.json"))
    )

    # Build context
    run_id = f"scenario_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    context = {
        "run_id": run_id,
        "paper_ids": args.paper_ids.split(",") if args.paper_ids else [],
        "source_count": len(args.paper_ids.split(",")) if args.paper_ids else 0,
        "weather": weather_snapshot,
        "dm_snapshot": dm_snapshot,
        "almanac_snapshot": almanac_snapshot,
    }

    # Run scenario envelope runner
    print(f"Running scenario envelope analysis: {run_id}")
    print(f"Base priors: {base_priors}")

    result = run_scenarios(
        base_priors=base_priors,
        sod_runner=run_sod_bundle,
        context=context,
    )

    print(f"✓ Generated {len(result.envelopes)} envelopes")

    # Delta-only check
    delta_only = args.delta_only == "true"
    snapshot_path = Path("data/runs/last_scenario_snapshot.json")
    last_snapshot = load_last_snapshot(snapshot_path) if delta_only else None

    result_dict = result.to_dict()

    if delta_only and not has_changed(result_dict, last_snapshot):
        print("✓ No changes detected (delta_only=true). Skipping write.")
        sys.exit(0)

    # Create output directory
    output_dir = Path(f"out/scenarios/{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write scenario result JSON
    result_path = output_dir / "scenario_result.json"
    with open(result_path, "w") as f:
        json.dump(result_dict, f, indent=2, sort_keys=True)
    print(f"✓ Wrote scenario result: {result_path}")

    # Generate cascade sheet
    cascade_outputs = generate_scenario_cascade_sheet(
        result=result,
        focus_cluster=args.focus_cluster,
        format=args.format,
    )

    if "json" in cascade_outputs:
        cascade_json_path = output_dir / "cascade_sheet.json"
        with open(cascade_json_path, "w") as f:
            f.write(cascade_outputs["json"])
        print(f"✓ Wrote cascade sheet JSON: {cascade_json_path}")

    if "md" in cascade_outputs:
        cascade_md_path = output_dir / "cascade_sheet.md"
        with open(cascade_md_path, "w") as f:
            f.write(cascade_outputs["md"])
        print(f"✓ Wrote cascade sheet MD: {cascade_md_path}")

    # Generate contamination advisory
    advisory_outputs = generate_scenario_contamination_advisory(
        dm_snapshot=context.get("dm_snapshot"),
        sim_priors=base_priors,
        weather=context.get("weather"),
        tier=args.tier,
        format=args.format,
    )

    if "json" in advisory_outputs:
        advisory_json_path = output_dir / "contamination_advisory.json"
        with open(advisory_json_path, "w") as f:
            f.write(advisory_outputs["json"])
        print(f"✓ Wrote contamination advisory JSON: {advisory_json_path}")

    if "md" in advisory_outputs:
        advisory_md_path = output_dir / "contamination_advisory.md"
        with open(advisory_md_path, "w") as f:
            f.write(advisory_outputs["md"])
        print(f"✓ Wrote contamination advisory MD: {advisory_md_path}")

    # Save snapshot for delta comparison
    if delta_only:
        save_snapshot(snapshot_path, result_dict)
        print(f"✓ Saved snapshot: {snapshot_path}")

    print(f"\n✓ Scenario run complete: {run_id}")


if __name__ == "__main__":
    main()
