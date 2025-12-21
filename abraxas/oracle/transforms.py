"""Deterministic transforms for Oracle Pipeline v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List


def decay(age_hours: float, half_life_hours: float) -> float:
    """
    Deterministic exponential decay.

    Args:
        age_hours: Age of the signal in hours
        half_life_hours: Half-life for decay calculation

    Returns:
        Decay weight (0.5 ** (age/half_life))
    """
    if half_life_hours <= 0:
        raise ValueError("half_life_hours must be > 0")
    # 0.5 ** (age/half_life)
    return 0.5 ** (age_hours / half_life_hours)


@dataclass(frozen=True)
class CorrelationDelta:
    """Represents a change in correlation between two domains."""

    domain_a: str
    domain_b: str
    key: str  # what correlated (token, motif, signal id)
    delta: float  # change magnitude
    observed_at_utc: str  # ISO8601 Z


def _parse_iso_z(ts: str) -> datetime:
    """Parse ISO8601 Zulu timestamp to datetime."""
    # expects "YYYY-MM-DDTHH:MM:SSZ"
    if not ts.endswith("Z"):
        raise ValueError("timestamp must be Zulu (Z) format")
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def score_deltas(
    deltas: Iterable[CorrelationDelta],
    *,
    as_of_utc: str,
    half_life_hours: float,
) -> List[Dict]:
    """
    Turns deltas into stable scored signals.

    Args:
        deltas: Collection of correlation deltas
        as_of_utc: Reference time for aging calculations (ISO8601 Z)
        half_life_hours: Half-life for decay weighting

    Returns:
        List of scored signal dicts, sorted by score (descending)
    """
    as_of = _parse_iso_z(as_of_utc)
    scored: List[Dict] = []

    for d in deltas:
        t = _parse_iso_z(d.observed_at_utc)
        age_h = max(0.0, (as_of - t).total_seconds() / 3600.0)
        w = decay(age_h, half_life_hours)
        score = float(d.delta) * w

        scored.append(
            {
                "pair": f"{d.domain_a}~{d.domain_b}",
                "key": d.key,
                "delta": float(d.delta),
                "age_hours": round(age_h, 6),
                "weight": round(w, 12),
                "score": round(score, 12),
                "observed_at_utc": d.observed_at_utc,
            }
        )

    # deterministic sort: score desc, then pair, then key, then observed_at
    scored.sort(key=lambda x: (-x["score"], x["pair"], x["key"], x["observed_at_utc"]))
    return scored


def render_oracle(scored_signals: List[Dict], *, top_k: int) -> Dict:
    """
    Output is compact JSON, not prose.

    Args:
        scored_signals: Scored signal dicts from score_deltas
        top_k: Number of top signals to include

    Returns:
        Oracle output dict with top signals and aggregates
    """
    return {
        "top_k": int(top_k),
        "signals": scored_signals[: int(top_k)],
        "aggregate": {
            "count": len(scored_signals),
            "score_sum": round(sum(s["score"] for s in scored_signals), 12),
        },
    }
