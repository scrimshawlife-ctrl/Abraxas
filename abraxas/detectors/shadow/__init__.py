"""Shadow Detectors

Three shadow detectors that feed shadow structural metrics as evidence only:
1. Compliance vs Remix Detector
2. Meta-Awareness Detector
3. Negative Space / Silence Detector

All detectors are SHADOW-ONLY (observe, never influence decisions).
"""

from abraxas.detectors.shadow.types import (
    DetectorId,
    DetectorProvenance,
    DetectorStatus,
    DetectorValue,
    clamp01,
)

__all__ = [
    "DetectorId",
    "DetectorStatus",
    "DetectorValue",
    "DetectorProvenance",
    "clamp01",
]
