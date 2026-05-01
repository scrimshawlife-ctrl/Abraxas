#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.viz.webgl_scene_runner import run_webgl_scene_spec


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="out/viz/webgl_scene_spec.latest.json")
    args = parser.parse_args()
    run_webgl_scene_spec(input_path=Path(args.input), out_path=Path(args.out))


if __name__ == "__main__":
    main()
