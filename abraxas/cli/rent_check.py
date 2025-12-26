#!/usr/bin/env python3
"""
Rent Check CLI — Enforce "Complexity Must Pay Rent"

Usage:
    python -m abraxas.cli.rent_check [OPTIONS]

Options:
    --manifests PATH        Path to rent_manifests directory (default: data/rent_manifests)
    --strict BOOL           Strict mode: fail on any validation error (default: true)
    --print-json BOOL       Print report as JSON (default: false)
    --fail-on-warnings BOOL Fail if warnings exist (default: false)
    --output DIR            Output directory for reports (default: out/reports)

Exit codes:
    0: All checks passed
    1: Validation failures or errors
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from abraxas.governance.rent_manifest_loader import (
    load_all_manifests,
    validate_manifest,
    ManifestValidationError,
    get_manifest_summary,
)
from abraxas.governance.rent_checks import (
    run_all_rent_checks,
    format_report_console,
    format_report_markdown,
)


def parse_bool(value: str) -> bool:
    """Parse boolean string."""
    return value.lower() in ("true", "1", "yes", "y")


def main():
    parser = argparse.ArgumentParser(
        description="Rent Enforcement Check — Validate that complexity pays rent"
    )
    parser.add_argument(
        "--manifests",
        type=str,
        default=None,
        help="Path to rent_manifests directory (default: auto-detect from repo root)",
    )
    parser.add_argument(
        "--strict",
        type=str,
        default="true",
        help="Strict mode: fail on any validation error (default: true)",
    )
    parser.add_argument(
        "--print-json",
        type=str,
        default="false",
        help="Print report as JSON to stdout (default: false)",
    )
    parser.add_argument(
        "--fail-on-warnings",
        type=str,
        default="false",
        help="Fail if warnings exist (default: false)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="out/reports",
        help="Output directory for reports (default: out/reports)",
    )

    args = parser.parse_args()

    # Parse boolean flags
    strict = parse_bool(args.strict)
    print_json = parse_bool(args.print_json)
    fail_on_warnings = parse_bool(args.fail_on_warnings)

    # Determine repo root (assume we're in abraxas/cli/)
    repo_root = Path(__file__).parent.parent.parent.resolve()

    # Determine manifests directory
    if args.manifests:
        manifests_dir = Path(args.manifests)
    else:
        manifests_dir = repo_root / "data" / "rent_manifests"

    # Check if manifests directory exists
    if not manifests_dir.exists():
        print(f"Error: Manifests directory does not exist: {manifests_dir}")
        print(
            f"Create the directory or use --manifests to specify the correct location."
        )
        sys.exit(1)

    print("=" * 60)
    print("RENT ENFORCEMENT CHECK")
    print("=" * 60)
    print(f"Repo root: {repo_root}")
    print(f"Manifests: {manifests_dir}")
    print(f"Strict mode: {strict}")
    print(f"Fail on warnings: {fail_on_warnings}")
    print("")

    # Step 1: Load manifests
    print("Loading manifests...")
    try:
        manifests = load_all_manifests(str(repo_root))
    except Exception as e:
        print(f"Error loading manifests: {e}")
        sys.exit(1)

    summary = get_manifest_summary(manifests)
    print(f"  Loaded {summary['total_manifests']} manifests:")
    print(f"    - Metrics: {summary['by_kind']['metrics']}")
    print(f"    - Operators: {summary['by_kind']['operators']}")
    print(f"    - Artifacts: {summary['by_kind']['artifacts']}")
    print("")

    # Step 2: Validate manifests
    print("Validating manifest schemas...")
    validation_errors = []
    all_manifests = []
    for kind in ["metrics", "operators", "artifacts"]:
        all_manifests.extend(manifests.get(kind, []))

    for manifest in all_manifests:
        manifest_id = manifest.get("id", "unknown")
        try:
            validate_manifest(manifest)
        except ManifestValidationError as e:
            validation_errors.append({"manifest_id": manifest_id, "error": str(e)})

    if validation_errors:
        print(f"  ✗ Validation failed for {len(validation_errors)} manifests:")
        for err in validation_errors:
            print(f"    - [{err['manifest_id']}] {err['error']}")
        if strict:
            print("")
            print("Validation failed. Fix errors and try again.")
            sys.exit(1)
    else:
        print("  ✓ All manifests valid")
    print("")

    # Step 3: Run rent checks
    print("Running rent checks...")
    report = run_all_rent_checks(manifests, str(repo_root))

    # Step 4: Output results
    if print_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_report_console(report))

    # Step 5: Save reports
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Save JSON report
    json_path = output_dir / f"rent_check_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"JSON report saved to: {json_path}")

    # Save Markdown report
    md_path = output_dir / f"rent_check_{timestamp}.md"
    with open(md_path, "w") as f:
        f.write(format_report_markdown(report))
    print(f"Markdown report saved to: {md_path}")
    print("")

    # Step 6: Determine exit code
    exit_code = 0

    if not report.passed:
        print("RESULT: FAILED ✗")
        exit_code = 1
    elif fail_on_warnings and report.warnings:
        print(f"RESULT: FAILED (warnings exist) ✗")
        exit_code = 1
    else:
        print("RESULT: PASSED ✓")
        exit_code = 0

    print("")
    print("No manifest, no merge.")
    print("Complexity must pay rent.")
    print("=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
