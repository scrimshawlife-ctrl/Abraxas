#!/usr/bin/env python3
"""Combined graft + todo scan report. Writes stable artifact."""
from __future__ import annotations
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PREFLIGHT_PATH = Path("out/reports/promotion_preflight.latest.json")


def _load_promotion_preflight() -> dict:
    if not PREFLIGHT_PATH.exists():
        return {"status": "NOT_COMPUTABLE", "reason": "report_missing"}
    try:
        return json.loads(PREFLIGHT_PATH.read_text())
    except Exception:
        return {"status": "NOT_COMPUTABLE", "reason": "report_unreadable"}


def main() -> None:
    out = Path("out/reports/graft_combined_gap_report.latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    # Run analyzer
    subprocess.run(["python3", "scripts/graft_gap_analyzer.py", "--mode", "binding,residual"], check=True)
    # Run todo
    subprocess.run(["python3", "scripts/scan_todo_markers.py", "--repo-root", ".", "--out", "out/reports/todo_markers.latest.json"], check=True)
    # Promotion preflight: produce validator/attestation artifacts for readiness
    subprocess.run(["python3", "scripts/generate_promotion_preflight.py"], check=True)
    # Graft is the default for gap discovery in promotion and BETA paths
    graft_promo = subprocess.check_output(
        ["graft", "ask", "promotion or beta gaps", "--source"], text=True
    )
    report = {
        "schema_version": "GraftCombinedGap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analyzer_report": json.loads(Path("out/reports/graft_gap_report.latest.json").read_text()),
        "todo_report": json.loads(Path("out/reports/todo_markers.latest.json").read_text()),
        "promotion_preflight": _load_promotion_preflight(),
        "graft_promotion_hits": graft_promo[:500],
    }
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()