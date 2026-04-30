#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.pse.calibration_apply import apply_calibration_proposal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", default="out/reports/pse_calibration_application_proposal.latest.json")
    parser.add_argument("--approval-gate", default="out/reports/pse_calibration_approval_gate.latest.json")
    parser.add_argument("--readiness", default="out/reports/abx_readiness_gate.latest.json")
    parser.add_argument("--state-out", default="out/state/pse_calibration_state.latest.json")
    parser.add_argument("--rollback-out", default="out/state/rollback/pse_calibration_state.previous.json")
    parser.add_argument("--report-out", default="out/reports/pse_calibration_application.latest.json")
    parser.add_argument("--timestamp", default="1970-01-01T00:00:00Z")
    parser.add_argument("--rerun-readiness", default="true")
    args = parser.parse_args()

    repo_root = REPO_ROOT
    proposal = json.loads((repo_root / args.proposal).read_text(encoding="utf-8"))
    approval_gate = json.loads((repo_root / args.approval_gate).read_text(encoding="utf-8"))
    readiness = json.loads((repo_root / args.readiness).read_text(encoding="utf-8"))

    report = apply_calibration_proposal(
        readiness=readiness,
        proposal=proposal,
        approval_gate=approval_gate,
        state_out=repo_root / args.state_out,
        rollback_out=repo_root / args.rollback_out,
        timestamp=args.timestamp,
    )

    report_path = repo_root / args.report_out
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report_path.as_posix())


if __name__ == "__main__":
    main()
