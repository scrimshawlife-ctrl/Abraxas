from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExpectedErrorBand:
    timing_days_min: float
    timing_days_max: float
    magnitude_pct_min: float
    magnitude_pct_max: float
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


HORIZON_BASE = {
    "days": (1.0, 3.0),
    "weeks": (3.0, 10.0),
    "months": (10.0, 35.0),
    "years_1": (45.0, 140.0),
    "years_5": (140.0, 420.0),
}


PHASE_VOL = {
    "surging": 0.35,
    "resurgent": 0.30,
    "emergent": 0.28,
    "plateau": 0.12,
    "decaying": 0.18,
    "dormant": 0.22,
}


def expected_error_band(
    *,
    horizon: str,
    phase: str,
    half_life_days: float,
    manipulation_risk: float,
    recurrence_days: Optional[float],
) -> ExpectedErrorBand:
    """
    Deterministic EEB generator (v0.1):
      - start with horizon base window
      - widen with risk + volatile phase
      - tighten with long half-life + stable recurrence
    """
    base = HORIZON_BASE.get(horizon, (10.0, 35.0))
    tmin, tmax = base

    vol = PHASE_VOL.get(phase, 0.22)
    risk = max(0.0, min(1.0, float(manipulation_risk)))
    hl = max(0.5, float(half_life_days))

    hl_tight = min(0.25, math.log10(1.0 + hl) / 12.0)

    rec_tight = 0.0
    if recurrence_days is not None:
        rec = max(0.5, float(recurrence_days))
        rec_tight = 0.06 if rec <= 7.0 else (0.03 if rec <= 14.0 else 0.0)

    widen = (0.55 * risk) + (0.45 * vol)

    tmin = tmin * (1.0 + 0.25 * widen) * (1.0 - hl_tight - rec_tight)
    tmax = tmax * (1.0 + 0.70 * widen) * (1.0 - 0.65 * (hl_tight + rec_tight))

    mag_base = 0.10 if horizon in ("days", "weeks") else (0.18 if horizon == "months" else 0.28)
    mag_widen = mag_base + 0.22 * risk + 0.18 * vol
    mag_min = max(0.05, mag_base * (1.0 - 0.45 * (hl_tight + rec_tight)))
    mag_max = min(0.95, mag_widen)

    return ExpectedErrorBand(
        timing_days_min=float(max(0.5, tmin)),
        timing_days_max=float(max(tmin + 0.5, tmax)),
        magnitude_pct_min=float(mag_min),
        magnitude_pct_max=float(mag_max),
        provenance={
            "method": "expected_error_band.v0.1",
            "inputs": {"horizon": horizon, "phase": phase},
        },
    )


def brier_score(probs: List[float], outcomes: List[int]) -> float:
    """
    Standard Brier score for binary outcomes.
    """
    if not probs or len(probs) != len(outcomes):
        return float("nan")
    score = 0.0
    for prob, outcome in zip(probs, outcomes):
        prob = max(0.0, min(1.0, float(prob)))
        truth = 1.0 if int(outcome) == 1 else 0.0
        score += (prob - truth) ** 2
    return float(score / float(len(probs)))
