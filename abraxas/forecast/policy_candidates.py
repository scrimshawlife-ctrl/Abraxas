from __future__ import annotations

from typing import Dict


def candidates_v0_1() -> Dict[str, Dict[str, float]]:
    """
    Thresholds are Brier score caps (lower is better).
    More aggressive = higher caps = more horizons allowed.
    """
    return {
        "conservative": {"days": 0.20, "weeks": 0.22, "months": 0.24, "years": 0.26},
        "balanced": {"days": 0.22, "weeks": 0.24, "months": 0.26, "years": 0.28},
        "aggressive": {"days": 0.24, "weeks": 0.26, "months": 0.28, "years": 0.30},
    }
