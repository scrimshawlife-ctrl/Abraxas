"""Rune adapter for memetic DMX capabilities.

Thin adapter layer exposing memetic.dmx_context operations via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope, hash_canonical_json
from abraxas.memetic.dmx_context import load_dmx_context as load_dmx_context_core


def load_dmx_context_deterministic(
    mwr_path: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible DMX context loading from MWR artifact.

    Wraps existing load_dmx_context with provenance envelope.

    Args:
        mwr_path: Path to MWR artifact file
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with DMX context, success status, and provenance
    """
    # Validate inputs
    if not mwr_path:
        return {
            "success": False,
            "dmx_context": None,
            "not_computable": {
                "reason": "Missing required parameter: mwr_path",
                "missing_inputs": ["mwr_path"]
            },
            "provenance": None
        }

    # Call existing load_dmx_context function (deterministic)
    try:
        dmx_context = load_dmx_context_core(mwr_path)
    except Exception as e:
        # Not computable - return structured error
        return {
            "success": False,
            "dmx_context": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "dmx_context": dmx_context},
        config={},
        inputs={"mwr_path": str(mwr_path)},
        operation_id="memetic.dmx_context.load",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "success": True,
        "dmx_context": dmx_context,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["load_dmx_context_deterministic"]
