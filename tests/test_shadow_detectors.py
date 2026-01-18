"""
Tests for Shadow Detectors.

Validates:
1. Determinism - same inputs produce same outputs
2. Bounds - all outputs in valid ranges [0,1]
3. Missing input handling - graceful not_computable status
4. Provenance - SHA-256 hashes present and consistent
"""

import pytest
from abraxas.detectors.shadow import (
    ComplianceRemixDetector,
    MetaAwarenessDetector,
    NegativeSpaceDetector,
    compute_all_detectors,
    aggregate_evidence,
)
from abraxas.detectors.shadow.types import DetectorStatus


class TestComplianceRemixDetector:
    """Tests for ComplianceRemixDetector."""

    def test_determinism(self):
        """Test that same inputs produce same outputs."""
        detector = ComplianceRemixDetector()
        inputs = {
            "text": "This is a test message about politics",
            "reference_texts": [
                "Politics is important for governance",
                "Political discourse shapes policy",
            ],
        }

        result1 = detector.detect(inputs)
        result2 = detector.detect(inputs)

        assert result1.inputs_hash == result2.inputs_hash
        assert result1.status == result2.status
        if result1.evidence and result2.evidence:
            assert result1.evidence.signal_strength == result2.evidence.signal_strength
            assert result1.evidence.confidence == result2.evidence.confidence

    def test_bounds(self):
        """Test that outputs are in valid ranges."""
        detector = ComplianceRemixDetector()
        inputs = {
            "text": "The algorithm promotes engagement bait",
            "reference_texts": ["Normal political discourse"],
        }

        result = detector.detect(inputs)

        if result.evidence:
            assert 0.0 <= result.evidence.signal_strength <= 1.0
            assert 0.0 <= result.evidence.confidence <= 1.0
            metadata = result.evidence.metadata
            assert 0.0 <= metadata["compliance_score"] <= 1.0
            assert 0.0 <= metadata["remix_score"] <= 1.0

    def test_missing_input(self):
        """Test handling of missing inputs."""
        detector = ComplianceRemixDetector()
        inputs = {}  # Missing 'text'

        result = detector.detect(inputs)

        assert result.status == DetectorStatus.NOT_COMPUTABLE
        assert "text" in result.error_message

    def test_missing_reference(self):
        """Test handling of missing reference texts."""
        detector = ComplianceRemixDetector()
        inputs = {"text": "Some text"}  # Missing reference_texts

        result = detector.detect(inputs)

        assert result.status == DetectorStatus.NOT_COMPUTABLE
        assert "reference" in result.error_message.lower()

    def test_provenance(self):
        """Test that provenance hash is present and consistent."""
        detector = ComplianceRemixDetector()
        inputs = {
            "text": "Test",
            "reference_texts": ["Reference"],
        }

        result = detector.detect(inputs)

        assert result.inputs_hash
        assert len(result.inputs_hash) == 64  # SHA-256 hex length
        assert result.timestamp_utc.endswith("Z")

        # Provenance hash should be deterministic
        prov_hash1 = result.compute_provenance_hash()
        prov_hash2 = result.compute_provenance_hash()
        assert prov_hash1 == prov_hash2


class TestMetaAwarenessDetector:
    """Tests for MetaAwarenessDetector."""

    def test_determinism(self):
        """Test that same inputs produce same outputs."""
        detector = MetaAwarenessDetector()
        inputs = {
            "text": "The algorithm promotes clickbait for engagement",
        }

        result1 = detector.detect(inputs)
        result2 = detector.detect(inputs)

        assert result1.inputs_hash == result2.inputs_hash
        assert result1.status == result2.status
        if result1.evidence and result2.evidence:
            assert result1.evidence.signal_strength == result2.evidence.signal_strength

    def test_bounds(self):
        """Test that outputs are in valid ranges."""
        detector = MetaAwarenessDetector()
        inputs = {
            "text": "This is engagement bait. The algorithm loves this stuff.",
        }

        result = detector.detect(inputs)

        if result.evidence:
            assert 0.0 <= result.evidence.signal_strength <= 1.0
            assert 0.0 <= result.evidence.confidence <= 1.0

    def test_missing_input(self):
        """Test handling of missing inputs."""
        detector = MetaAwarenessDetector()
        inputs = {}  # Missing 'text'

        result = detector.detect(inputs)

        assert result.status == DetectorStatus.NOT_COMPUTABLE
        assert "text" in result.error_message

    def test_empty_text(self):
        """Test handling of empty text."""
        detector = MetaAwarenessDetector()
        inputs = {"text": ""}

        result = detector.detect(inputs)

        assert result.status == DetectorStatus.NOT_COMPUTABLE

    def test_meta_detection(self):
        """Test that meta-awareness patterns are detected."""
        detector = MetaAwarenessDetector()
        inputs = {
            "text": "The algorithm is manipulating our feed to promote engagement bait",
        }

        result = detector.detect(inputs)

        assert result.status == DetectorStatus.OK
        assert result.evidence is not None
        assert result.evidence.signal_strength > 0.0
        assert result.evidence.metadata["marker_count"] > 0


class TestNegativeSpaceDetector:
    """Tests for NegativeSpaceDetector."""

    def test_determinism(self):
        """Test that same inputs produce same outputs."""
        detector = NegativeSpaceDetector()
        inputs = {
            "text": "Politics and economy are important",
            "baseline_texts": [
                "Politics, economy, and climate are all critical issues",
            ],
        }

        result1 = detector.detect(inputs)
        result2 = detector.detect(inputs)

        assert result1.inputs_hash == result2.inputs_hash
        assert result1.status == result2.status
        if result1.evidence and result2.evidence:
            assert result1.evidence.signal_strength == result2.evidence.signal_strength

    def test_bounds(self):
        """Test that outputs are in valid ranges."""
        detector = NegativeSpaceDetector()
        inputs = {
            "text": "Only talking about politics",
            "baseline_texts": ["Politics and climate and economy"],
        }

        result = detector.detect(inputs)

        if result.evidence:
            assert 0.0 <= result.evidence.signal_strength <= 1.0
            assert 0.0 <= result.evidence.confidence <= 1.0
            assert 0.0 <= result.evidence.metadata["divergence_score"] <= 1.0

    def test_missing_input(self):
        """Test handling of missing inputs."""
        detector = NegativeSpaceDetector()
        inputs = {}  # Missing 'text'

        result = detector.detect(inputs)

        assert result.status == DetectorStatus.NOT_COMPUTABLE
        assert "text" in result.error_message

    def test_missing_baseline(self):
        """Test handling of missing baseline."""
        detector = NegativeSpaceDetector()
        inputs = {"text": "Some text"}  # Missing baseline_texts

        result = detector.detect(inputs)

        assert result.status == DetectorStatus.NOT_COMPUTABLE
        assert "baseline" in result.error_message.lower()

    def test_topic_dropout_detection(self):
        """Test that topic dropout is detected."""
        detector = NegativeSpaceDetector()
        inputs = {
            "text": "Politics is important. Politics matters. Political discourse.",
            "baseline_texts": [
                "Politics is important. Climate is critical. Economy matters.",
            ],
        }

        result = detector.detect(inputs)

        assert result.status == DetectorStatus.OK
        assert result.evidence is not None
        # Should detect that climate and economy are dropped
        assert len(result.evidence.metadata["dropped_topics"]) > 0


class TestDetectorRegistry:
    """Tests for detector registry."""

    def test_compute_all_detectors(self):
        """Test that all detectors run successfully."""
        inputs = {
            "text": "The algorithm promotes engagement bait",
            "reference_texts": ["Normal discourse"],
            "baseline_texts": ["Expected topics"],
        }

        results = compute_all_detectors(inputs)

        assert "compliance_remix" in results
        assert "meta_awareness" in results
        assert "negative_space" in results

    def test_aggregate_evidence(self):
        """Test evidence aggregation."""
        inputs = {
            "text": "The algorithm promotes engagement bait",
            "reference_texts": ["Normal discourse"],
            "baseline_texts": ["Expected topics"],
        }

        results = compute_all_detectors(inputs)
        aggregated = aggregate_evidence(results)

        assert "computed_count" in aggregated
        assert "evidence_by_detector" in aggregated
        assert "max_signal_strength" in aggregated
        assert "provenance_hashes" in aggregated

        # All detectors should have provenance
        assert len(aggregated["provenance_hashes"]) == 3

    def test_determinism_across_registry(self):
        """Test that registry execution is deterministic."""
        inputs = {
            "text": "Test message",
            "reference_texts": ["Reference"],
            "baseline_texts": ["Baseline"],
        }

        results1 = compute_all_detectors(inputs)
        results2 = compute_all_detectors(inputs)

        agg1 = aggregate_evidence(results1)
        agg2 = aggregate_evidence(results2)

        # Provenance hashes are present and valid (but include timestamps, so won't match)
        assert len(agg1["provenance_hashes"]) == 3
        assert len(agg2["provenance_hashes"]) == 3
        for hash_val in agg1["provenance_hashes"].values():
            assert len(hash_val) == 64  # SHA-256 hex

        # Inputs hashes SHOULD match (deterministic input hashing)
        for detector_name in results1:
            assert results1[detector_name].inputs_hash == results2[detector_name].inputs_hash

        # Signal strengths should match (deterministic computation)
        if agg1["computed_count"] > 0 and agg2["computed_count"] > 0:
            for detector_name in agg1["computed_detectors"]:
                if detector_name in agg2["computed_detectors"]:
                    sig1 = agg1["evidence_by_detector"][detector_name]["signal_strength"]
                    sig2 = agg2["evidence_by_detector"][detector_name]["signal_strength"]
                    assert sig1 == sig2
