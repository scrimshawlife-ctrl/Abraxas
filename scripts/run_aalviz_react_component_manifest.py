#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.viz.react_component_manifest_runner import run_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="out/viz/react_component_manifest.latest.json")
    args = parser.parse_args()
    run_manifest(Path(args.repo_root), Path(args.out))


if __name__ == "__main__":
    main()
