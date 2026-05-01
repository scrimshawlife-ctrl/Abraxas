#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.viz.svg_ledger_runner import run_svg_artifact_ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--previous", default=None)
    parser.add_argument("--out", default="out/viz/svg_artifact_ledger.latest.json")
    args = parser.parse_args()
    prev = Path(args.previous) if args.previous else None
    run_svg_artifact_ledger(manifest_path=Path(args.manifest), previous_path=prev, out_path=Path(args.out))


if __name__ == "__main__":
    main()
