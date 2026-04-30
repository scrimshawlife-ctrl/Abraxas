#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.pse.outcome_tracker import build_outcome_ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--outcomes", required=True)
    parser.add_argument("--out", default="out/reports/pse_outcome_ledger.latest.json")
    args = parser.parse_args()

    predictions = json.loads(Path(args.predictions).read_text(encoding="utf-8"))
    outcomes = json.loads(Path(args.outcomes).read_text(encoding="utf-8"))
    if not isinstance(predictions, list):
        predictions = []
    if not isinstance(outcomes, list):
        outcomes = []

    ledger = build_outcome_ledger(predictions, outcomes)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ledger, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
