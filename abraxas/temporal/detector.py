"""Temporal Drift Detector with caching."""

from __future__ import annotations

from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_string
from abraxas.temporal.classifier import (
    classify_temporal_mode,
    classify_causality_status,
    classify_diagram_role,
    classify_sovereignty_risk,
    determine_operator_hits,
)
from abraxas.temporal.features import extract_temporal_features, compute_temporal_signature
from abraxas.temporal.models import TemporalDriftResult


class TemporalDriftDetector:
    """
    Detector for temporal drift patterns.

    Caches results by text SHA256 for efficiency.
    """

    def __init__(self):
        self._cache: dict[str, TemporalDriftResult] = {}

    def analyze(
        self, text: str, operator_hits: list[str] | None = None, use_cache: bool = True
    ) -> TemporalDriftResult:
        """
        Analyze text for temporal drift.

        Args:
            text: Text to analyze
            operator_hits: Optional list of operator IDs already detected
            use_cache: Whether to use cache (default True)

        Returns:
            TemporalDriftResult
        """
        if operator_hits is None:
            operator_hits = []

        # Compute cache key
        cache_key = hash_string(text)
        if operator_hits:
            cache_key += "_" + "_".join(sorted(operator_hits))

        # Check cache
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # Extract features
        features = extract_temporal_features(text)
        signature = compute_temporal_signature(features)

        # Classify
        temporal_mode = classify_temporal_mode(features, signature)
        causality_status = classify_causality_status(features)
        diagram_role = classify_diagram_role(features, signature)
        sovereignty_risk = classify_sovereignty_risk(
            features, signature, temporal_mode, causality_status
        )

        # Determine operator hits
        tdd_operators = determine_operator_hits(
            temporal_mode, causality_status, diagram_role, sovereignty_risk
        )

        # Merge with provided operator hits
        all_operators = sorted(list(set(operator_hits + tdd_operators)))

        # Build evidence
        evidence = {
            "features": features,
            "signature": signature,
            "text_hash": hash_string(text),
        }

        # Build provenance
        provenance = ProvenanceBundle(
            inputs=[
                ProvenanceRef(
                    scheme="text",
                    path="tdd_input",
                    sha256=hash_string(text),
                )
            ],
            transforms=[
                "extract_temporal_features",
                "compute_signature",
                "classify_temporal_mode",
                "classify_causality",
                "classify_diagram_role",
                "classify_sovereignty_risk",
            ],
            metrics={
                "retronic_score": signature.get("retronic_score", 0.0),
                "eschatological_score": signature.get("eschatological_score", 0.0),
                "sovereignty_risk_score": signature.get("sovereignty_risk_score", 0.0),
            },
            created_by="temporal_drift_detector",
        )

        # Create result
        result = TemporalDriftResult(
            temporal_mode=temporal_mode,
            causality_status=causality_status,
            diagram_role=diagram_role,
            sovereignty_risk=sovereignty_risk,
            operator_hits=all_operators,
            evidence=evidence,
            provenance=provenance,
        )

        # Cache result
        if use_cache:
            self._cache[cache_key] = result

        return result

    def clear_cache(self) -> None:
        """Clear analysis cache."""
        self._cache.clear()

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {"cache_size": len(self._cache)}


# Singleton instance
_detector_instance: TemporalDriftDetector | None = None


def get_detector() -> TemporalDriftDetector:
    """Get singleton detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = TemporalDriftDetector()
    return _detector_instance


def analyze_text(
    text: str, operator_hits: list[str] | None = None, use_cache: bool = True
) -> TemporalDriftResult:
    """
    Convenience function to analyze text for temporal drift.

    Args:
        text: Text to analyze
        operator_hits: Optional operator IDs already detected
        use_cache: Whether to use cache

    Returns:
        TemporalDriftResult
    """
    detector = get_detector()
    return detector.analyze(text, operator_hits, use_cache)
