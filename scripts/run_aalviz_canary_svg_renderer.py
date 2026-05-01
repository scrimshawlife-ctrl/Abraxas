#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.viz.svg_runner import run_renderer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--view-packet", required=True)
    parser.add_argument("--svg-out", default="out/viz/canary_governance_view.latest.svg")
    parser.add_argument("--manifest-out", default="out/viz/canary_governance_view.latest.render.json")
    args = parser.parse_args()
    run_renderer(Path(args.view_packet), Path(args.svg_out), Path(args.manifest_out))


if __name__ == "__main__":
    main()
