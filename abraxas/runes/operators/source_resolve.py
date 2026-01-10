"""ABX-Rune Operator: SOURCE_RESOLVE."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.atlas import build_source_atlas, resolve_sources, list_sources


class SourceResolveResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_source_resolve(source_ids: List[str], *, strict_execution: bool = False) -> Dict[str, Any]:
    if strict_execution and source_ids is None:
        raise NotImplementedError("SOURCE_RESOLVE requires source_ids")

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
