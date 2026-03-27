#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.continuity import build_continuity_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Build cross-run continuity summary artifact")
    ap.add_argument("scenario_json")
    args = ap.parse_args()
    payload = json.loads(Path(args.scenario_json).read_text(encoding="utf-8"))
    base_dir = Path(str(payload.get("base_dir") or "."))
    out = build_continuity_summary(base_dir=base_dir, payload=payload)
    print(json.dumps(out.__dict__, indent=2, sort_keys=True))
    return 0 if out.continuity_status in {"VALID", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
