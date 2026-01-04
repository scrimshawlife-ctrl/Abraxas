"""
Shadow Detectors - Observe-only pattern detectors.

CRITICAL DESIGN CONSTRAINT:
These detectors feed ONLY into Shadow Structural Metrics (SEI/CLIP/NOR/PTS/SCG/FVC).
They MUST NOT influence prediction/forecast pipelines unless explicitly PROMOTED
via the governance system with calibration/stability/redundancy validation.

Shadow detectors are diagnostic/observational instruments that annotate
evidence without altering core prediction behavior.

Access Control: ABX-Runes ϟ₇ (SSO) ONLY
Version: 0.1.0
"""

from abraxas.detectors.shadow.types import (
    ShadowDetectorResult,
    ShadowEvidence,
    DetectorStatus,
)
from abraxas.detectors.shadow.compliance_remix import ComplianceRemixDetector
from abraxas.detectors.shadow.meta_awareness import MetaAwarenessDetector
from abraxas.detectors.shadow.negative_space import NegativeSpaceDetector
from abraxas.detectors.shadow.registry import compute_all_detectors, aggregate_evidence, get_shadow_tasks, DETECTOR_REGISTRY
from abraxas.detectors.shadow.lane_guard import LaneGuard, LaneViolationError

__version__ = "0.1.0"

__all__ = [
    "ShadowDetectorResult",
    "ShadowEvidence",
    "DetectorStatus",
    "ComplianceRemixDetector",
    "MetaAwarenessDetector",
    "NegativeSpaceDetector",
    "compute_all_detectors",
    "aggregate_evidence",
    "get_shadow_tasks",
    "DETECTOR_REGISTRY",
    "LaneGuard",
    "LaneViolationError",
]
