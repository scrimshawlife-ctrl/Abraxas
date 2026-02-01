"""Rune adapter for forecast term class map loading capability.

Thin adapter layer exposing forecast.term_class_map.load via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.forecast.term_class_map import load_term_class_map as load_term_class_map_core


def load_term_class_map_deterministic(
    a2_phase_path: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term class map loading.

    Wraps existing load_term_class_map with provenance envelope.

    Args:
        a2_phase_path: Path to A2 phase artifact JSON
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with term_class_map, success status, and provenance
    """
    # Validate inputs
    if not isinstance(a2_phase_path, str) or not a2_phase_path:
        return {
            "success": False,
            "term_class_map": None,
            "not_computable": {
                "reason": "Invalid a2_phase_path: expected non-empty string",
                "missing_inputs": ["a2_phase_path"]
            },
            "provenance": None
        }

    # Call existing load_term_class_map function (pure, deterministic)
    try:
        term_class_map = load_term_class_map_core(a2_phase_path)
    except Exception as e:
        # Not computable - return structured error
        return {
            "success": False,
            "term_class_map": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "term_class_map": term_class_map},
        config={},
        inputs={"a2_phase_path": a2_phase_path},
        operation_id="forecast.term_class_map.load",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "success": True,
        "term_class_map": term_class_map,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["load_term_class_map_deterministic"]
