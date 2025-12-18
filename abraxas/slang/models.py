"""Data models for Slang Emergence Engine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class SlangToken(BaseModel):
    """A single token in the slang analysis."""

    token: str = Field(..., description="Token text")
    position: int = Field(..., description="Position in source")
    features: dict[str, float] = Field(default_factory=dict, description="Token features")


class OperatorReadout(BaseModel):
    """Output from an operator applied to text/frame."""

    operator_id: str = Field(..., description="Operator that produced this readout")
    label: str = Field(..., description="Classification or label")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    features: dict[str, Any] = Field(default_factory=dict, description="Additional features")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Operator-specific metadata")


class SlangCluster(BaseModel):
    """
    A cluster of related tokens/patterns detected by SEE.

    Represents emergent slang patterns or linguistic structures.
    """

    cluster_id: str = Field(..., description="Unique cluster identifier")
    tokens: list[SlangToken] = Field(default_factory=list, description="Tokens in cluster")
    features: dict[str, float] = Field(default_factory=dict, description="Cluster-level features")
    window: tuple[datetime, datetime] | None = Field(
        default=None, description="Time window for this cluster"
    )
    evidence_refs: list[str] = Field(
        default_factory=list, description="Event IDs that contributed to this cluster"
    )
    operator_readouts: list[OperatorReadout] = Field(
        default_factory=list, description="Readouts from applied operators"
    )
    drift_tags: list[str] = Field(
        default_factory=list, description="Drift classification tags (e.g., 'VBM_CLASS')"
    )
    vbm_phase: str | None = Field(default=None, description="VBM phase if VBM drift detected")
    vbm_score: float | None = Field(default=None, description="VBM drift score [0, 1]")
    vbm_lattice_hits: list[str] = Field(
        default_factory=list, description="VBM operator lattice hits"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def add_readout(self, readout: OperatorReadout) -> None:
        """Add an operator readout to this cluster."""
        self.operator_readouts.append(readout)
