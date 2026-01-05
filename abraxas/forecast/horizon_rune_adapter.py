"""Rune adapter for forecast horizon capabilities.

Thin adapter layer exposing forecast.horizon operations via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope, hash_canonical_json
from abraxas.forecast.horizon_bins import horizon_bucket as horizon_bucket_core


def horizon_bucket_deterministic(
    horizon: Any,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible horizon bucket normalization.

    Wraps existing horizon_bucket with provenance envelope.

    Args:
        horizon: Horizon value to normalize (string, int, float, or any type)
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with normalized bucket, success status, and provenance
    """
    # Call existing horizon_bucket function (pure, deterministic)
    try:
        bucket = horizon_bucket_core(horizon)
    except Exception as e:
        # Not computable - return structured error
        return {
            "success": False,
            "bucket": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "bucket": bucket},
        config={},
        inputs={"horizon": str(horizon) if horizon is not None else None},
        operation_id="forecast.horizon.bucket",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "success": True,
        "bucket": bucket,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["horizon_bucket_deterministic"]
