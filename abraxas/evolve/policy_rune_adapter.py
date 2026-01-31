"""Rune adapter for evolve policy capabilities.

Thin adapter layer exposing evolve.policy operations via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope, hash_canonical_json
from abraxas.evolve.non_truncation import enforce_non_truncation as enforce_non_truncation_core


def enforce_non_truncation_deterministic(
    artifact: Dict[str, Any],
    raw_full: Any,
    raw_full_path: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible non-truncation policy enforcement.

    Wraps existing enforce_non_truncation with provenance envelope.

    Args:
        artifact: Base artifact dictionary to enhance
        raw_full: Full raw data to preserve (embed or reference)
        raw_full_path: Optional path to write raw_full to disk
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with enhanced artifact, success status, and provenance
    """
    # Validate inputs
    if not isinstance(artifact, dict):
        return {
            "success": False,
            "artifact": None,
            "not_computable": {
                "reason": "Invalid artifact: must be dictionary",
                "missing_inputs": ["artifact"]
            },
            "provenance": None
        }

    if raw_full is None:
        return {
            "success": False,
            "artifact": None,
            "not_computable": {
                "reason": "Missing required input: raw_full",
                "missing_inputs": ["raw_full"]
            },
            "provenance": None
        }

    # Call existing enforce_non_truncation function
    try:
        enhanced_artifact = enforce_non_truncation_core(
            artifact=artifact,
            raw_full=raw_full,
            raw_full_path=raw_full_path
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "success": False,
            "artifact": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "artifact": enhanced_artifact},
        config={},
        inputs={
            "artifact_hash": hash_canonical_json(artifact),
            "raw_full_hash": hash_canonical_json(raw_full) if isinstance(raw_full, (dict, list)) else None,
            "raw_full_path": raw_full_path
        },
        operation_id="evolve.policy.enforce_non_truncation",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "success": True,
        "artifact": enhanced_artifact,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["enforce_non_truncation_deterministic"]
