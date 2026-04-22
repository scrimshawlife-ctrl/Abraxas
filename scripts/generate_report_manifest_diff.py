from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.report_manifest_diff import generate_report_manifest_diff


def main() -> int:
    payload = generate_report_manifest_diff()
    diff = payload.get("diff") if isinstance(payload.get("diff"), dict) else {}
    print(
        json.dumps(
            {
                "status": payload.get("status", "NOT_COMPUTABLE"),
                "added": len(diff.get("added", [])),
                "removed": len(diff.get("removed", [])),
                "hash_changed": len(diff.get("hash_changed", [])),
                "freshness_changed": len(diff.get("freshness_changed", [])),
                "status_changed": len(diff.get("status_changed", [])),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
