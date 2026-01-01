from __future__ import annotations

import argparse
import glob
import json
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def _days_between(a: datetime, b: datetime) -> float:
    return float((b - a).total_seconds() / 86400.0)


def _variance(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mu = sum(xs) / len(xs)
    return float(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def _rolling_vars(xs: List[float], w: int) -> List[float]:
    out = []
    for i in range(len(xs)):
        start = max(0, i - w + 1)
        seg = xs[start : i + 1]
        out.append(_variance(seg))
    return out


def ttt_threshold(points: List[Dict[str, Any]], threshold: float = 0.60, sustain: int = 3) -> float:
    """
    Returns days from first point until CS_score >= threshold for sustain consecutive points.
    Returns -1 if never achieved.
    """
    if not points:
        return -1.0
    t0 = _parse_ts(str(points[0].get("ts") or ""))
    streak = 0
    for p in points:
        cs = float(p.get("CS_score") or 0.0)
        if cs >= threshold:
            streak += 1
            if streak >= sustain:
                return _days_between(t0, _parse_ts(str(p.get("ts") or "")))
        else:
            streak = 0
    return -1.0


def stabilization_half_life(points: List[Dict[str, Any]], window: int = 5) -> float:
    """
    Approximate: compute rolling variance of CS_score; find when it falls below half the initial variance peak.
    Returns days to half-variance. -1 if not enough points.
    """
    if len(points) < max(6, window):
        return -1.0
    t0 = _parse_ts(str(points[0].get("ts") or ""))
    xs = [float(p.get("CS_score") or 0.0) for p in points]
    rv = _rolling_vars(xs, window)
    v0 = max(rv[:window])  # early volatility
    target = 0.5 * v0
    for i in range(window, len(rv)):
        if rv[i] <= target:
            ti = _parse_ts(str(points[i].get("ts") or ""))
            return _days_between(t0, ti)
    return -1.0


def flip_rate(points: List[Dict[str, Any]]) -> float:
    if len(points) < 2:
        return 0.0
    flips = 0
    prev = str(points[0].get("quadrant") or "")
    for p in points[1:]:
        q = str(p.get("quadrant") or "")
        if q and prev and q != prev:
            flips += 1
        prev = q
    return float(flips / max(1, len(points) - 1))


def horizon_class(cshl_days: float, ttt_08: float, ml_latest: float) -> str:
    """
    Governance: not a "prediction limit", a recommended class.
    """
    # If manipulation risk is high, shorten horizon by default (still can forecast longer, but label it).
    ml = ml_latest
    if cshl_days < 0 and ttt_08 < 0:
        return "UNKNOWN"
    base = "WEEKS"
    d = cshl_days if cshl_days >= 0 else (ttt_08 if ttt_08 >= 0 else 21.0)
    if d <= 2:
        base = "DAYS"
    elif d <= 14:
        base = "WEEKS"
    elif d <= 60:
        base = "MONTHS"
    else:
        base = "YEARS"
    if ml >= 0.70 and base in ("MONTHS", "YEARS"):
        return base + "_HIGH_POLLUTION"
    return base


def compute_ttt(claim_timeseries_path: str) -> Dict[str, Any]:
    obj = _read_json(claim_timeseries_path)
    series = obj.get("series") if isinstance(obj.get("series"), dict) else {}
    meta = obj.get("claim_meta") if isinstance(obj.get("claim_meta"), dict) else {}

    out = {}
    for cid, pts in series.items():
        if not isinstance(pts, list) or len(pts) < 2:
            continue
        pts = sorted(pts, key=lambda p: _parse_ts(str(p.get("ts") or "")))
        ttt06 = ttt_threshold(pts, threshold=0.60, sustain=3)
        ttt08 = ttt_threshold(pts, threshold=0.80, sustain=3)
        cshl = stabilization_half_life(pts, window=5)
        fr = flip_rate(pts)
        latest = pts[-1]
        ml_latest = float(latest.get("ML_score") or 0.0)
        cs_latest = float(latest.get("CS_score") or 0.0)
        hc = horizon_class(cshl, ttt08, ml_latest)

        out[cid] = {
            "term": (meta.get(cid) or {}).get("term") if isinstance(meta.get(cid), dict) else None,
            "claim_handle": (meta.get(cid) or {}).get("claim_handle") if isinstance(meta.get(cid), dict) else None,
            "CSHL_days": float(cshl),
            "TTT_0.6_days": float(ttt06),
            "TTT_0.8_days": float(ttt08),
            "flip_rate": float(fr),
            "latest": {"CS_score": float(cs_latest), "ML_score": float(ml_latest), "quadrant": str(latest.get("quadrant") or "")},
            "horizon_class": hc,
            "notes": "TTT/CSHL quantify temporal stabilization of claims. Used to govern forecast horizon without pretending certainty.",
        }

    return {
        "version": "time_to_truth.v0.1",
        "ts": _utc_now_iso(),
        "source": claim_timeseries_path,
        "n_claims_scored": len(out),
        "claims": out,
        "notes": "Time-to-Truth curves + stabilization half-life. Core temporal element for multi-year horizon governance.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute Time-to-Truth + stabilization metrics for claims")
    ap.add_argument("--claim-timeseries", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    cts = args.claim_timeseries
    if not cts:
        # latest
        paths = sorted(glob.glob("out/reports/claim_timeseries_*.json"))
        cts = paths[-1] if paths else ""
    if not cts:
        raise SystemExit("No claim_timeseries found. Run `python -m abx.claim_timeseries` first.")

    obj = compute_ttt(cts)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"time_to_truth_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[TTT] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
