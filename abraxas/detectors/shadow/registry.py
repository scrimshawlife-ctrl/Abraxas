"""
Shadow Detector Registry.

Centralized registry of all shadow detectors with deterministic execution.

Canonical exports:
- get_shadow_tasks(ctx) -> Dict[str, Callable] — for pipeline bindings
- compute_all_detectors(inputs) -> Dict[str, ShadowDetectorResult]
- aggregate_evidence(results) -> Dict[str, Any]
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from abraxas.detectors.shadow.types import ShadowDetectorResult
from abraxas.detectors.shadow.compliance_remix import ComplianceRemixDetector
from abraxas.detectors.shadow.meta_awareness import MetaAwarenessDetector
from abraxas.detectors.shadow.negative_space import NegativeSpaceDetector


# Global detector registry (for compute_all_detectors and legacy access)
DETECTOR_REGISTRY = {
    "compliance_remix": ComplianceRemixDetector(),
    "meta_awareness": MetaAwarenessDetector(),
    "negative_space": NegativeSpaceDetector(),
}


def get_shadow_tasks(_ctx: Dict[str, Any]) -> Dict[str, Callable[[Dict[str, Any]], Any]]:
    """
    Canonical shadow task provider for pipeline bindings.

    Returns dict[name -> callable(context)->Any].

    Deterministic discovery:
    - Imports from registry_impl (the single source of truth)
    - If registry_impl not found, returns {} (shadow lane is optional)
    - Never fails silently with placeholder data
    """
    try:
        from abraxas.detectors.shadow.registry_impl import build_shadow_task_map

        return build_shadow_task_map()
    except ImportError:
        # Shadow lane is optional — empty is valid and deterministic
        return {}


def compute_all_detectors(inputs: Dict[str, Any]) -> Dict[str, ShadowDetectorResult]:
    """
    Run all shadow detectors on inputs.

    Args:
        inputs: Dictionary of input data. Each detector will extract
                what it needs from this dict.

    Returns:
        Dict mapping detector_name -> ShadowDetectorResult

    Example:
        inputs = {
            "text": "The algorithm promotes engagement bait...",
            "reference_texts": ["Normal discourse corpus..."],
            "baseline_texts": ["Expected topic distribution..."],
        }
        results = compute_all_detectors(inputs)
    """
    results = {}

    # Run each detector in deterministic order (sorted by name)
    for detector_name in sorted(DETECTOR_REGISTRY.keys()):
        detector = DETECTOR_REGISTRY[detector_name]
        result = detector.detect(inputs)
        results[detector_name] = result

    return results


def aggregate_evidence(results: Dict[str, ShadowDetectorResult]) -> Dict[str, Any]:
    """
    Aggregate evidence from all detector results.

    This creates a summary bundle that can be attached to shadow metrics
    as annotations.

    Args:
        results: Dict of detector results from compute_all_detectors()

    Returns:
        Aggregated evidence bundle with:
        - computed_count: number of detectors that computed successfully
        - not_computable_count: number that couldn't compute
        - error_count: number that errored
        - evidence_by_detector: evidence from each detector
        - max_signal_strength: highest signal across all detectors
        - provenance_hashes: SHA-256 hashes from all results
    """
    computed = []
    not_computable = []
    errors = []
    evidence_by_detector = {}
    provenance_hashes = {}

    for detector_name, result in results.items():
        provenance_hashes[detector_name] = result.compute_provenance_hash()

        if result.status == "computed" and result.evidence:
            computed.append(detector_name)
            evidence_by_detector[detector_name] = result.evidence.model_dump()
        elif result.status == "not_computable":
            not_computable.append(detector_name)
        elif result.status == "error":
            errors.append(detector_name)

    # Find max signal strength
    max_signal = 0.0
    for detector_name in computed:
        signal = evidence_by_detector[detector_name]["signal_strength"]
        max_signal = max(max_signal, signal)

    return {
        "computed_count": len(computed),
        "not_computable_count": len(not_computable),
        "error_count": len(errors),
        "computed_detectors": computed,
        "evidence_by_detector": evidence_by_detector,
        "max_signal_strength": max_signal,
        "provenance_hashes": provenance_hashes,
    }


def serialize_detector_results(results: Dict[str, ShadowDetectorResult]) -> Dict[str, Any]:
    """Serialize detector results to dicts."""
    return {name: result.model_dump() for name, result in results.items()}


__all__ = [
    "DETECTOR_REGISTRY",
    "get_shadow_tasks",
    "compute_all_detectors",
    "aggregate_evidence",
    "serialize_detector_results",
]
