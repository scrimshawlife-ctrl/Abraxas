"""ABX-Rune Operator: ϟ₉ INFLUENCE_WEIGHT."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class InfluenceWeightBundle(BaseModel):
    """Influence weights derived from ICS bundles."""

    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    weights: Dict[str, Optional[float]] = Field(default_factory=dict)
    not_computable: List[str] = Field(default_factory=list)
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def _normalize_metric(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def apply_influence_weight(ics_bundle: Dict[str, Any], *, strict_execution: bool = False) -> Dict[str, Any]:
    """Apply INFLUENCE_WEIGHT rune operator.

    Args:
        ics_bundle: Output from influence detect
        strict_execution: If True, raises NotImplementedError for unimplemented operators
    """
    if ics_bundle is None:
        if strict_execution:
            raise NotImplementedError("INFLUENCE_WEIGHT requires ics_bundle")
        provenance = {
            "inputs_hash": sha256_hex(canonical_json({"ics_bundle": {}})),
            "metrics": ["CVP", "TLL", "RD", "CDEC", "RRS"],
        }
        bundle = InfluenceWeightBundle(
            weights={},
            not_computable=["ics_bundle"],
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["ics_bundle"],
            },
            provenance=provenance,
        )
        return bundle.model_dump()

    ics = (ics_bundle or {}).get("ics") or {}
    weights: Dict[str, Optional[float]] = {}
    not_comp: List[str] = []

    for domain, metrics in ics.items():
        vals = []
        for key in ("CVP", "TLL", "RD", "CDEC", "RRS"):
            val = _normalize_metric(metrics.get(key))
            if val is not None:
                vals.append(val)
        score = _mean(vals)
        if score is None:
            not_comp.append(domain)
        weights[domain] = score

    provenance = {
        "inputs_hash": sha256_hex(canonical_json({"ics_bundle": ics_bundle or {}})),
        "metrics": ["CVP", "TLL", "RD", "CDEC", "RRS"],
    }

    bundle = InfluenceWeightBundle(weights=weights, not_computable=sorted(not_comp), provenance=provenance)
    return bundle.model_dump()
