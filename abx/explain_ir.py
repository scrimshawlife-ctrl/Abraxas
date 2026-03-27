from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from abx.core.types import EvidenceRef


class ExplainProvenance(BaseModel):
    observed: list[str] = Field(default_factory=list)
    inferred: list[str] = Field(default_factory=list)
    speculative: list[str] = Field(default_factory=list)


class ExplainIR(BaseModel):
    """Canonical explainability payload; UI must consume this shape."""

    explain_rune_id: str
    event_type: str
    target_id: Optional[str] = None
    summary: str
    metric_logic: Optional[dict[str, Any]] = None
    evidence: list[EvidenceRef] = Field(default_factory=list)
    provenance: ExplainProvenance
    confidence: float = Field(..., ge=0.0, le=1.0)
