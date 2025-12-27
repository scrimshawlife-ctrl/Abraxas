from __future__ import annotations

import json
import math
import os
from collections import Counter
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


def _entropy(counts: List[int]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    ent = 0.0
    for c in counts:
        if c <= 0:
            continue
        p = c / total
        ent -= p * math.log(p + 1e-12, 2)
    return float(ent)


def proof_quality_from_terms(terms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Input: proof_density terms list (term-level).
    Output: quality metrics + anti-gaming penalty signals.

    We do NOT have per-anchor lists in v0.1. So we approximate:
    - diversity proxy = unique_domains
    - primary proxy = primary_anchors
    """
    n = len(terms)
    if n == 0:
        return {
            "domain_entropy_norm": 0.0,
            "avg_unique_domains": 0.0,
            "avg_primary_anchors": 0.0,
            "recycle_risk": 1.0,
            "quality_score": 0.0,
            "penalty": 0.25,
            "notes": "No terms provided; default penalty applied.",
        }

    uniq_domains = [int(t.get("unique_domains") or 0) for t in terms if isinstance(t, dict)]
    prim = [int(t.get("primary_anchors") or 0) for t in terms if isinstance(t, dict)]

    avg_ud = sum(uniq_domains) / float(len(uniq_domains) or 1)
    avg_pr = sum(prim) / float(len(prim) or 1)

    # Entropy proxy: distribution of unique_domains across terms
    # (Not perfect, but detects "all terms have same tiny diversity" vs broad spread)
    bins = Counter(uniq_domains)
    ent = _entropy(list(bins.values()))
    ent_norm = float(ent / (math.log(len(bins) + 1e-12, 2) + 1e-9)) if len(bins) > 1 else 0.0

    # recycle risk: low diversity + low entropy => likely gaming/recycling
    recycle_risk = float(max(0.0, min(1.0, 1.0 - (0.55 * min(1.0, avg_ud / 4.0) + 0.45 * ent_norm))))

    # quality score encourages both diversity + primary anchors
    q = 0.55 * min(1.0, avg_ud / 6.0) + 0.45 * min(1.0, avg_pr / 4.0)
    q = float(max(0.0, min(1.0, q)))

    # penalty applies when recycle risk is high
    penalty = float(0.40 * recycle_risk)  # up to 0.40

    return {
        "domain_entropy_norm": ent_norm,
        "avg_unique_domains": float(avg_ud),
        "avg_primary_anchors": float(avg_pr),
        "recycle_risk": recycle_risk,
        "quality_score": q,
        "penalty": penalty,
        "notes": "Anti-Goodhart: penalize low diversity + low entropy (recycled anchors).",
    }


def apply_goodhart_to_observed_gain(observed_gain: float, quality: Dict[str, Any]) -> float:
    """
    Adjust observed gain by proof-quality penalty.
    Positive gains remain possible, but gaming gets discounted.
    """
    pen = float(quality.get("penalty") or 0.0)
    # discount magnitude (both positive and negative) slightly; primarily hits positive "inflations"
    if observed_gain > 0:
        return float(max(-1.5, min(1.5, observed_gain * (1.0 - pen))))
    return float(max(-1.5, min(1.5, observed_gain * (1.0 - 0.15 * pen))))


def build_goodhart_guard_report(*, proof_density_path: str) -> Dict[str, Any]:
    pd = _read_json(proof_density_path)
    terms = pd.get("terms") if isinstance(pd.get("terms"), list) else []
    q = proof_quality_from_terms(terms)
    return {
        "version": "goodhart_guard.v0.1",
        "ts": _utc_now_iso(),
        "proof_density_path": proof_density_path,
        "quality": q,
    }
