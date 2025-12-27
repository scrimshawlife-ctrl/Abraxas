from __future__ import annotations

from typing import Any, Dict


def classify_term(profile: Dict[str, Any]) -> str:
    """
    Deterministic term stability class from A2 profile fields.
    Output: stable | emerging | contested | volatile | unknown
    """
    if not isinstance(profile, dict):
        return "unknown"

    cg = float(profile.get("consensus_gap_term") or 0.0)
    hl = float(profile.get("half_life_days") or 0.0)
    mr = float(profile.get("manipulation_risk") or 0.0)
    mom = str(profile.get("momentum") or "").lower()
    flags = profile.get("flags") if isinstance(profile.get("flags"), list) else []

    if "CONSENSUS_MISSING" in flags and cg == 0.0:
        return "unknown"

    if cg >= 0.60 or mr >= 0.75:
        return "contested"

    if hl < 7.0:
        return "volatile"
    if mom in ("surging", "spiking") and cg >= 0.50:
        return "volatile"

    if hl >= 14.0 and cg <= 0.35 and mr <= 0.55:
        return "stable"

    if mom in ("rising", "surging", "spiking") and cg <= 0.50:
        return "emerging"
    if hl < 14.0 and cg <= 0.50:
        return "emerging"

    return "unknown"
