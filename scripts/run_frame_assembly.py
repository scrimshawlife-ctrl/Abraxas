#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.frame_adapters import assemble_resonance_frame


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble canonical ResonanceFrame from runtime artifacts")
    ap.add_argument("scenario_json")
    args = ap.parse_args()
    payload = json.loads(Path(args.scenario_json).read_text(encoding="utf-8"))
    out = assemble_resonance_frame(payload)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
