#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.viz.controlled_hover_runner import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interaction-policy", required=True)
    parser.add_argument("--policy-ledger", required=True)
    parser.add_argument("--provisioning-manifest", required=True)
    parser.add_argument("--ci-proof", required=True)
    parser.add_argument("--component-manifest", required=True)
    parser.add_argument("--out", default="out/viz/controlled_hover_policy_packet.latest.json")
    args = parser.parse_args()
    run(Path(args.interaction_policy), Path(args.policy_ledger), Path(args.provisioning_manifest), Path(args.ci_proof), Path(args.component_manifest), Path(args.out))


if __name__ == "__main__":
    main()
