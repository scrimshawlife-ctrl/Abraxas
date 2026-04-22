from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.readiness_comparison import append_comparison_ledger, build_readiness_comparison_record


def main() -> int:
    record = build_readiness_comparison_record()
    appended = append_comparison_ledger(record)
    print(json.dumps({"comparison_id": record["comparison_id"], "alignment": record["alignment"], "appended": appended}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
