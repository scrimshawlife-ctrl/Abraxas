#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.viz.interaction_policy_runner import run_interaction_policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--viewer-spec", required=True)
    parser.add_argument("--component-manifest", required=True)
    parser.add_argument("--out", default="out/viz/interaction_policy.latest.json")
    args = parser.parse_args()
    run_interaction_policy(Path(args.viewer_spec), Path(args.component_manifest), Path(args.out))


if __name__ == "__main__":
    main()
