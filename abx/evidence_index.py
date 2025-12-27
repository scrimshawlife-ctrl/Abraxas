from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    p = argparse.ArgumentParser(description="Index evidence bundles for a run")
    p.add_argument("--run-id", required=True)
    p.add_argument("--bundles-dir", default="out/evidence_bundles")
    p.add_argument("--out-reports", default="out/reports")
    args = p.parse_args()

    ts = _utc_now_iso()
    bundles: List[Dict[str, Any]] = []
    if os.path.exists(args.bundles_dir):
        for fn in sorted(os.listdir(args.bundles_dir)):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(args.bundles_dir, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    bundles.append(json.load(f))
            except Exception:
                continue

    out = {
        "version": "evidence_index.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "count": len(bundles),
        "bundles": [
            {
                "bundle_id": b.get("bundle_id"),
                "terms": b.get("terms"),
                "source_type": b.get("source_type"),
                "source_ref": b.get("source_ref"),
            }
            for b in bundles
        ],
        "provenance": {"builder": "abx.evidence_index.v0.1"},
    }

    os.makedirs(args.out_reports, exist_ok=True)
    path = os.path.join(args.out_reports, f"evidence_index_{args.run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[EVIDENCE_INDEX] wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
