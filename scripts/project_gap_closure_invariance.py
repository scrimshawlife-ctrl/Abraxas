from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.gap_closure_invariance import project_gap_closure_invariance, read_gap_closure_invariance_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Project gap-closure invariance into normalized schema.")
    parser.add_argument(
        "--in",
        dest="input_path",
        type=Path,
        default=Path("out/reports/gap_closure_stabilization_report.json"),
        help="Path to gap-closure stabilization report",
    )
    parser.add_argument(
        "--out",
        dest="output_path",
        type=Path,
        default=Path("out/reports/gap_closure_invariance.projection.json"),
        help="Output projection path",
    )
    args = parser.parse_args()

    payload = read_gap_closure_invariance_payload(args.input_path)
    if payload["raw"] is None:
        projection = payload["projection"]
    else:
        projection = project_gap_closure_invariance(payload["raw"], source_path=args.input_path)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"gap-closure invariance projection written: {args.output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
