"""Seed pack CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.seeds.year_seed_2025 import write_seedpack


def run_seed(year: int, out: str) -> int:
    if year != 2025:
        raise SystemExit("Only year 2025 is supported in seedpack v0.1")
    write_seedpack(Path(out))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="abraxas seed", description="Seed pack generator")
    parser.add_argument("--year", type=int, required=True, help="Seed pack year")
    parser.add_argument("--out", required=True, help="Output path")
    args = parser.parse_args()

    return run_seed(args.year, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
