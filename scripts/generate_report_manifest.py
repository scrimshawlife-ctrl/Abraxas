from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.report_manifest import build_report_manifest, write_report_manifest


def main() -> int:
    records = build_report_manifest()
    write_report_manifest(records)
    print(json.dumps({"status": "OK", "records": len(records)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
