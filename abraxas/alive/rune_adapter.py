"""Rune adapter for ALIVE capabilities.

Deterministic wrappers for ALIVE engine execution and model validation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.alive import ALIVEEngine
from abraxas.alive.models import ALIVERunInput, ALIVEFieldSignature
from abraxas.core.provenance import canonical_envelope


def run_alive_engine_deterministic(
    subjectId: str,
    tier: str,
    corpusConfig: Dict[str, Any],
    metricConfig: Optional[Dict[str, Any]] = None,
    registry_path: Optional[str] = None,
    seed: Optional[int] = None,
    strict_execution: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run ALIVE engine with deterministic provenance wrapper."""
    _ = strict_execution
    run_input = ALIVERunInput(
        subjectId=subjectId,
        tier=tier,
        corpusConfig=corpusConfig,
        metricConfig=metricConfig,
    )
    engine = ALIVEEngine(registry_path=registry_path)
    signature = engine.run(run_input)
    signature_dict = signature.model_dump()

    envelope = canonical_envelope(
        result=signature_dict,
        config={"registry_path": registry_path},
        inputs={
            "subjectId": subjectId,
            "tier": tier,
            "corpusConfig": corpusConfig,
            "metricConfig": metricConfig,
        },
        operation_id="alive.engine.run",
        seed=seed,
    )

    return {
        "field_signature": signature_dict,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


def serialize_alive_field_signature_deterministic(
    field_signature: Dict[str, Any],
    seed: Optional[int] = None,
    strict_execution: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Validate and normalize ALIVE field signature payloads."""
    _ = strict_execution
    signature = ALIVEFieldSignature(**field_signature)
    signature_dict = signature.model_dump()

    envelope = canonical_envelope(
        result=signature_dict,
        config={},
        inputs={"field_signature": field_signature},
        operation_id="alive.models.serialize",
        seed=seed,
    )

    return {
        "field_signature": signature_dict,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }
