#!/usr/bin/env python3
"""Graft-powered gap analyzer — query the graft index for binding and residual gaps.

Produces a JSON report mapping each query mode to its top N symbol hits,
with file locations and line spans.

Usage:
    PYTHONPATH=. python3 scripts/graft_gap_analyzer.py --mode binding,residual
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_MODES = frozenset({"binding", "residual"})
DEFAULT_REPORT_PATH = REPO_ROOT / "out" / "reports" / "graft_gap_report.latest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Graft-powered gap analyzer — query the graft index for gap data."
    )
    parser.add_argument(
        "--mode",
        required=True,
        help="Comma-separated query modes: binding,residual",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help=f"Output path for the JSON report (default: {DEFAULT_REPORT_PATH})",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Maximum number of top symbols per mode (default: 10)",
    )
    return parser.parse_args()


def _run_graft_ask(mode: str) -> str:
    """Run `graft ask '<mode> gap' --source` and return stdout."""
    query = f"{mode} gap"
    result = subprocess.run(
        ["graft", "ask", query, "--source"],
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"graft_gap_analyzer: graft ask '{query}' failed (exit {result.returncode}): {result.stderr.strip() or result.stdout.strip()}",
              file=sys.stderr)
        return ""
    return result.stdout


def _parse_graft_output(output: str, top_n: int) -> tuple[list[dict], int]:
    """Parse graft ask --source output into structured symbol entries.

    Returns (top_symbols, total_hits).
    """
    symbols: list[dict] = []
    total_hits = 0

    # graft output format:
    #   N. symbol_name · kind [symbol]
    #      file:Lxx-Lyy
    #      ... code block ...
    #
    # Parse the ranked entry headers.
    entry_pattern = re.compile(
        r"^(\d+)\.\s+(?P<name>\S+)\s+·\s+(?P<kind>\S+)\s+\[symbol\]\s*$",
        re.MULTILINE,
    )
    file_span_pattern = re.compile(
        r"(?P<file>[^\s]+):L(?P<start>\d+)-L(?P<end>\d+)",
    )

    lines = output.splitlines()
    for i, line in enumerate(lines):
        m = entry_pattern.match(line)
        if not m:
            continue
        entry_num = int(m.group(1))
        name = m.group("name")
        kind = m.group("kind")

        # The file span line immediately follows the header
        file_info = ""
        if i + 1 < len(lines):
            fm = file_span_pattern.search(lines[i + 1])
            if fm:
                file_info = f"{fm.group('file')}:L{fm.group('start')}-L{fm.group('end')}"

        symbols.append({
            "rank": entry_num,
            "name": name,
            "kind": kind,
            "file": file_info,
        })

        if entry_num > total_hits:
            total_hits = entry_num

    # Limit to top_n
    return symbols[:top_n], total_hits


def _query_mode(mode: str, top_n: int) -> dict:
    """Run graft query for a single mode and return the section dict."""
    raw = _run_graft_ask(mode)
    if not raw:
        return {"total_hits": 0, "top_symbols": [], "raw_output": ""}

    symbols, total = _parse_graft_output(raw, top_n)
    return {
        "total_hits": total,
        "top_symbols": symbols,
        "query": f"{mode} gap",
    }


def main() -> int:
    args = parse_args()

    modes = [m.strip() for m in args.mode.split(",") if m.strip()]
    if not modes:
        print("graft_gap_analyzer: no modes specified", file=sys.stderr)
        return 1

    for mode in modes:
        if mode not in VALID_MODES:
            print(f"graft_gap_analyzer: unknown mode '{mode}'. Valid modes: {', '.join(sorted(VALID_MODES))}",
                  file=sys.stderr)
            return 1

    report = {
        "schema_version": "GraftGapReport.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_time_ms": 0,
        "modes": {},
    }

    for mode in sorted(VALID_MODES):
        if mode in modes:
            report["modes"][mode] = _query_mode(mode, args.top_n)
        else:
            report["modes"][mode] = {"total_hits": 0, "top_symbols": []}

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())