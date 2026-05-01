#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from abraxas.viz.frontend_provisioning_manifest import build_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend-root", default="frontend/aal-viz")
    parser.add_argument("--out", default="out/viz/frontend_provisioning_manifest.latest.json")
    parser.add_argument("--npm-ci-status", default="not_run")
    parser.add_argument("--npm-ci-reason", default=None)
    args = parser.parse_args()
    manifest = build_manifest(
        frontend_root=args.frontend_root,
        npm_ci_status=args.npm_ci_status,
        npm_ci_reason=args.npm_ci_reason,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(f"Wrote manifest → {out_path}")


if __name__ == "__main__":
    main()
