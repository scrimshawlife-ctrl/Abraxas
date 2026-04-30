#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.pse.calibration_runtime_wiring import enable_runtime_wiring


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-state", default="out/state/pse_calibration_candidate_state.latest.json")
    parser.add_argument("--activation-review", default="out/reports/pse_calibration_activation_review.latest.json")
    parser.add_argument("--readiness", default="out/reports/abx_readiness_gate.latest.json")
    parser.add_argument("--wiring-out", default="out/state/pse_calibration_runtime_wiring.latest.json")
    parser.add_argument("--rollback-out", default="out/state/rollback/pse_calibration_runtime_wiring.previous.json")
    parser.add_argument("--report-out", default="out/reports/pse_calibration_runtime_wiring.latest.json")
    args = parser.parse_args()

    candidate_state = json.loads((REPO_ROOT / args.candidate_state).read_text(encoding="utf-8"))
    activation_review = json.loads((REPO_ROOT / args.activation_review).read_text(encoding="utf-8"))
    readiness = json.loads((REPO_ROOT / args.readiness).read_text(encoding="utf-8"))

    report = enable_runtime_wiring(
        candidate_state=candidate_state,
        activation_review=activation_review,
        readiness=readiness,
        wiring_out=REPO_ROOT / args.wiring_out,
        rollback_out=REPO_ROOT / args.rollback_out,
    )

    out_path = REPO_ROOT / args.report_out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
