from __future__ import annotations

import argparse
import json
from pathlib import Path

from abraxas.oracle.stability.invariance import run_invariance_v2


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Oracle Signal Layer v2 invariance only")
    parser.add_argument("--input", required=True)
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--out", default="out/oracle_signal_layer_v2/invariance_only.json")
    args = parser.parse_args()

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = run_invariance_v2(raw, repeats=args.repeats)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "status": report["status"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
