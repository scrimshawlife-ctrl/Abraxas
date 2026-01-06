"""Rune adapter for evolution ledger capabilities.

Thin adapter layer exposing evolve.ledger via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope, hash_canonical_json
from abraxas.evolve.ledger import append_chained_jsonl as append_chained_jsonl_core


def append_ledger_deterministic(
    ledger_path: str,
    record: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible chained JSONL ledger appender.

    Wraps existing append_chained_jsonl with provenance envelope and validation.
    Returns the step_hash for hash chain verification.

    Args:
        ledger_path: Path to JSONL ledger file (created if doesn't exist)
        record: Record to append (will be augmented with prev_hash and step_hash)
        seed: Optional deterministic seed (unused for ledger append, kept for consistency)

    Returns:
        Dictionary with step_hash, prev_hash, provenance, and optionally not_computable
    """
    # Validate inputs
    if not ledger_path or not isinstance(ledger_path, str):
        return {
            "step_hash": None,
            "prev_hash": None,
            "not_computable": {
                "reason": "Invalid ledger_path: must be non-empty string",
                "missing_inputs": ["ledger_path"]
            },
            "provenance": None
        }

    if not record or not isinstance(record, dict):
        return {
            "step_hash": None,
            "prev_hash": None,
            "not_computable": {
                "reason": "Invalid record: must be non-empty dictionary",
                "missing_inputs": ["record"]
            },
            "provenance": None
        }

    # Get previous hash before appending (for return value)
    try:
        path = Path(ledger_path)
        if not path.exists():
            prev_hash = "genesis"
        else:
            lines = path.read_text().splitlines()
            if not lines:
                prev_hash = "genesis"
            else:
                import json
                last = json.loads(lines[-1])
                prev_hash = last.get("step_hash", "genesis")
    except Exception as e:
        return {
            "step_hash": None,
            "prev_hash": None,
            "not_computable": {
                "reason": f"Failed to read ledger: {str(e)}",
                "missing_inputs": []
            },
            "provenance": None
        }

    # Call existing append_chained_jsonl function (no changes to core logic)
    try:
        append_chained_jsonl_core(ledger_path, record)
    except Exception as e:
        # Not computable - return structured error
        return {
            "step_hash": None,
            "prev_hash": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Compute step_hash for the record we just appended
    # Replicate the logic from append_chained_jsonl
    augmented_record = dict(record)
    augmented_record["prev_hash"] = prev_hash
    step_hash = hash_canonical_json(augmented_record)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"step_hash": step_hash, "prev_hash": prev_hash},
        config={},
        inputs={"ledger_path": ledger_path, "record": record},
        operation_id="evolve.ledger.append",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "step_hash": step_hash,
        "prev_hash": prev_hash,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = [
    "append_ledger_deterministic"
]
