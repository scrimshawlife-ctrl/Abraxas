from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.report_manifest_summary import build_manifest_change_summary, write_manifest_change_summary


def main() -> int:
    payload = build_manifest_change_summary(window_size=10)
    write_manifest_change_summary(payload)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    print(
        json.dumps(
            {
                "status": payload.get("status", "NOT_COMPUTABLE"),
                "stability_indicator": summary.get("stability_indicator", "NOT_COMPUTABLE"),
                "window_size": summary.get("window_size", 0),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
