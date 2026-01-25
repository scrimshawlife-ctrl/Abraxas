"""ABX-Rune Operator: PROVENANCE_SEAL."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class ProvenanceSealResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    payload_hash: str
    inputs_hash: str
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_provenance_seal(payload: Any, *, strict_execution: bool = False) -> Dict[str, Any]:
    if payload is None:
        if strict_execution:
            raise NotImplementedError("PROVENANCE_SEAL requires payload")
        inputs_hash = sha256_hex(canonical_json({"payload": None}))
        return ProvenanceSealResult(
            payload_hash="",
            inputs_hash=inputs_hash,
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["payload"],
            },
            provenance={"payload_hash": ""},
        ).model_dump()

    payload_hash = sha256_hex(canonical_json(payload))
    inputs_hash = sha256_hex(canonical_json({"payload": payload}))
    provenance = {"payload_hash": payload_hash}
    return ProvenanceSealResult(payload_hash=payload_hash, inputs_hash=inputs_hash, provenance=provenance).model_dump()
