from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, List, Optional, Tuple


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = " ".join(s.replace("-", " ").replace("_", " ").split())
    return s


def find_latest_slang_drift(out_reports: str) -> Optional[str]:
    paths = sorted(glob.glob(os.path.join(out_reports, "slang_drift_*.json")))
    if not paths:
        return None
    best = paths[-1]
    try:
        best_m = os.path.getmtime(best)
        for p in reversed(paths[-10:]):
            try:
                if os.path.getmtime(p) > best_m:
                    best = p
                    best_m = os.path.getmtime(p)
            except Exception:
                continue
    except Exception:
        pass
    return best


def load_ml_map(out_reports: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    path = find_latest_slang_drift(out_reports)
    if not path:
        return {}, {"path": "", "ts": "", "version": "", "notes": "No slang_drift found."}

    obj = _read_json(path)
    terms = obj.get("terms") if isinstance(obj.get("terms"), list) else []
    out: Dict[str, Dict[str, Any]] = {}
    for it in terms:
        if not isinstance(it, dict):
            continue
        canon = str(it.get("canonical_term") or "").strip()
        if not canon:
            continue
        variants = it.get("variants") if isinstance(it.get("variants"), list) else [canon]
        m = it.get("manufacture") if isinstance(it.get("manufacture"), dict) else {}
        cell = {
            "ml_score": float(m.get("ml_score") or 0.0),
            "bucket": str(m.get("bucket") or "UNKNOWN"),
            "signals": m.get("signals") if isinstance(m.get("signals"), list) else [],
            "canonical_term": canon,
            "variants": [str(v) for v in variants if str(v).strip()],
        }
        out[_norm(canon)] = cell
        for v in variants:
            out[_norm(str(v))] = cell

    meta = {
        "path": path,
        "ts": str(obj.get("ts") or ""),
        "version": str(obj.get("version") or ""),
        "notes": "Latest slang_drift used as ML index.",
    }
    return out, meta
