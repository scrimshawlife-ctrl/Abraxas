"""Rune adapter for forecast policy candidates capability.

Thin adapter layer exposing forecast.policy_candidates.candidates_v0_1 via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.forecast.policy_candidates import candidates_v0_1 as candidates_v0_1_core


def candidates_v0_1_deterministic(
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible policy candidates retrieval.

    Wraps existing candidates_v0_1 with provenance envelope.

    Args:
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with policy_candidates, success status, and provenance
    """
    # Call existing candidates_v0_1 function (pure, deterministic, no inputs)
    try:
        policy_candidates = candidates_v0_1_core()
    except Exception as e:
        return {
            "success": False,
            "policy_candidates": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "policy_candidates": policy_candidates},
        config={},
        inputs={},
        operation_id="forecast.policy.candidates_v0_1",
        seed=seed
    )

    return {
        "success": True,
        "policy_candidates": policy_candidates,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["candidates_v0_1_deterministic"]
