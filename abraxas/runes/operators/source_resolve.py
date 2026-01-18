"""ABX-Rune Operator: SOURCE_RESOLVE."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.atlas import build_source_atlas, resolve_sources, list_sources


class SourceResolveResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_source_resolve(source_ids: List[str], *, strict_execution: bool = False) -> Dict[str, Any]:
    if source_ids is None:
        if strict_execution:
            raise NotImplementedError("SOURCE_RESOLVE requires source_ids")
        provenance = {
            "atlas_hash": build_source_atlas().atlas_hash(),
            "inputs_hash": sha256_hex(canonical_json({"source_ids": []})),
            "record_hashes": [],
        }
        return SourceResolveResult(
            sources=[],
            missing=[],
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["source_ids"],
            },
            provenance=provenance,
        ).model_dump()

    atlas = build_source_atlas()
    resolved, missing = resolve_sources(source_ids or [])
    if not resolved:
        resolved = list_sources() if not source_ids else resolved
    payload = [record.canonical_payload() for record in resolved]
    provenance = {
        "atlas_hash": atlas.atlas_hash(),
        "inputs_hash": sha256_hex(canonical_json({"source_ids": source_ids or []})),
        "record_hashes": [record.record_hash() for record in resolved],
    }
    return SourceResolveResult(sources=payload, missing=missing, provenance=provenance).model_dump()
