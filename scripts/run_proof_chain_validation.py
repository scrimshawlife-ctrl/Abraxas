#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.operator_console import dispatch_operator_command


def main() -> int:
    ap = argparse.ArgumentParser(description="Run simulation proof-chain validation")
    ap.add_argument("scenario_json", help="Path to scenario payload json")
    args = ap.parse_args()

    payload = json.loads(Path(args.scenario_json).read_text(encoding="utf-8"))
    output = dispatch_operator_command("run-simulation", payload)
    print(json.dumps(output, indent=2, sort_keys=True))

    status = ((output.get("proof_chain") or {}).get("status") or "").upper()
    return 0 if status == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
