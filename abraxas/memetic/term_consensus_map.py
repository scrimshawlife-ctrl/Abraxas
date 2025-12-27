from __future__ import annotations

import json
import os
from typing import Any, Dict


def load_term_consensus_map(path: str) -> Dict[str, float]:
    """
    term(lower) -> consensus_gap (0..1)
    Reads term_claims_<run>.json metrics.term_consensus.
    """
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            return {}
        metrics = obj.get("metrics") or {}
        if not isinstance(metrics, dict):
            return {}
        term_consensus = metrics.get("term_consensus") or {}
        if not isinstance(term_consensus, dict):
            return {}
        out: Dict[str, float] = {}
        for term, payload in term_consensus.items():
            if not isinstance(payload, dict):
                continue
            out[str(term).strip().lower()] = float(payload.get("consensus_gap") or 0.0)
        return out
    except Exception:
        return {}
