from __future__ import annotations

from typing import Any, Dict, List


def _clamp(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def _bucket(x: float) -> str:
    if x <= 0.33:
        return "LOW"
    if x <= 0.66:
        return "MED"
    return "HIGH"


def _ratio(d: Dict[str, int], keys: List[str]) -> float:
    if not isinstance(d, dict) or not d:
        return 0.0
    total = sum(int(v) for v in d.values())
    if total <= 0:
        return 0.0
    num = 0
    for k in keys:
        num += int(d.get(k, 0))
    return float(num) / float(total)


def manufacture_likelihood(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Manufacture Likelihood (ML):
      - HIGH when: new-to-window + high drift + concentrated in high-fog + OP_FOG/FORK_STORM tags +
                  low evidence adequacy/falsifiability (if known).
      - LOW when: stable usage across buckets + low drift OR investigative corridor regimes.
    """
    signals: List[str] = []

    novelty = entry.get("novelty") if isinstance(entry.get("novelty"), dict) else {}
    drift = entry.get("drift") if isinstance(entry.get("drift"), dict) else {}
    dmx_counts = (
        entry.get("dmx_bucket_counts")
        if isinstance(entry.get("dmx_bucket_counts"), dict)
        else {}
    )
    fog_counts = (
        entry.get("fog_type_counts")
        if isinstance(entry.get("fog_type_counts"), dict)
        else {}
    )

    new_to_window = bool(novelty.get("new_to_window"))
    drift_score = float(drift.get("drift_score") or 0.0)

    high_fog_ratio = _ratio(dmx_counts, ["HIGH"])
    op_fog_ratio = _ratio(fog_counts, ["OP_FOG"])
    fork_ratio = _ratio(fog_counts, ["FORK_STORM"])
    drought_ratio = _ratio(fog_counts, ["PROVENANCE_DROUGHT"])
    corridor_ratio = _ratio(fog_counts, ["COH_HIGH_EQ", "INVESTIGATIVE_CORRIDOR"])

    csp = entry.get("csp") if isinstance(entry.get("csp"), dict) else {}
    ea = float(csp.get("EA") or 0.0)
    ff = float(csp.get("FF") or 0.0)
    mio = float(csp.get("MIO") or 0.0)

    score = 0.0
    if new_to_window:
        score += 0.18
        signals.append("NEW_TO_WINDOW")

    score += 0.22 * _clamp(drift_score)
    if drift_score >= 0.55:
        signals.append("HIGH_DRIFT")
    elif drift_score >= 0.30:
        signals.append("MED_DRIFT")

    score += 0.22 * _clamp(high_fog_ratio)
    if high_fog_ratio >= 0.60:
        signals.append("HIGH_FOG_CONCENTRATED")
    elif high_fog_ratio >= 0.35:
        signals.append("HIGH_FOG_PRESENT")

    score += 0.16 * _clamp(op_fog_ratio)
    if op_fog_ratio >= 0.30:
        signals.append("OP_FOG_FREQUENT")
    score += 0.12 * _clamp(fork_ratio)
    if fork_ratio >= 0.25:
        signals.append("FORK_STORM_FREQUENT")
    score += 0.08 * _clamp(drought_ratio)
    if drought_ratio >= 0.25:
        signals.append("PROVENANCE_DROUGHT_FREQUENT")

    if csp:
        if ea < 0.45:
            score += 0.10
            signals.append("EA_LOW")
        if ff < 0.50:
            score += 0.10
            signals.append("FF_LOW")
        if ea >= 0.60 and ff >= 0.60:
            score -= 0.16
            signals.append("EA_FF_HIGH_DEBIAS")
        if mio >= 0.70:
            score += 0.08
            signals.append("MIO_HIGH")

    if corridor_ratio >= 0.20:
        score -= 0.14
        signals.append("INVESTIGATIVE_CORRIDOR_DEBIAS")

    score = _clamp(score)

    return {
        "ml_score": float(score),
        "bucket": _bucket(float(score)),
        "signals": signals,
        "notes": "Manufacture Likelihood (label-only): steering/amplification probability, not falsity.",
    }
