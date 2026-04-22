from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.developer_readiness import project_developer_readiness


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize developer readiness report into projection schema.")
    parser.add_argument(
        "--in",
        dest="input_path",
        type=Path,
        default=Path("out/reports/developer_readiness.json"),
        help="Path to raw developer readiness report",
    )
    parser.add_argument(
        "--out",
        dest="output_path",
        type=Path,
        default=Path("out/reports/developer_readiness.projection.json"),
        help="Path to write normalized projection",
    )
    args = parser.parse_args()

    raw = json.loads(args.input_path.read_text(encoding="utf-8"))
    projection = project_developer_readiness(raw)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(projection, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"developer-readiness projection written: {args.output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
