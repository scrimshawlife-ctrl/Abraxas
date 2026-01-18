"""ABX-Rune Operator: ϟ₁₁ COHESION_SCORE."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class CohesionResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    cohesion_score: Optional[float] = Field(None, description="Aggregate cohesion score")
    not_computable: bool = Field(False, description="True if cohesion cannot be computed")
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def apply_cohesion_score(synchronicity_envelopes: Dict[str, Any], *, strict_execution: bool = False) -> Dict[str, Any]:
    if synchronicity_envelopes is None:
        if strict_execution:
            raise NotImplementedError("COHESION_SCORE requires synchronicity_envelopes")
        result = CohesionResult(
            cohesion_score=None,
            not_computable=True,
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["synchronicity_envelopes"],
            },
            provenance={"inputs_hash": sha256_hex(canonical_json({"envelopes": []}))},
        )
        return result.model_dump()

    envelopes = (synchronicity_envelopes or {}).get("envelopes") or []
    scores = []
    for envelope in envelopes:
        metrics = (envelope.get("metrics") or {})
        rac = metrics.get("RAC")
        tci = metrics.get("TCI")
        sis = metrics.get("SIS")
        for val in (rac, tci, sis):
            if isinstance(val, (int, float)):
                scores.append(float(val))

    cohesion = _mean(scores)
    not_computable = cohesion is None
    provenance = {
        "inputs_hash": sha256_hex(canonical_json({"envelopes": envelopes})),
        "metrics": ["RAC", "TCI", "SIS"],
    }

    result = CohesionResult(
        cohesion_score=cohesion,
        not_computable=not_computable,
        not_computable_detail=None if not not_computable else {
            "reason": "insufficient metrics",
            "missing_inputs": ["synchronicity_envelopes"],
        },
        provenance=provenance,
    )
    return result.model_dump()
