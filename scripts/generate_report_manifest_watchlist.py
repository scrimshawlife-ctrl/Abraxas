from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.report_manifest_watchlist import build_report_manifest_watchlist, write_report_manifest_watchlist


def main() -> int:
    payload = build_report_manifest_watchlist(window_size=20)
    write_report_manifest_watchlist(payload)
    watchlist = payload.get("watchlist") if isinstance(payload.get("watchlist"), dict) else {}
    items = watchlist.get("items") if isinstance(watchlist.get("items"), list) else []
    print(json.dumps({"status": payload.get("status", "NOT_COMPUTABLE"), "item_count": len(items)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
