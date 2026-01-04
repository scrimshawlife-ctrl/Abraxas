"""Rune adapter for Oracle V2 pipeline.

Thin adapter layer exposing oracle.v2 via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.oracle.v2.pipeline import run_oracle as run_oracle_core


def run_oracle_deterministic(
    run_id: str,
    observations: list[dict],
    config: Optional[dict] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible oracle V2 runner.

    Wraps existing run_oracle with provenance envelope and validation.

    Args:
        run_id: Unique run identifier
        observations: List of observation dictionaries
        config: Optional configuration dictionary
        seed: Optional deterministic seed

    Returns:
        Dictionary with oracle_output, provenance, and optionally not_computable
    """
    config = config or {}

    # Call existing oracle pipeline (no changes to core logic)
    try:
        oracle_output = run_oracle_core(
            run_id=run_id,
            observations=observations,
            config=config,
            seed=seed
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "oracle_output": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []  # Could be extended to detect missing fields
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result=oracle_output,
        config=config,
        inputs={"run_id": run_id, "observations": observations},
        operation_id="oracle.v2.run",
        seed=seed
    )

    # Rename 'result' key to 'oracle_output' for clarity
    return {
        "oracle_output": envelope["result"],
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["run_oracle_deterministic"]
