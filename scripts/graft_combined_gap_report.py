#!/usr/bin/env python3
"""Combined graft + todo scan report. Writes stable artifact."""
from __future__ import annotations
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

def main() -> None:
    out = Path("out/reports/graft_combined_gap_report.latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    # Run analyzer
    subprocess.run(["python3", "scripts/graft_gap_analyzer.py", "--mode", "binding,residual"], check=True)
    # Run todo
    subprocess.run(["python3", "scripts/scan_todo_markers.py", "--repo-root", ".", "--out", "out/reports/todo_markers.latest.json"], check=True)
    report = {
        "schema_version": "GraftCombinedGap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analyzer_report": json.loads(Path("out/reports/graft_gap_report.latest.json").read_text()),
        "todo_report": json.loads(Path("out/reports/todo_markers.latest.json").read_text()),
    }
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()