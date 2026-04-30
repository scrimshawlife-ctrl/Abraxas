#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.pse.calibration_candidate_apply import apply_candidate_proposal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", default="out/reports/pse_calibration_candidate_proposal.latest.json")
    parser.add_argument("--approval-gate", default="out/reports/pse_calibration_candidate_approval_gate.latest.json")
    parser.add_argument("--readiness", default="out/reports/abx_readiness_gate.latest.json")
    parser.add_argument("--state-out", default="out/state/pse_calibration_candidate_state.latest.json")
    parser.add_argument("--rollback-out", default="out/state/rollback/pse_calibration_candidate_state.previous.json")
    parser.add_argument("--report-out", default="out/reports/pse_calibration_candidate_application.latest.json")
    args = parser.parse_args()

    proposal = json.loads((REPO_ROOT / args.proposal).read_text(encoding="utf-8"))
    approval = json.loads((REPO_ROOT / args.approval_gate).read_text(encoding="utf-8"))
    readiness = json.loads((REPO_ROOT / args.readiness).read_text(encoding="utf-8"))

    report = apply_candidate_proposal(
        proposal=proposal,
        approval_gate=approval,
        readiness=readiness,
        state_out=REPO_ROOT / args.state_out,
        rollback_out=REPO_ROOT / args.rollback_out,
    )

    out_path = REPO_ROOT / args.report_out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
