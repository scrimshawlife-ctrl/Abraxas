"""
Shadow Detector Registry Implementation.

This is THE canonical provider of shadow tasks for the Abraxas runtime.
No discovery magic — this file explicitly exports what shadow detectors exist.

Called by: abraxas.detectors.shadow.registry.get_shadow_tasks()

Detector types:
- Class-based: Use ShadowDetectorBase, return ShadowDetectorResult
- Function-based: Use util helpers (ok/not_computable/err), return ShadowResult
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, Dict, Union

from abraxas.detectors.shadow.types import ShadowDetectorResult, ShadowResult
from abraxas.detectors.shadow.compliance_remix import ComplianceRemixDetector
from abraxas.detectors.shadow.meta_awareness import MetaAwarenessDetector
from abraxas.detectors.shadow.negative_space import NegativeSpaceDetector
from abraxas.detectors.shadow.token_density import run_token_density
from abraxas.detectors.shadow.anagram import run_shadow_anagrams


# Class-based detector instances (deterministic, no per-call construction)
_CLASS_DETECTORS = {
    "compliance_remix": ComplianceRemixDetector(),
    "meta_awareness": MetaAwarenessDetector(),
    "negative_space": NegativeSpaceDetector(),
}

# Function-based detectors using new util helpers (ok/not_computable/err)
_FUNCTION_DETECTORS: Dict[str, Callable[[Dict[str, Any]], ShadowResult]] = {
    "anagram": run_shadow_anagrams,
    "token_density": run_token_density,
}


def _make_class_task(detector_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create a task callable for a class-based detector.

    The returned callable:
    - Accepts context dict
    - Returns serialized ShadowDetectorResult
    - Handles errors gracefully (no exceptions leak to scheduler)
    """

    def task(ctx: Dict[str, Any]) -> Dict[str, Any]:
        detector = _CLASS_DETECTORS.get(detector_name)
        if detector is None:
            return {
                "status": "error",
                "error": f"Class detector {detector_name} not found in registry_impl",
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


def _make_function_task(detector_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create a task callable for a function-based detector.

    Function-based detectors use the new util helpers (ok/not_computable/err)
    and return ShadowResult dataclass.

    The returned callable:
    - Accepts context dict
    - Returns dict (asdict of ShadowResult)
    - Handles errors gracefully (no exceptions leak to scheduler)
    """

    def task(ctx: Dict[str, Any]) -> Dict[str, Any]:
        fn = _FUNCTION_DETECTORS.get(detector_name)
        if fn is None:
            return {
                "status": "error",
                "error": f"Function detector {detector_name} not found in registry_impl",
            }
        try:
            result: ShadowResult = fn(ctx)
            return asdict(result)
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

    Includes both class-based and function-based detectors.
    """
    tasks: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    # Add class-based detectors
    for name in _CLASS_DETECTORS:
        tasks[name] = _make_class_task(name)

    # Add function-based detectors
    for name in _FUNCTION_DETECTORS:
        tasks[name] = _make_function_task(name)

    # Return in sorted order for determinism
    return {k: tasks[k] for k in sorted(tasks.keys())}


def get_detector_names() -> list[str]:
    """Return sorted list of registered detector names."""
    all_names = set(_CLASS_DETECTORS.keys()) | set(_FUNCTION_DETECTORS.keys())
    return sorted(all_names)


__all__ = ["build_shadow_task_map", "get_detector_names"]
