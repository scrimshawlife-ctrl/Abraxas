from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


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


def _as_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _mean(xs: List[float]) -> float:
    return sum(xs) / float(len(xs) or 1)


def _std(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mu = _mean(xs)
    var = sum((x - mu) ** 2 for x in xs) / float(len(xs) - 1)
    return float(math.sqrt(max(0.0, var)))


def _vec(s: Dict[str, Any]) -> Dict[str, float]:
    cal = s.get("CAL") if isinstance(s.get("CAL"), dict) else {}
    pdg = s.get("PDG") if isinstance(s.get("PDG"), dict) else {}
    sdg = s.get("SDG") if isinstance(s.get("SDG"), dict) else {}
    return {
        "SIG_scalar": _as_float(s.get("SIG_scalar")),
        "MAE": _as_float(cal.get("mae")),
        "BRIER": _as_float(cal.get("brier_red_within_horizon")),
        "PDG_anchors": _as_float(pdg.get("avg_primary_anchors_per_term")),
        "PDG_domains": _as_float(pdg.get("avg_unique_domains_per_term")),
        "PDG_tests": _as_float(pdg.get("avg_falsification_tests_per_term")),
        "SDG_stability": _as_float(sdg.get("slang_bucket_stability")),
        "TAU": _as_float(cal.get("tau_half_life_days")),
    }


def compute_bands(sig_ledger: str, window: int = 14) -> Dict[str, Any]:
    snaps = [s for s in _read_jsonl(sig_ledger) if str(s.get("kind") or "") == "sig_snapshot"]
    snaps.sort(key=lambda d: str(d.get("ts") or ""))
    if not snaps:
        return {"version": "confidence_bands.v0.1", "ts": _utc_now_iso(), "error": "No snapshots found."}

    tail = snaps[-window:] if len(snaps) > window else snaps
    vecs = [_vec(s) for s in tail]
    keys = sorted(vecs[0].keys())
    out = {"version": "confidence_bands.v0.1", "ts": _utc_now_iso(), "window": len(tail), "bands": {}}

    for k in keys:
        xs = [float(v.get(k, 0.0)) for v in vecs]
        mu = _mean(xs)
        sd = _std(xs)
        out["bands"][k] = {
            "mean": float(mu),
            "std": float(sd),
            "band_1s": [float(mu - sd), float(mu + sd)],
            "band_2s": [float(mu - 2 * sd), float(mu + 2 * sd)],
            "latest": float(vecs[-1].get(k, 0.0)),
        }
    out["notes"] = "Rolling confidence bands from SIG snapshots. Use for regime shift + skepticism calibration."
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute confidence bands over SIG snapshots")
    ap.add_argument("--sig-ledger", default="out/ledger/sig_snapshots.jsonl")
    ap.add_argument("--window", type=int, default=14)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    obj = compute_bands(args.sig_ledger, window=int(args.window))
    out_path = args.out or os.path.join("out/reports", f"confidence_bands_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[BANDS] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
