"""Rune adapter for artifacts capabilities.

Thin adapter layer exposing artifacts.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.artifacts.proof_bundle import generate_proof_bundle as generate_proof_bundle_core
from abraxas.core.provenance import canonical_envelope


def generate_proof_bundle_deterministic(
    *,
    run_id: str,
    artifacts: Dict[str, str],
    bundle_root: str = "out/proof_bundles",
    ledger_pointer: Optional[Dict[str, Any]] = None,
    ts: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible proof bundle generator.

    Wraps existing generate_proof_bundle with provenance envelope.

    Args:
        run_id: Run identifier
        artifacts: Mapping of artifact labels to file paths
        bundle_root: Root directory for bundles
        ledger_pointer: Optional ledger pointer mapping
        ts: Optional timestamp override
        seed: Optional deterministic seed (unused, kept for consistency)

    Returns:
        Dictionary with bundle paths, provenance, and not_computable (always None)
    """
    result = generate_proof_bundle_core(
        run_id=run_id,
        artifacts=artifacts,
        bundle_root=bundle_root,
        ledger_pointer=ledger_pointer,
        ts=ts,
    )

    envelope = canonical_envelope(
        result=result,
        config={},
        inputs={
            "run_id": run_id,
            "artifacts": artifacts,
            "bundle_root": bundle_root,
            "ledger_pointer": ledger_pointer or {},
            "ts": ts,
        },
        operation_id="artifacts.proof_bundle.generate",
        seed=seed,
    )

    return {
        "bundle": result,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


__all__ = ["generate_proof_bundle_deterministic"]
