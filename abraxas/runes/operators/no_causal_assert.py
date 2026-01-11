"""ABX-Rune Operator: ϟ₁₂ NO_CAUSAL_ASSERT."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class CausalAssertResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    compliance: bool = Field(..., description="Compliance flag")
    violations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


def _scan_for_causal_claims(payload: Any) -> List[str]:
    violations: List[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if "causal" in key.lower() or "cause" in key.lower():
                violations.append(f"field:{key}")
            violations.extend(_scan_for_causal_claims(value))
    elif isinstance(payload, list):
        for item in payload:
            violations.extend(_scan_for_causal_claims(item))
    elif isinstance(payload, str):
        if "causal" in payload.lower() or "cause" in payload.lower():
            violations.append("string:causal")
    return sorted(set(violations))


def apply_no_causal_assert(payload: Any, *, strict_execution: bool = False) -> Dict[str, Any]:
    if strict_execution and payload is None:
        raise NotImplementedError("NO_CAUSAL_ASSERT requires payload")

    violations = _scan_for_causal_claims(payload)
    compliance = len(violations) == 0
    provenance = {"inputs_hash": sha256_hex(canonical_json({"payload": payload}))}
    return CausalAssertResult(compliance=compliance, violations=violations, provenance=provenance).model_dump()
