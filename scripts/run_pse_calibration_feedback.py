#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.pse.calibration_feedback import build_calibration_feedback


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brier-ledger", default="out/reports/pse_brier_ledger.latest.json")
    parser.add_argument("--readiness", default="out/reports/abx_readiness_gate.latest.json")
    parser.add_argument("--out", default="out/reports/pse_calibration_feedback.latest.json")
    args = parser.parse_args()

    brier = json.loads(Path(args.brier_ledger).read_text(encoding="utf-8"))
    readiness = json.loads(Path(args.readiness).read_text(encoding="utf-8"))
    report = build_calibration_feedback(brier, readiness)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
