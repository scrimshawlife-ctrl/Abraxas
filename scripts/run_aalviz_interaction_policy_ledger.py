#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.viz.interaction_policy_ledger_runner import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", default="out/viz/interaction_policy_ledger.latest.json")
    parser.add_argument("--prior", default=None)
    args = parser.parse_args()
    run(Path(args.policy), Path(args.manifest), Path(args.out), Path(args.prior) if args.prior else None)


if __name__ == "__main__":
    main()
