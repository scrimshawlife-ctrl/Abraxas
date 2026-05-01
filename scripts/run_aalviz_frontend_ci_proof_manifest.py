#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abraxas.core.canonical import canonical_json
from abraxas.viz.frontend_ci_proof_manifest import build_ci_proof_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", required=True)
    parser.add_argument("--reason", default=None)
    parser.add_argument("--out", default="out/viz/frontend_ci_proof.latest.json")
    args = parser.parse_args()
    manifest = build_ci_proof_manifest(args.status, args.reason)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonical_json(manifest), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
