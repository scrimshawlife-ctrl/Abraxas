"""ABX-Rune Operator: ϟ₁₃ NO_DOMAIN_PRIOR."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class DomainPriorResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    compliance: bool = Field(..., description="Compliance flag")
    violations: List[str] = Field(default_factory=list)
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def _scan_for_domain_priors(payload: Any) -> List[str]:
    violations: List[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = key.lower()
            if "legitimacy" in lowered or "pseudoscience" in lowered or "tier" in lowered:
                violations.append(f"field:{key}")
            if "domain_prior" in lowered or "exclude_domain" in lowered:
                violations.append(f"field:{key}")
            violations.extend(_scan_for_domain_priors(value))
    elif isinstance(payload, list):
        for item in payload:
            violations.extend(_scan_for_domain_priors(item))
    elif isinstance(payload, str):
        lowered = payload.lower()
        if "pseudoscience" in lowered or "illegitimate" in lowered:
            violations.append("string:domain_prior")
    return sorted(set(violations))


def apply_no_domain_prior(payload: Any, *, strict_execution: bool = False) -> Dict[str, Any]:
    if payload is None:
        if strict_execution:
            raise NotImplementedError("NO_DOMAIN_PRIOR requires payload")
        provenance = {"inputs_hash": sha256_hex(canonical_json({"payload": None}))}
        return DomainPriorResult(
            compliance=False,
            violations=[],
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["payload"],
            },
            provenance=provenance,
        ).model_dump()

    violations = _scan_for_domain_priors(payload)
    compliance = len(violations) == 0
    provenance = {"inputs_hash": sha256_hex(canonical_json({"payload": payload}))}
    return DomainPriorResult(
        compliance=compliance,
        violations=violations,
        provenance=provenance,
    ).model_dump()
