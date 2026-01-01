from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abx.confidence_bands import compute_bands, _read_jsonl, _vec


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def detect_regime_shift(sig_ledger: str, window: int = 14, z_thresh: float = 2.2) -> Dict[str, Any]:
    snaps = [s for s in _read_jsonl(sig_ledger) if str(s.get("kind") or "") == "sig_snapshot"]
    snaps.sort(key=lambda d: str(d.get("ts") or ""))
    if len(snaps) < max(10, window):
        return {
            "version": "regime_shift.v0.1",
            "ts": _utc_now_iso(),
            "error": "Not enough snapshots for regime detection.",
            "n": len(snaps),
        }

    bands = compute_bands(sig_ledger, window=window)
    b = bands.get("bands") if isinstance(bands.get("bands"), dict) else {}

    # Use MAE, BRIER, TAU, SIG_scalar volatility as indicators
    keys = ["SIG_scalar", "MAE", "BRIER", "TAU"]
    latest = _vec(snaps[-1])

    flags = []
    for k in keys:
        bk = b.get(k) if isinstance(b.get(k), dict) else {}
        mu = float(bk.get("mean") or 0.0)
        sd = float(bk.get("std") or 0.0)
        x = float(latest.get(k, 0.0))
        z = 0.0 if sd <= 1e-9 else (x - mu) / sd
        if abs(z) >= float(z_thresh):
            flags.append({"metric": k, "z": float(z), "latest": x, "mean": mu, "std": sd})

    # Additional: persistent mean shift between first half and second half of window (SIG_scalar)
    tail = snaps[-window:]
    mid = window // 2
    a = [_vec(s).get("SIG_scalar", 0.0) for s in tail[:mid]]
    c = [_vec(s).get("SIG_scalar", 0.0) for s in tail[mid:]]
    mean_a = sum(a) / float(len(a) or 1)
    mean_c = sum(c) / float(len(c) or 1)
    sd_sig = float((b.get("SIG_scalar") or {}).get("std") or 0.0)
    mean_shift = 0.0 if sd_sig <= 1e-9 else (mean_c - mean_a) / sd_sig

    regime = bool(flags) and (abs(mean_shift) >= 1.2 or any(f["metric"] == "TAU" for f in flags))
    return {
        "version": "regime_shift.v0.1",
        "ts": _utc_now_iso(),
        "window": window,
        "z_thresh": float(z_thresh),
        "flags": flags,
        "mean_shift_SIG_scalar_z": float(mean_shift),
        "regime_shift": bool(regime),
        "recommendation": (
            "Regime shift detected: widen τ search + allow scenario change; treat rapid τ movement as phase transition, not model failure."
            if regime else
            "No regime shift detected."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect regime shift from SIG snapshots")
    ap.add_argument("--sig-ledger", default="out/ledger/sig_snapshots.jsonl")
    ap.add_argument("--window", type=int, default=14)
    ap.add_argument("--z-thresh", type=float, default=2.2)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    obj = detect_regime_shift(args.sig_ledger, window=int(args.window), z_thresh=float(args.z_thresh))
    out_path = args.out or os.path.join("out/reports", f"regime_shift_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[REGIME] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
