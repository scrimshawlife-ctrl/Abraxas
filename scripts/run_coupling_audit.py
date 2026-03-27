#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.coupling_audit import audit_coupling


def main() -> int:
    ap = argparse.ArgumentParser(description="Run cross-subsystem coupling audit")
    ap.add_argument("--base-dir", default=".")
    args = ap.parse_args()
    artifact = audit_coupling(repo_root=Path(args.base_dir))
    print(json.dumps(artifact.__dict__, indent=2, sort_keys=True))
    return 0 if artifact.status != "BROKEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
