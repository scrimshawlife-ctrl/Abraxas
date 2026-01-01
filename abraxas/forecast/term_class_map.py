from __future__ import annotations

import json
import os
from typing import Any, Dict

from abraxas.forecast.term_classify import classify_term


def load_term_class_map(a2_phase_path: str) -> Dict[str, str]:
    """
    term(lower) -> class
    """
    if not a2_phase_path or not os.path.exists(a2_phase_path):
        return {}
    try:
        with open(a2_phase_path, "r", encoding="utf-8") as f:
            a2 = json.load(f)
        raw = a2.get("raw_full") if isinstance(a2, dict) else {}
        profs = raw.get("profiles") if isinstance(raw, dict) else None
        if not isinstance(profs, list):
            profs = (a2.get("views") or {}).get("profiles_top") if isinstance(a2, dict) else None
        if not isinstance(profs, list):
            return {}

        out: Dict[str, str] = {}
        for p in profs:
            if not isinstance(p, dict):
                continue
            t = str(p.get("term") or "").strip().lower()
            if not t:
                continue
            out[t] = classify_term(p)
        return out
    except Exception:
        return {}
