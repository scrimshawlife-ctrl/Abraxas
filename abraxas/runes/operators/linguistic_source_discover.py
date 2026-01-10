"""ABX-Rune Operator: LINGUISTIC_SOURCE_DISCOVER."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.linguistics.autopoiesis import propose_sources


class LinguisticDiscoverResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_linguistic_source_discover(tokens: List[str], *, strict_execution: bool = False) -> Dict[str, Any]:
    if strict_execution and tokens is None:
        raise NotImplementedError("LINGUISTIC_SOURCE_DISCOVER requires tokens")

    output = propose_sources(tokens=tokens)
    provenance = {
        "inputs_hash": sha256_hex(canonical_json({"tokens": tokens or []})),
        "candidate_hash": sha256_hex(canonical_json(output.get("candidates") or [])),
    }
    return LinguisticDiscoverResult(candidates=output.get("candidates") or [], provenance=provenance).model_dump()
