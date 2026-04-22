from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.report_manifest_diff import generate_report_manifest_diff
from abx.report_manifest_diff_ledger import log_diff_ledger


def main() -> int:
    generate_report_manifest_diff()
    payload = log_diff_ledger()
    record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
    print(
        json.dumps(
            {
                "status": payload.get("status", "NOT_COMPUTABLE"),
                "appended": bool(payload.get("appended", False)),
                "diff_id": record.get("diff_id", "NOT_COMPUTABLE"),
                "added_count": int(record.get("added_count", 0) or 0),
                "removed_count": int(record.get("removed_count", 0) or 0),
                "status_changed_count": int(record.get("status_changed_count", 0) or 0),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
