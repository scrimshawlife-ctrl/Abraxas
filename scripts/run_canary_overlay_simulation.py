#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.canary.sim_runner import build_canary_overlay_simulation_run
from abraxas.core.canonical import canonical_json


def _read(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", required=True)
    parser.add_argument("--forecasts", required=True)
    parser.add_argument("--outcomes", required=True)
    parser.add_argument("--scores", required=True)
    parser.add_argument("--out", default="out/canary/overlay_simulation.latest.json")
    args = parser.parse_args()

    report = build_canary_overlay_simulation_run(
        overlay_run=_read(args.overlay),
        forecast_run=_read(args.forecasts),
        outcome_run=_read(args.outcomes),
        score_run=_read(args.scores),
    )

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(report) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
