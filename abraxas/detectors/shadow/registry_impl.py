"""
Shadow Detector Registry Implementation.

This is THE canonical provider of shadow tasks for the Abraxas runtime.
No discovery magic — this file explicitly exports what shadow detectors exist.

Called by: abraxas.detectors.shadow.registry.get_shadow_tasks()
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from abraxas.detectors.shadow.types import ShadowDetectorResult
from abraxas.detectors.shadow.compliance_remix import ComplianceRemixDetector
from abraxas.detectors.shadow.meta_awareness import MetaAwarenessDetector
from abraxas.detectors.shadow.negative_space import NegativeSpaceDetector


# Singleton detector instances (deterministic, no per-call construction)
_DETECTORS = {
    "compliance_remix": ComplianceRemixDetector(),
    "meta_awareness": MetaAwarenessDetector(),
    "negative_space": NegativeSpaceDetector(),
}


def _make_task(detector_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create a task callable for a specific detector.

    The returned callable:
    - Accepts context dict
    - Returns serialized ShadowDetectorResult
    - Handles errors gracefully (no exceptions leak to scheduler)
    """

    def task(ctx: Dict[str, Any]) -> Dict[str, Any]:
        detector = _DETECTORS.get(detector_name)
        if detector is None:
            return {
                "status": "error",
                "error": f"Detector {detector_name} not found in registry_impl",
            }
        try:
            result: ShadowDetectorResult = detector.detect(ctx)
            return result.model_dump()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "detector": detector_name,
            }

    return task


def build_shadow_task_map() -> Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]:
    """
    Build the canonical shadow task map.

    Returns:
        Dict mapping detector_name -> callable(ctx) -> dict

    This is the ONLY function the shadow registry should call.
    Stable ordering (sorted by name) ensures determinism.
    """
    return {name: _make_task(name) for name in sorted(_DETECTORS.keys())}


def get_detector_names() -> list[str]:
    """Return sorted list of registered detector names."""
    return sorted(_DETECTORS.keys())


__all__ = ["build_shadow_task_map", "get_detector_names"]
