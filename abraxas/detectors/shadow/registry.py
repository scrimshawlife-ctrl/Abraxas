"""
Shadow Detector Registry.

Centralized registry of all shadow detectors with deterministic execution.
Provides `compute_all_detectors()` function to run all detectors and
aggregate evidence.
"""

from typing import Any, Callable, Dict, List
from abraxas.detectors.shadow.types import ShadowDetectorResult
from abraxas.detectors.shadow.compliance_remix import ComplianceRemixDetector
from abraxas.detectors.shadow.meta_awareness import MetaAwarenessDetector
from abraxas.detectors.shadow.negative_space import NegativeSpaceDetector


# Global detector registry
DETECTOR_REGISTRY = {
    "compliance_remix": ComplianceRemixDetector(),
    "meta_awareness": MetaAwarenessDetector(),
    "negative_space": NegativeSpaceDetector(),
}


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
    return {name: result.model_dump() for name, result in results.items()}


def get_shadow_tasks(ctx: Dict[str, Any]) -> Dict[str, Callable[[Dict[str, Any]], Any]]:
    """
    Return shadow detector tasks as callables for the pipeline bindings resolver.

    Each returned callable wraps a detector's detect() method, returning
    a serialized ShadowDetectorResult.

    Args:
        ctx: Context dict (currently unused, reserved for future configuration).

    Returns:
        Dict mapping detector_name -> callable(ctx) -> dict

    Note:
        This function is called by abraxas.runtime.pipeline_bindings.resolve_pipeline_bindings()
        to discover shadow tasks for the ERS scheduler.
    """

    def make_task(detector_name: str) -> Callable[[Dict[str, Any]], Any]:
        """Create a task callable for a specific detector."""

        def task(ctx: Dict[str, Any]) -> Dict[str, Any]:
            detector = DETECTOR_REGISTRY.get(detector_name)
            if detector is None:
                return {
                    "status": "error",
                    "error": f"Detector {detector_name} not found in registry",
                }
            try:
                result = detector.detect(ctx)
                return result.model_dump()
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "detector": detector_name,
                }

        return task

    # Return stable-ordered dict of task callables
    return {name: make_task(name) for name in sorted(DETECTOR_REGISTRY.keys())}
