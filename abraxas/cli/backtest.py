#!/usr/bin/env python3
"""
Backtest CLI — Deterministic Forecast Evaluation

Evaluates backtest cases against local signal store and ledgers.

Usage:
    python -m abraxas.cli.backtest --cases data/backtests/cases
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from abraxas.backtest.evaluator import evaluate_case, load_backtest_case
from abraxas.backtest.ledger import BacktestLedger
from abraxas.backtest.schema import BacktestStatus


def parse_time_max(time_max_str: str) -> datetime:
    """Parse time_max argument (NOW or ISO timestamp)."""
    if time_max_str.upper() == "NOW":
        return datetime.now(timezone.utc)
    else:
        return datetime.fromisoformat(time_max_str.replace("Z", "+00:00"))


def parse_bool(value: str) -> bool:
    """Parse boolean string."""
    return value.lower() in ("true", "1", "yes", "y")


def generate_backtest_report_md(
    results: list[dict], run_id: str, cases_dir: Path
) -> str:
    """Generate Markdown backtest report."""
    lines = []
    lines.append(f"# Backtest Report: {run_id}")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Cases Directory**: {cases_dir}")
    lines.append("")

    # Summary
    total = len(results)
    hit_count = sum(1 for r in results if r["status"] == "HIT")
    miss_count = sum(1 for r in results if r["status"] == "MISS")
    abstain_count = sum(1 for r in results if r["status"] == "ABSTAIN")
    unknown_count = sum(1 for r in results if r["status"] == "UNKNOWN")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Cases**: {total}")
    lines.append(f"- **HIT**: {hit_count} ({hit_count/total*100:.1f}%)" if total > 0 else "- **HIT**: 0")
    lines.append(f"- **MISS**: {miss_count} ({miss_count/total*100:.1f}%)" if total > 0 else "- **MISS**: 0")
    lines.append(f"- **ABSTAIN**: {abstain_count} ({abstain_count/total*100:.1f}%)" if total > 0 else "- **ABSTAIN**: 0")
    lines.append(f"- **UNKNOWN**: {unknown_count} ({unknown_count/total*100:.1f}%)" if total > 0 else "- **UNKNOWN**: 0")
    lines.append("")

    # Results by case
    lines.append("## Case Results")
    lines.append("")

    for result in results:
        lines.append(f"### {result['case_id']}")
        lines.append("")
        lines.append(f"- **Status**: {result['status']}")
        lines.append(f"- **Score**: {result['score']:.2f}")
        lines.append(f"- **Confidence**: {result['confidence']}")
        lines.append(f"- **Satisfied Triggers**: {', '.join(result['satisfied_triggers']) if result['satisfied_triggers'] else 'None'}")
        lines.append(f"- **Satisfied Falsifiers**: {', '.join(result['satisfied_falsifiers']) if result['satisfied_falsifiers'] else 'None'}")
        lines.append("")

        if result.get("notes"):
            lines.append("**Notes**:")
            for note in result["notes"]:
                lines.append(f"- {note}")
            lines.append("")

    return "\n".join(lines)


def main():
    """Run backtest CLI."""
    parser = argparse.ArgumentParser(
        description="Abraxas Backtest Evaluator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("data/backtests/cases"),
        help="Directory containing backtest case YAML files (default: data/backtests/cases)",
    )

    parser.add_argument(
        "--case-id",
        type=str,
        default=None,
        help="Run specific case only (by case_id)",
    )

    parser.add_argument(
        "--since-days",
        type=int,
        default=None,
        help="Evaluate cases from last N days only",
    )

    parser.add_argument(
        "--time-max",
        type=str,
        default="NOW",
        help="Maximum timestamp for evaluation window (default: NOW)",
    )

    parser.add_argument(
        "--strict",
        type=str,
        default="false",
        help="Require all ledgers exist (default: false)",
    )

    parser.add_argument(
        "--write-ledgers",
        type=str,
        default="true",
        help="Write results to backtest ledger (default: true)",
    )

    parser.add_argument(
        "--emit-reports",
        type=str,
        default="true",
        help="Generate MD/JSON reports (default: true)",
    )

    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=Path("out/backtest_ledgers/backtest_runs.jsonl"),
        help="Path to backtest ledger (default: out/backtest_ledgers/backtest_runs.jsonl)",
    )

    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("out/reports"),
        help="Directory for reports (default: out/reports)",
    )

    args = parser.parse_args()

    # Parse flags
    strict = parse_bool(args.strict)
    write_ledgers = parse_bool(args.write_ledgers)
    emit_reports = parse_bool(args.emit_reports)
    time_max = parse_time_max(args.time_max)

    print("=" * 80)
    print("BACKTEST EVALUATION")
    print("=" * 80)
    print(f"Cases Directory: {args.cases}")
    print(f"Time Max: {time_max.isoformat()}")
    print(f"Strict Mode: {strict}")
    print("")

    # Load cases
    if not args.cases.exists():
        print(f"Error: Cases directory not found: {args.cases}")
        sys.exit(1)

    case_files = list(args.cases.glob("*.yaml")) + list(args.cases.glob("*.yml"))

    if not case_files:
        print(f"Warning: No case files found in {args.cases}")
        sys.exit(0)

    print(f"[1/4] Loading cases...")
    cases = []
    for case_file in case_files:
        try:
            case = load_backtest_case(case_file)

            # Filter by case_id if specified
            if args.case_id and case.case_id != args.case_id:
                continue

            # Filter by since_days if specified
            if args.since_days:
                cutoff = time_max - timedelta(days=args.since_days)
                if case.evaluation_window.start_ts < cutoff:
                    continue

            cases.append(case)
        except Exception as e:
            print(f"Warning: Failed to load {case_file}: {e}")

    print(f"  Loaded {len(cases)} cases")
    print("")

    # Evaluate cases
    print(f"[2/4] Evaluating cases...")
    results = []
    for case in cases:
        try:
            result = evaluate_case(case)
            results.append(result.model_dump())
            print(f"  {case.case_id}: {result.status.value} (score: {result.score:.2f})")
        except Exception as e:
            print(f"  Error evaluating {case.case_id}: {e}")

    print("")

    # Write to ledger
    if write_ledgers:
        print(f"[3/4] Writing to backtest ledger...")
        ledger = BacktestLedger(ledger_path=args.ledger_path)

        backtest_run_id = f"backtest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        for result_dict in results:
            from abraxas.backtest.schema import BacktestResult

            result = BacktestResult(**result_dict)
            ledger.append_result(backtest_run_id, result)

        print(f"  Wrote {len(results)} results to {args.ledger_path}")
        print("")
    else:
        backtest_run_id = f"backtest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    # Generate reports
    if emit_reports:
        print(f"[4/4] Generating reports...")
        args.reports_dir.mkdir(parents=True, exist_ok=True)

        # JSON report
        json_path = args.reports_dir / f"{backtest_run_id}.json"
        with open(json_path, "w") as f:
            json.dump(
                {"backtest_run_id": backtest_run_id, "results": results},
                f,
                indent=2,
                default=str,
            )
        print(f"  JSON report: {json_path}")

        # Markdown report
        md_path = args.reports_dir / f"{backtest_run_id}.md"
        md_content = generate_backtest_report_md(results, backtest_run_id, args.cases)
        with open(md_path, "w") as f:
            f.write(md_content)
        print(f"  MD report: {md_path}")
        print("")

    # Print summary
    print("=" * 80)
    print("BACKTEST EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Cases Evaluated: {len(results)}")

    hit_count = sum(1 for r in results if r["status"] == "HIT")
    miss_count = sum(1 for r in results if r["status"] == "MISS")
    abstain_count = sum(1 for r in results if r["status"] == "ABSTAIN")
    unknown_count = sum(1 for r in results if r["status"] == "UNKNOWN")

    total = len(results)
    if total > 0:
        print(f"  HIT: {hit_count} ({hit_count/total*100:.1f}%)")
        print(f"  MISS: {miss_count} ({miss_count/total*100:.1f}%)")
        print(f"  ABSTAIN: {abstain_count} ({abstain_count/total*100:.1f}%)")
        print(f"  UNKNOWN: {unknown_count} ({unknown_count/total*100:.1f}%)")
        print("")

        # Top failure reasons
        all_notes = []
        for r in results:
            if r["status"] in ["MISS", "ABSTAIN", "UNKNOWN"]:
                all_notes.extend(r.get("notes", []))

        if all_notes:
            print("Top Issues:")
            note_counts = {}
            for note in all_notes:
                # Simplify note for grouping
                simplified = note.split("(")[0].strip() if "(" in note else note
                note_counts[simplified] = note_counts.get(simplified, 0) + 1

            sorted_notes = sorted(note_counts.items(), key=lambda x: x[1], reverse=True)
            for note, count in sorted_notes[:5]:
                print(f"  - {note}: {count}")
            print("")

    if emit_reports:
        print(f"Reports written to: {args.reports_dir}/{backtest_run_id}.{{json,md}}")
    if write_ledgers:
        print(f"Ledger updated: {args.ledger_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
