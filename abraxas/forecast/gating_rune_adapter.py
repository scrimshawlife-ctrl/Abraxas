"""Rune adapter for forecast gating capabilities.

Thin adapter layer exposing forecast.gating operations via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope, hash_canonical_json
from abraxas.forecast.gating_policy import decide_gate as decide_gate_core


def decide_gate_deterministic(
    dmx_overall: float,
    attribution_strength: float,
    source_diversity: float,
    consensus_gap: float,
    manipulation_risk_mean: float,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible gating policy decision.

    Wraps existing decide_gate with provenance envelope.

    Args:
        dmx_overall: Overall DMX score [0,1]
        attribution_strength: Attribution strength [0,1]
        source_diversity: Source diversity [0,1]
        consensus_gap: Consensus gap [0,1]
        manipulation_risk_mean: Mean manipulation risk [0,1]
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with gate decision, success status, and provenance
    """
    # Validate inputs
    required_params = {
        "dmx_overall": dmx_overall,
        "attribution_strength": attribution_strength,
        "source_diversity": source_diversity,
        "consensus_gap": consensus_gap,
        "manipulation_risk_mean": manipulation_risk_mean
    }

    missing = [k for k, v in required_params.items() if v is None]
    if missing:
        return {
            "success": False,
            "gate_decision": None,
            "not_computable": {
                "reason": f"Missing required parameters: {', '.join(missing)}",
                "missing_inputs": missing
            },
            "provenance": None
        }

    # Call existing decide_gate function (pure, deterministic)
    try:
        gate_decision = decide_gate_core(
            dmx_overall=float(dmx_overall),
            attribution_strength=float(attribution_strength),
            source_diversity=float(source_diversity),
            consensus_gap=float(consensus_gap),
            manipulation_risk_mean=float(manipulation_risk_mean)
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "success": False,
            "gate_decision": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "gate_decision": gate_decision.to_dict()},
        config={},
        inputs={
            "dmx_overall": float(dmx_overall),
            "attribution_strength": float(attribution_strength),
            "source_diversity": float(source_diversity),
            "consensus_gap": float(consensus_gap),
            "manipulation_risk_mean": float(manipulation_risk_mean)
        },
        operation_id="forecast.gating.decide_gate",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "success": True,
        "gate_decision": gate_decision.to_dict(),
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["decide_gate_deterministic"]
