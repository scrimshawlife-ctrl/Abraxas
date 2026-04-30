#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.pse.calibration_post_activation_validation import run_post_activation_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", default="fixtures/pse/scoreable_predictions.v1.json")
    parser.add_argument("--outcomes", default="fixtures/pse/scoreable_outcomes.v1.json")
    parser.add_argument("--wiring-state", default="out/state/pse_calibration_runtime_wiring.latest.json")
    parser.add_argument("--wiring-report", default="out/reports/pse_calibration_runtime_wiring.latest.json")
    parser.add_argument("--readiness", default="out/reports/abx_readiness_gate.latest.json")
    parser.add_argument("--out", default="out/reports/pse_calibration_post_activation_validation.latest.json")
    args = parser.parse_args()

    predictions = json.loads((REPO_ROOT / args.predictions).read_text(encoding="utf-8"))
    outcomes = json.loads((REPO_ROOT / args.outcomes).read_text(encoding="utf-8"))
    wiring_state = json.loads((REPO_ROOT / args.wiring_state).read_text(encoding="utf-8"))
    wiring_report = json.loads((REPO_ROOT / args.wiring_report).read_text(encoding="utf-8"))
    readiness = json.loads((REPO_ROOT / args.readiness).read_text(encoding="utf-8"))

    report = run_post_activation_validation(predictions, outcomes, wiring_state, wiring_report, readiness)

    out_path = REPO_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
