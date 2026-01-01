from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple


def _safe_read(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def load_bundles(bundles_dir: str) -> List[Dict[str, Any]]:
    if not bundles_dir or not os.path.exists(bundles_dir):
        return []
    out: List[Dict[str, Any]] = []
    for fn in sorted(os.listdir(bundles_dir)):
        if not fn.endswith(".json"):
            continue
        out.append(_safe_read(os.path.join(bundles_dir, fn)))
    return [b for b in out if isinstance(b, dict) and b.get("bundle_id")]


def load_bundles_from_index(bundles_dir: str, index_path: str) -> List[Dict[str, Any]]:
    """
    Load bundles using an evidence_index_<run>.json if available.
    Falls back to full directory scan when index is missing or empty.
    """
    if not index_path or not os.path.exists(index_path):
        return load_bundles(bundles_dir)
    index = _safe_read(index_path)
    listed = index.get("bundles") if isinstance(index, dict) else None
    if not isinstance(listed, list):
        return load_bundles(bundles_dir)
    bundle_ids = [str(b.get("bundle_id") or "") for b in listed if isinstance(b, dict)]
    bundle_ids = [bid for bid in bundle_ids if bid]
    if not bundle_ids:
        return load_bundles(bundles_dir)
    out: List[Dict[str, Any]] = []
    for bid in bundle_ids:
        path = os.path.join(bundles_dir, f"{bid}.json")
        if os.path.exists(path):
            out.append(_safe_read(path))
    return [b for b in out if isinstance(b, dict) and b.get("bundle_id")]


def term_lift(bundles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    term(lower) -> lift summary
    """
    out: Dict[str, Dict[str, Any]] = {}
    for b in bundles:
        terms = b.get("terms") if isinstance(b.get("terms"), list) else []
        st = str(b.get("source_type") or "unknown")
        cred = float(b.get("credence") or 0.5)
        if cred < 0.0:
            cred = 0.0
        if cred > 1.0:
            cred = 1.0

        for t in terms:
            tk = str(t or "").strip().lower()
            if not tk:
                continue
            cell = out.setdefault(
                tk,
                {
                    "bundle_count": 0,
                    "source_types": {},
                    "credence_sum": 0.0,
                    "credence_mean": 0.0,
                },
            )
            cell["bundle_count"] += 1
            cell["source_types"][st] = int(cell["source_types"].get(st, 0)) + 1
            cell["credence_sum"] = float(cell["credence_sum"]) + float(cred)

    for tk, cell in out.items():
        n = int(cell.get("bundle_count") or 0)
        cell["credence_mean"] = float(cell.get("credence_sum") or 0.0) / float(n) if n else 0.0
    return out


def uplift_factors(lift: Dict[str, Any]) -> Tuple[float, float]:
    """
    Convert lift summary into bounded additive uplifts:
      - attribution_uplift in [0, 0.20]
      - diversity_uplift in [0, 0.15]
    """
    n = int(lift.get("bundle_count") or 0)
    types = lift.get("source_types") if isinstance(lift.get("source_types"), dict) else {}
    uniq_types = len(types)
    cred = float(lift.get("credence_mean") or 0.0)

    att = min(0.20, (0.05 * min(n, 3)) + (0.05 * cred))
    div = min(0.15, (0.04 * min(uniq_types, 3)) + (0.02 * min(n, 3)))

    return float(att), float(div)
