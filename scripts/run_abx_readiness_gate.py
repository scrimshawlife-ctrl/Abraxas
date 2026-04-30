#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.governance.readiness_gate import run_readiness_gate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="out/reports/abx_readiness_gate.latest.json")
    args = parser.parse_args()

    report = run_readiness_gate(args.repo_root)
    out_path = Path(args.out)
    root = Path(args.repo_root).resolve()
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(out_path.as_posix())
    raise SystemExit(0 if report["status"] == "READY" else 1)


if __name__ == "__main__":
    main()
