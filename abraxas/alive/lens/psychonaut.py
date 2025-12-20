# abraxas/alive/lens/psychonaut.py
"""
Psychonaut translator v0.1

Converts raw ALIVE signature (metrics) into felt-state outputs:
- pressure: "How hard is this pushing me?"
- pull: "How attractive is it?"
- agency_delta: "Does it narrow my choice-space?"
- drift_risk: "Am I likely to get captured over time?"

Philosophy: No therapy language. No diagnosis. Just signal and navigation.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List
import math


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, x))


def _clamp_m11(x: float) -> float:
    """Clamp value to [-1, 1] range."""
    return max(-1.0, min(1.0, x))


def _mean(vals: List[float]) -> float:
    """Compute mean of values, defaulting to 0.5 if empty."""
    return sum(vals) / float(len(vals)) if vals else 0.5


def _get_metric(signature: Dict[str, Any], metric_id: str) -> Optional[Dict[str, Any]]:
    """Extract metric from signature by ID."""
    for axis in ("influence", "vitality", "life_logistics"):
        for m in signature.get(axis, []) or []:
            if m.get("metric_id") == metric_id:
                return m
    return None


def psychonaut_translate(
    signature: Dict[str, Any], profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Translate raw ALIVE signature into Psychonaut felt-state view.

    Args:
        signature: Raw ALIVE metrics (influence, vitality, life_logistics)
        profile: User profile with capacity/susceptibility/preference

    Returns:
        {
          "pressure": float [0,1],
          "pull": float [0,1],
          "agency_delta": float [-1,1],
          "drift_risk": float [0,1],
          "notes": string[]
        }
    """
    profile = profile or {}
    cap = profile.get("capacity", {})
    susc = profile.get("susceptibility", {})
    pref = profile.get("preference", {})

    # Extract capacity dimensions
    cap_time = float(cap.get("time", 0.5))
    cap_sleep = float(cap.get("sleep", 0.5))
    cap_social = float(cap.get("social", 0.5))
    cap_money = float(cap.get("money", 0.5))

    # Compute capacity floor and vulnerability
    cap_floor = _mean([cap_time, cap_sleep, cap_social, cap_money])
    vuln = 1.0 - cap_floor

    # Extract susceptibility
    susc_vol = float(susc.get("volatility", 0.5))

    # Get IM.NCR (Narrative Compression Ratio)
    ncr = _get_metric(signature, "IM.NCR") or {"value": 0.0}
    ncr_val = float(ncr.get("value", 0.0))

    # Get VM.GI (Generativity Index)
    gi = _get_metric(signature, "VM.GI") or {"value": 0.0}
    gi_val = float(gi.get("value", 0.0))

    # Get LL.LFC (Life-Logistics Friction Coefficient)
    lfc = _get_metric(signature, "LL.LFC") or {
        "value": 0.0,
        "components": {"loads": {}},
    }
    lfc_val = float(lfc.get("value", 0.0))
    loads = (lfc.get("components") or {}).get("loads", {}) or {}

    # A) PRESSURE: "push" + "cognitive narrowing pressure" + "life cost"
    # Pressure now includes compression push (NCR), not just logistics burden
    pressure = _clamp(0.50 * lfc_val + 0.25 * ncr_val + 0.25 * vuln)

    # B) PULL: attracted to generativity, damped by high friction and low capacity
    # Pull is now REAL: driven by vitality (GI), moderated by logistics and capacity
    pull = _clamp(0.60 * gi_val + 0.20 * (1.0 - lfc_val) + 0.20 * cap_floor)

    # C) AGENCY DELTA: narrowing vs expanding
    # Agency delta tightens when compression is high (NCR narrows cognitive space)
    # High friction + high compression + high vulnerability → negative delta (space collapses)
    # low LFC + low NCR + high capacity → positive delta (space opens)
    agency_delta = _clamp_m11(0.45 - (0.75 * lfc_val + 0.55 * ncr_val + 0.55 * vuln))

    # D) DRIFT RISK: probability of slow capture
    # Drift risk now includes compression as capture accelerant
    # High NCR makes it easier to get pulled into a single-frame reality
    # IGNITION: High GI + High NCR = creative capture (fun capture)
    ignite = _clamp(ncr_val * gi_val)  # 0..1
    drift_risk = _clamp(
        0.40 * pressure + 0.20 * vuln + 0.15 * susc_vol + 0.15 * ncr_val + 0.10 * ignite
    )

    # Generate deterministic prompts based on thresholds
    notes: List[str] = []

    # Creative ignition (high GI + high NCR)
    if ignite > 0.55:
        notes.append(
            "Creative ignition detected: high novelty + high compression—watch for 'fun capture'."
        )

    # High generativity with low friction
    if gi_val > 0.65 and lfc_val < 0.35:
        notes.append("High generativity, low friction: fertile—build something.")

    # Compression warnings
    if ncr_val > 0.60:
        notes.append(
            "Totalizing frame detected: check for missing causes and alternative explanations."
        )

    # Standard warnings
    if pressure > 0.65:
        notes.append("High life-demand signal: check sleep/time capacity before engaging.")
    if agency_delta < -0.35:
        notes.append("Agency narrowing detected: watch for 'no alternatives' feeling.")
    if drift_risk > 0.60:
        notes.append("Elevated drift risk: avoid consuming when tired or isolated.")
    if float(loads.get("VL", 0.0)) > 0.50:
        notes.append("Urgency cues detected: delay action by ~24h if possible.")
    if float(loads.get("SL", 0.0)) > 0.40:
        notes.append("Social policing pressure detected: watch for loyalty tests.")

    return {
        "pressure": pressure,
        "pull": pull,
        "agency_delta": agency_delta,
        "drift_risk": drift_risk,
        "notes": notes[:5] if notes else ["Signals computed (v0.1)."],
    }
