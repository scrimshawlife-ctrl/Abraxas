"""Rune adapter for evolve ledger capabilities.

Thin adapter layer exposing evolve.ledger via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path

from abraxas.core.provenance import canonical_envelope
from abraxas.evolve.ledger import append_chained_jsonl as append_chained_jsonl_core


def append_ledger_deterministic(
    path: str,
    record: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible chained JSONL append operation.

    Wraps existing append_chained_jsonl with provenance envelope.

    Args:
        path: Path to the JSONL ledger file
        record: Dictionary record to append
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with success status, step_hash, and provenance
    """
    # Validate inputs
    if not path:
        return {
            "success": False,
            "step_hash": None,
            "not_computable": {
                "reason": "Empty path provided",
                "missing_inputs": ["path"]
            },
            "provenance": None
        }

    if not record or not isinstance(record, dict):
        return {
            "success": False,
            "step_hash": None,
            "not_computable": {
                "reason": "Invalid record: must be non-empty dictionary",
                "missing_inputs": ["record"]
            },
            "provenance": None
        }

    # Call existing append_chained_jsonl function (side-effect operation)
    try:
        append_chained_jsonl_core(path, record)

        # Read back the step_hash that was written
        from abraxas.evolve.ledger import _get_last_hash
        ledger_path = Path(path)
        step_hash = _get_last_hash(ledger_path)

    except Exception as e:
        # Not computable - return structured error
        return {
            "success": False,
            "step_hash": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "step_hash": step_hash},
        config={},
        inputs={"path": path, "record_hash": hash(frozenset(record.items()))},  # Don't include full record in provenance
        operation_id="evolve.ledger.append",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "success": True,
        "step_hash": step_hash,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["append_ledger_deterministic"]
