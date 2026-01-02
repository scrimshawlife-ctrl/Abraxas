"""
Shadow Detector Base Types.

Defines the core types and interfaces for shadow detectors.
All shadow detectors must be deterministic and include provenance.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib
import json


class DetectorStatus(str, Enum):
    OK = "computed"
    NOT_COMPUTABLE = "not_computable"
    ERROR = "error"


def clamp01(x: float) -> float:
    try:
        xf = float(x)
    except Exception:
        return 0.0
    if xf <= 0.0:
        return 0.0
    if xf >= 1.0:
        return 1.0
    return xf


class DetectorOutput(BaseModel):
    """
    Lightweight detector output used by `tests/test_shadow_detectors_*`.

    Contract:
      - `value` and all `subscores` are clamped to [0, 1]
      - `missing_keys` is sorted for determinism
      - `subscores` keys are sorted for determinism
    """

    status: DetectorStatus = Field(..., description="OK / NOT_COMPUTABLE / ERROR")
    value: Optional[float] = Field(None, description="Main detector value in [0,1]")
    subscores: Dict[str, float] = Field(default_factory=dict, description="Subscores in [0,1]")
    missing_keys: List[str] = Field(default_factory=list, description="Sorted list of missing input keys")
    bounds: Tuple[float, float] = Field(default=(0.0, 1.0), description="Output bounds")


class ShadowEvidence(BaseModel):
    """
    Evidence bundle from a shadow detector.

    Evidence is attached as annotations to shadow metrics but does NOT
    influence prediction unless the detector is explicitly PROMOTED.
    """
    detector_name: str = Field(..., description="Name of the detector")
    signal_strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength [0,1]")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in detection [0,1]")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional evidence metadata")

    class Config:
        frozen = True


class ShadowDetectorResult(BaseModel):
    """
    Result from a shadow detector execution.

    Includes deterministic provenance via SHA-256 hash.
    """
    detector_name: str = Field(..., description="Detector identifier")
    status: DetectorStatus = Field(..., description="Computation status")
    evidence: Optional[ShadowEvidence] = Field(None, description="Evidence bundle if computed")
    error_message: Optional[str] = Field(None, description="Error message if status=error")

    # Provenance
    inputs_hash: str = Field(..., description="SHA-256 hash of inputs")
    timestamp_utc: str = Field(..., description="ISO8601 timestamp (Z)")
    version: str = Field(default="0.1.0", description="Detector version")

    @staticmethod
    def now_iso_z() -> str:
        """Return current time in ISO8601 format with Z timezone."""
        return datetime.utcnow().isoformat() + "Z"

    @staticmethod
    def hash_inputs(inputs: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of inputs in canonical form."""
        canonical = json.dumps(inputs, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def compute_provenance_hash(self) -> str:
        """Compute SHA-256 hash of this result for provenance chain."""
        data = {
            "detector_name": self.detector_name,
            "status": self.status,
            "evidence": self.evidence.model_dump() if self.evidence else None,
            "inputs_hash": self.inputs_hash,
            "timestamp_utc": self.timestamp_utc,
            "version": self.version,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    class Config:
        frozen = True


class ShadowDetectorBase:
    """
    Base class for all shadow detectors.

    Detectors must:
    1. Be deterministic (same inputs → same outputs)
    2. Include provenance (SHA-256 hashes)
    3. Handle missing inputs gracefully (return not_computable)
    4. Validate outputs are in valid ranges
    5. Never influence prediction directly
    """

    def __init__(self, name: str, version: str = "0.1.0"):
        self.name = name
        self.version = version

    def detect(self, inputs: Dict[str, Any]) -> ShadowDetectorResult:
        """
        Run detection on inputs.

        Args:
            inputs: Dictionary of input data

        Returns:
            ShadowDetectorResult with status and optional evidence
        """
        raise NotImplementedError("Subclasses must implement detect()")

    def _validate_inputs(self, inputs: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Validate that all required keys are present in inputs.

        Args:
            inputs: Input dictionary
            required_keys: List of required key names

        Returns:
            True if all keys present, False otherwise
        """
        return all(key in inputs for key in required_keys)

    def _create_result(
        self,
        inputs: Dict[str, Any],
        status: DetectorStatus,
        evidence: Optional[ShadowEvidence] = None,
        error_message: Optional[str] = None,
    ) -> ShadowDetectorResult:
        """
        Create a ShadowDetectorResult with provenance.

        Args:
            inputs: Input dictionary (for hash)
            status: Computation status
            evidence: Optional evidence bundle
            error_message: Optional error message

        Returns:
            ShadowDetectorResult
        """
        return ShadowDetectorResult(
            detector_name=self.name,
            status=status,
            evidence=evidence,
            error_message=error_message,
            inputs_hash=ShadowDetectorResult.hash_inputs(inputs),
            timestamp_utc=ShadowDetectorResult.now_iso_z(),
            version=self.version,
        )
