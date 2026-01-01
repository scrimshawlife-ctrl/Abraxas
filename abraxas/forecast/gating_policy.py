from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class GateDecision:
    version: str
    eeb_multiplier: float
    horizon_max: str
    evidence_escalation: str
    flags: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _bucket(dmx_overall: float) -> str:
    if dmx_overall >= 0.70:
        return "HIGH"
    if dmx_overall >= 0.40:
        return "MED"
    return "LOW"


def decide_gate(
    *,
    dmx_overall: float,
    attribution_strength: float,
    source_diversity: float,
    consensus_gap: float,
    manipulation_risk_mean: float,
) -> GateDecision:
    """
    Deterministic v0.1 gating:
    - DMX increases EEB and reduces max horizon.
    - Weak provenance escalates evidence requirements.
    - Nothing is filtered; this is constraint/labeling only.
    """
    bucket = _bucket(float(dmx_overall))
    flags: List[str] = []

    if bucket == "HIGH":
        eeb_mul = 1.35
        horizon_max = "months"
        flags.append("FOG_HIGH")
    elif bucket == "MED":
        eeb_mul = 1.15
        horizon_max = "years"
        flags.append("FOG_MED")
    else:
        eeb_mul = 1.00
        horizon_max = "years"
        flags.append("FOG_LOW")

    evidence = "none"
    if bucket in ("MED", "HIGH"):
        if attribution_strength < 0.75 or source_diversity < 0.60 or consensus_gap > 0.45:
            horizon_max = "months"
            evidence = "online_escalation"
            flags.append("PROVENANCE_WEAK_FOR_LONG_HORIZON")

    if manipulation_risk_mean >= 0.70:
        eeb_mul *= 1.20
        flags.append("TERM_RISK_HIGH")
    elif manipulation_risk_mean >= 0.40:
        eeb_mul *= 1.08
        flags.append("TERM_RISK_MED")

    if bucket == "HIGH" and (attribution_strength < 0.65 or source_diversity < 0.50):
        evidence = "offline_escalation"
        flags.append("OFFLINE_EVIDENCE_REQUIRED")

    return GateDecision(
        version="gate_policy.v0.1",
        eeb_multiplier=float(eeb_mul),
        horizon_max=horizon_max,
        evidence_escalation=evidence,
        flags=flags,
        provenance={"method": "decide_gate.v0.1", "dmx_bucket": bucket},
    )
