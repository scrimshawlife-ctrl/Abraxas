#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.viz.webgl_render_runner import run_render_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="out/viz/webgl_render_bundle.latest.json")
    args = parser.parse_args()
    run_render_bundle(input_path=Path(args.input), out_path=Path(args.out))


if __name__ == "__main__":
    main()
