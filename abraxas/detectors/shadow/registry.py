"""
Shadow Detector Registry.

Centralized registry of all shadow detectors with deterministic execution.
Provides `compute_all_detectors()` function to run all detectors and
aggregate evidence.
"""

from typing import Any, Dict, Optional

from abraxas.detectors.shadow.types import DetectorOutput, ShadowDetectorResult
from abraxas.detectors.shadow.compliance_remix import ComplianceRemixDetector
from abraxas.detectors.shadow import compliance_remix
from abraxas.detectors.shadow.meta_awareness import MetaAwarenessDetector
from abraxas.detectors.shadow import meta_awareness
from abraxas.detectors.shadow.negative_space import NegativeSpaceDetector
from abraxas.detectors.shadow import negative_space


# Global detector registry
DETECTOR_REGISTRY = {
    "compliance_remix": ComplianceRemixDetector(),
    "meta_awareness": MetaAwarenessDetector(),
    "negative_space": NegativeSpaceDetector(),
}


def compute_all_detectors(
    context: Dict[str, Any],
    history: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Run all shadow detectors on inputs.

    This function supports two call signatures:
      - `compute_all_detectors(context)` -> class-based detect() results (ShadowDetectorResult)
      - `compute_all_detectors(context, history)` -> test-facing compute_detector() results (DetectorOutput)

    Returns:
        Dict mapping detector_name -> result model

    Example:
        inputs = {
            "text": "The algorithm promotes engagement bait...",
            "reference_texts": ["Normal discourse corpus..."],
            "baseline_texts": ["Expected topic distribution..."],
        }
        results = compute_all_detectors(inputs)
    """
    if history is not None:
        # Test-facing deterministic API (context + optional history)
        return {
            "compliance_remix": compliance_remix.compute_detector(context),
            "meta_awareness": meta_awareness.compute_detector(context),
            "negative_space": negative_space.compute_detector(context, history),
        }

    results: Dict[str, ShadowDetectorResult] = {}
    for detector_name in sorted(DETECTOR_REGISTRY.keys()):
        detector = DETECTOR_REGISTRY[detector_name]
        results[detector_name] = detector.detect(context)
    return results


def serialize_detector_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic serialization for test comparisons.
    """
    out: Dict[str, Any] = {}
    for k in sorted(results.keys()):
        v = results[k]
        if hasattr(v, "model_dump"):
            out[k] = v.model_dump()
        else:
            out[k] = v
    return out


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
