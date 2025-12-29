from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def brier(p: float, y: float) -> float:
    return float((p - y) ** 2)


def expected_calibration_error(pairs: List[Tuple[float, float]], bins: int = 10) -> float:
    """
    ECE over (p,y) pairs where y in {0,1}.
    """
    if not pairs:
        return 0.0
    bins = max(2, min(50, int(bins)))
    bucket = [[] for _ in range(bins)]
    for p, y in pairs:
        i = min(bins - 1, max(0, int(p * bins)))
        bucket[i].append((p, y))
    ece = 0.0
    n = len(pairs)
    for b in bucket:
        if not b:
            continue
        ps = sum(x[0] for x in b) / len(b)
        ys = sum(x[1] for x in b) / len(b)
        ece += (len(b) / n) * abs(ps - ys)
    return float(ece)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute forecast calibration metrics (Brier/ECE) from ledger + resolved outcomes"
    )
    ap.add_argument("--forecast-ledger", default="out/ledger/forecast_ledger.jsonl")
    ap.add_argument("--outcome-ledger", default="out/ledger/forecast_outcomes.jsonl")
    ap.add_argument("--bins", type=int, default=10)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    forecasts = [
        f for f in _read_jsonl(args.forecast_ledger) if f.get("kind") == "forecast"
    ]
    outcomes = [
        o for o in _read_jsonl(args.outcome_ledger)
        if o.get("kind") == "forecast_outcome"
    ]
    out_by_id = {str(o.get("forecast_id")): o for o in outcomes if o.get("forecast_id")}

    pairs: List[Tuple[float, float]] = []
    scored = []
    for f in forecasts:
        fid = str(f.get("forecast_id") or "")
        if fid not in out_by_id:
            continue
        y = float(out_by_id[fid].get("y") or 0.0)
        p = float(f.get("p") or 0.0)
        pairs.append((p, y))
        scored.append(
            {
                "forecast_id": fid,
                "p": p,
                "y": y,
                "brier": brier(p, y),
                "horizon": (f.get("horizon") or {}).get("key"),
            }
        )

    b = sum(brier(p, y) for (p, y) in pairs) / len(pairs) if pairs else 0.0
    ece = expected_calibration_error(pairs, bins=int(args.bins))

    obj = {
        "version": "forecast_accuracy.v0.1",
        "ts": _utc_now_iso(),
        "n_scored": len(scored),
        "brier": float(b),
        "ece": float(ece),
        "scored": scored[:500],
        "notes": "Accuracy defined as calibration (Brier/ECE) on resolved forecasts; long horizons score slowly, by design.",
    }

    out_path = args.out or os.path.join(
        "out/reports",
        f"forecast_accuracy_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json",
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[FORECAST_ACC] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
