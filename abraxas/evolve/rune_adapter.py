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


def enforce_non_truncation_deterministic(
    artifact: Optional[Dict[str, Any]] = None,
    raw_full: Any = None,
    raw_full_path: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Rune-compatible non-truncation policy enforcement.

    Ensures artifact retains full raw data (either embedded or via path reference).
    SEED Compliant: Deterministic, provenance-tracked.
    """
    import json as _json

    # Validate inputs
    if artifact is None or not isinstance(artifact, dict):
        return {
            "artifact": None,
            "provenance": None,
            "not_computable": {
                "reason": "Invalid artifact: must be a non-None dictionary",
                "missing_inputs": ["artifact"],
            },
        }

    if raw_full is None:
        return {
            "artifact": None,
            "provenance": None,
            "not_computable": {
                "reason": "Invalid raw_full: must be non-None",
                "missing_inputs": ["raw_full"],
            },
        }

    # Build enriched artifact (preserve existing fields)
    enriched = dict(artifact)

    # Update policy (merge with existing)
    policy = dict(enriched.get("policy", {}) or {})
    policy["non_truncation"] = True
    enriched["policy"] = policy

    # Embed raw_full or write to path
    if raw_full_path:
        # Write to disk, reference by path
        p = Path(raw_full_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            _json.dump(raw_full, f, sort_keys=True, indent=2)
        enriched["raw_full_path"] = str(raw_full_path)
    else:
        enriched["raw_full"] = raw_full

    # Add default structural fields if missing
    enriched.setdefault("views", {})
    enriched.setdefault("flags", {})
    enriched.setdefault("metrics", {})

    # Build provenance envelope
    envelope = canonical_envelope(
        result={"artifact": enriched},
        config={},
        inputs={"artifact_keys": sorted(artifact.keys()), "raw_full_type": type(raw_full).__name__},
        operation_id="evolve.policy.enforce_non_truncation",
        seed=seed,
    )

    # Add convenience aliases expected by tests
    prov = dict(envelope["provenance"])
    if "inputs_sha256" in prov:
        prov["inputs_hash"] = prov["inputs_sha256"]
    if "timestamp_utc" in prov:
        prov["timestamp"] = prov["timestamp_utc"]

    return {
        "artifact": enriched,
        "provenance": prov,
        "not_computable": envelope["not_computable"],
    }


__all__ = ["append_ledger_deterministic", "enforce_non_truncation_deterministic"]
