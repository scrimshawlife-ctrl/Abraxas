"""Shadow Detector Types

Defines base types and enums for shadow detectors.
These detectors feed shadow structural metrics as evidence only.

CRITICAL INVARIANTS:
- All detectors are SHADOW-ONLY (observe, never influence)
- Deterministic outputs with stable ordering
- Provenance includes used_keys, missing_keys, history_len
- not_computable status when required inputs missing
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DetectorId(str, Enum):
    """Detector identifiers."""

    COMPLIANCE_REMIX = "compliance_remix"
    META_AWARENESS = "meta_awareness"
    NEGATIVE_SPACE = "negative_space"


class DetectorStatus(str, Enum):
    """Detector computation status."""

    OK = "ok"
    NOT_COMPUTABLE = "not_computable"


class DetectorProvenance(BaseModel):
    """Provenance tracking for detector computation."""

    detector_id: str
    used_keys: list[str] = Field(default_factory=list)
    missing_keys: list[str] = Field(default_factory=list)
    history_len: int = 0
    envelope_version: Optional[str] = None
    inputs_hash: str
    config_hash: str
    computed_at_utc: str
    seed_compliant: bool = True
    no_influence_guarantee: bool = True

    class Config:
        frozen = True


class DetectorValue(BaseModel):
    """Result from a shadow detector computation.

    All values and subscores are clamped to [0.0, 1.0].
    """

    id: DetectorId
    status: DetectorStatus
    value: Optional[float] = Field(None, ge=0.0, le=1.0)
    subscores: dict[str, float] = Field(default_factory=dict)
    missing_keys: list[str] = Field(default_factory=list)
    evidence: Optional[dict[str, Any]] = None
    provenance: DetectorProvenance
    bounds: tuple[float, float] = Field(default=(0.0, 1.0))

    class Config:
        frozen = True

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to ensure deterministic dict ordering."""
        data = super().model_dump(**kwargs)
        # Sort subscores
        if "subscores" in data and isinstance(data["subscores"], dict):
            data["subscores"] = dict(sorted(data["subscores"].items()))
        # Sort evidence if present
        if "evidence" in data and isinstance(data["evidence"], dict):
            data["evidence"] = dict(sorted(data["evidence"].items()))
        # Sort missing_keys
        if "missing_keys" in data and isinstance(data["missing_keys"], list):
            data["missing_keys"] = sorted(data["missing_keys"])
        return data


def clamp01(value: float) -> float:
    """Clamp value to [0.0, 1.0] range."""
    return max(0.0, min(1.0, value))
