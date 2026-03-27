from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EvidenceRef(BaseModel):
    """Typed evidence reference for explainability and provenance chains."""

    id: str = Field(..., description="Stable evidence identifier")
    source: str = Field(..., description="Evidence source namespace")
    pointer: str = Field(..., description="Path, URI, or ledger pointer")
    kind: Literal["artifact", "ledger", "observation", "inference"] = "artifact"


class CanonicalVector(BaseModel):
    """Normalized vector contract for ingest/memetic surfaces."""

    id: str = Field(..., description="Vector identifier")
    normalized_vectors: Dict[str, float] = Field(default_factory=dict)


class ArtifactLineage(BaseModel):
    """Lineage references required for reconstruction of runtime chains."""

    run_id: str
    upstream_artifact_ids: List[str] = Field(default_factory=list)
    upstream_ledger_ids: List[str] = Field(default_factory=list)
    emitted_by_rune_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
