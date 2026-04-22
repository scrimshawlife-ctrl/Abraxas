from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.promotion_preflight import build_promotion_preflight_advisory, write_latest_advisory


def main() -> int:
    advisory = build_promotion_preflight_advisory()
    write_latest_advisory(advisory)
    print(json.dumps({"advisory_id": advisory["advisory_id"], "advisory_state": advisory["advisory_state"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
