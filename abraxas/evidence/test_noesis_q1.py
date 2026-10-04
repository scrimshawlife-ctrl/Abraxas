"""NOESIS-Q1 Qualification Test Suite

This test suite validates the NOESIS-Q1 qualification gates using the
deterministic fixtures defined in noesis_q1_fixtures.yaml.

Run with: python -m pytest abraxas/evidence/test_noesis_q1.py -v
"""

from __future__ import annotations

import os
import yaml
import pytest
import math
from pathlib import Path
from typing import List, Dict, Any

from abraxas.evidence.contract import (
    EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep, Decision
)
from abraxas.evidence.verifiers.latent import (
    cosine_similarity,
    l2_distance,
    kl_divergence,
    compute_rsa_matrix,
    compute_rsa_correlation,
    analyze_latent_structure,
    compute_manifold_integrity,
    compute_atomic_brier,
    calibrate_confidence_via_brier,
    LatentStructureVerifier,
    NoesisEvidenceProvider,
)

# Import assert_not_authoritative from evidence module
from abraxas.evidence.hyperlex_instrument import (
    HyperlexAuthorityError,
    adapt_observation,
    assert_not_authoritative,
    instrument_enabled,
    observe_text,
    promote_to_canonical_state,
)


FIXTURES_PATH = Path(__file__).parent / "noesis_q1_fixtures.yaml"


def load_fixtures() -> dict:
    """Load test fixtures from YAML."""
    with open(FIXTURES_PATH) as f:
        return yaml.safe_load(f)


class TestNOESIS_Q1_Specification:
    """Tests for NOESIS-Q1 specification compliance."""

    def test_spec_file_exists(self):
        """Verify the specification document exists."""
        spec_path = Path(__file__).parent / "noesis_latent_v1.spec.md"
        assert spec_path.exists(), "NOESIS-Q1 specification document missing"

    def test_spec_contains_required_sections(self):
        """Verify specification has all required gates documented."""
        spec_path = Path(__file__).parent / "noesis_latent_v1.spec.md"
        content = spec_path.read_text()
        
        required_sections = [
            "Qualification Gates",
            "Wire-Shape Contract",
            "Latent Structure Schema",
            "Invariants",
            "Test Fixtures",
            "Qualification Receipt Structure",
            "Pairwise Conformance",
        ]
        
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"


class TestNOESIS_Q1_LatentAnalysis:
    """Tests for core latent structure analysis math."""

    def test_cosine_similarity_flat_vectors(self):
        """cosine_similarity should work with flat vectors."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]
        assert math.isclose(cosine_similarity(a, b), 1.0, rel_tol=1e-6)
        
        b = [3.0, 2.0, 1.0]
        sim = cosine_similarity(a, b)
        assert 0.0 < sim < 1.0

    def test_cosine_similarity_nested_vectors(self):
        """cosine_similarity should work with nested vectors."""
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[1.0, 2.0], [3.0, 4.0]]
        assert math.isclose(cosine_similarity(a, b), 1.0, rel_tol=1e-6)

    def test_cosine_similarity_zero_vectors(self):
        """cosine_similarity should handle zero vectors."""
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        assert cosine_similarity(a, b) == 0.0

    def test_cosine_similarity_dimension_mismatch(self):
        """cosine_similarity should return 0 for dimension mismatch."""
        a = [1.0, 2.0]
        b = [1.0, 2.0, 3.0]
        assert cosine_similarity(a, b) == 0.0

    def test_l2_distance(self):
        """l2_distance should compute correct distances."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]
        assert math.isclose(l2_distance(a, b), 0.0, rel_tol=1e-6)
        
        b = [4.0, 6.0, 8.0]
        # (4-1)^2 + (6-2)^2 + (8-3)^2 = 9 + 16 + 25 = 50
        assert math.isclose(l2_distance(a, b), math.sqrt(50), rel_tol=1e-6)

    def test_l2_distance_nested(self):
        """l2_distance should work with nested vectors."""
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[1.0, 2.0], [3.0, 4.0]]
        assert math.isclose(l2_distance(a, b), 0.0, rel_tol=1e-6)

    def test_kl_divergence(self):
        """kl_divergence should compute correctly."""
        p = [0.5, 0.5]
        q = [0.5, 0.5]
        assert math.isclose(kl_divergence(p, q), 0.0, rel_tol=1e-6)
        
        p = [1.0, 0.0]
        q = [0.5, 0.5]
        kl = kl_divergence(p, q)
        assert kl > 0.0

    def test_rsa_matrix_computation(self):
        """compute_rsa_matrix should produce symmetric matrix."""
        captures = [
            {"condition": "baseline", "activations": [1.0, 2.0, 3.0]},
            {"condition": "baseline", "activations": [1.1, 2.1, 3.1]},
            {"condition": "intervention", "activations": [2.0, 3.0, 4.0]},
        ]
        
        rsa = compute_rsa_matrix(captures)
        assert len(rsa) == 3
        assert len(rsa[0]) == 3
        assert math.isclose(rsa[0][0], 1.0, rel_tol=1e-6)
        assert math.isclose(rsa[0][1], rsa[1][0], rel_tol=1e-6)
        assert math.isclose(rsa[1][2], rsa[2][1], rel_tol=1e-6)

    def test_rsa_correlation(self):
        """compute_rsa_correlation should work for identical matrices."""
        rsa1 = [[1.0, 0.9, 0.8], [0.9, 1.0, 0.7], [0.8, 0.7, 1.0]]
        rsa2 = [[1.0, 0.9, 0.8], [0.9, 1.0, 0.7], [0.8, 0.7, 1.0]]
        corr = compute_rsa_correlation(rsa1, rsa2)
        assert math.isclose(corr, 1.0, rel_tol=1e-6)

    def test_rsa_correlation_different(self):
        """compute_rsa_correlation should be < 1 for different matrices."""
        rsa1 = [[1.0, 0.9, 0.8], [0.9, 1.0, 0.7], [0.8, 0.7, 1.0]]
        rsa2 = [[1.0, 0.5, 0.3], [0.5, 1.0, 0.2], [0.3, 0.2, 1.0]]
        corr = compute_rsa_correlation(rsa1, rsa2)
        assert 0.0 <= corr < 1.0

    def test_analyze_latent_structure_baseline_only(self):
        """analyze_latent_structure should handle baseline only."""
        captures = [
            {"condition": "baseline", "activations": [1.0, 2.0, 3.0]},
            {"condition": "baseline", "activations": [1.1, 2.1, 3.1]},
        ]
        
        result = analyze_latent_structure(captures)
        assert "conditions" in result
        assert result["conditions"] == {}
        assert result["baseline_condition"] == "baseline"
        assert result["conditions_tested"] == []

    def test_analyze_latent_structure_multiple_conditions(self):
        """analyze_latent_structure should analyze multiple conditions."""
        captures = [
            {"condition": "baseline", "activations": [1.0, 2.0, 3.0]},
            {"condition": "baseline", "activations": [1.05, 2.05, 3.05]},
            {"condition": "intervention", "activations": [1.3, 2.3, 3.3]},
            {"condition": "counterfactual", "activations": [0.7, 1.7, 2.7]},
        ]
        
        result = analyze_latent_structure(captures)
        assert "intervention" in result["conditions"]
        assert "counterfactual" in result["conditions"]
        assert "intervention" in result["conditions_tested"]
        assert "counterfactual" in result["conditions_tested"]
        assert "mean_stability" in result["conditions"]["intervention"]
        assert "mean_intervention_sensitivity" in result["conditions"]["intervention"]

    def test_analyze_latent_structure_missing_baseline(self):
        """analyze_latent_structure should error on missing baseline."""
        captures = [
            {"condition": "intervention", "activations": [1.0, 2.0, 3.0]},
        ]
        
        result = analyze_latent_structure(captures)
        assert "error" in result
        assert "Baseline" in result["error"]

    def test_compute_manifold_integrity(self):
        """compute_manifold_integrity should work."""
        captures = [
            {"condition": "baseline", "activations": [1.0, 2.0, 3.0]},
            {"condition": "baseline", "activations": [1.1, 2.1, 3.1]},
            {"condition": "intervention", "activations": [1.3, 2.3, 3.3]},
        ]
        
        integrity = compute_manifold_integrity(captures)
        assert 0.0 <= integrity <= 1.0

    def test_compute_manifold_integrity_single_capture(self):
        """compute_manifold_integrity should return 1.0 for single capture."""
        captures = [
            {"condition": "baseline", "activations": [1.0, 2.0, 3.0]},
        ]
        
        integrity = compute_manifold_integrity(captures)
        assert integrity == 1.0

    def test_compute_atomic_brier(self):
        """compute_atomic_brier should compute correctly."""
        # Perfect prediction
        brier = compute_atomic_brier(1.0, 1)
        assert brier == 0.0
        
        brier = compute_atomic_brier(0.0, 0)
        assert brier == 0.0
        
        # Wrong prediction
        brier = compute_atomic_brier(1.0, 0)
        assert brier == 1.0
        
        # Partial
        brier = compute_atomic_brier(0.7, 1)
        assert math.isclose(brier, 0.09, rel_tol=1e-6)

    def test_compute_atomic_brier_validation(self):
        """compute_atomic_brier should validate inputs."""
        with pytest.raises(ValueError):
            compute_atomic_brier(1.5, 1)
        with pytest.raises(ValueError):
            compute_atomic_brier(0.5, 2)

    def test_calibrate_confidence_via_brier(self):
        """calibrate_confidence_via_brier should adjust confidence."""
        # No history -> return raw
        calibrated = calibrate_confidence_via_brier(0.8, [])
        assert calibrated == 0.8
        
        # Good history (low brier) -> confidence adjusted by calibration factor
        history = [{"brier": 0.05}, {"brier": 0.08}]
        calibrated = calibrate_confidence_via_brier(0.8, history)
        # calibration_factor = 1.0 - mean_brier = 1.0 - 0.065 = 0.935
        # calibrated = 0.8 * 0.935 = 0.748
        assert math.isclose(calibrated, 0.748, rel_tol=1e-3)
        
        # Bad history (high brier) -> confidence reduced more
        history = [{"brier": 0.3}, {"brier": 0.4}]
        calibrated = calibrate_confidence_via_brier(0.8, history)
        # calibration_factor = 1.0 - 0.35 = 0.65
        # calibrated = 0.8 * 0.65 = 0.52
        assert math.isclose(calibrated, 0.52, rel_tol=1e-3)
        assert calibrated < 0.8
        assert calibrated >= 0.0

    def test_softmax(self):
        """softmax should normalize to probabilities."""
        from abraxas.evidence.verifiers.latent import softmax
        vec = [1.0, 2.0, 3.0]
        probs = softmax(vec)
        assert math.isclose(sum(probs), 1.0, rel_tol=1e-6)
        assert all(p > 0 for p in probs)


class TestNOESIS_Q1_Fixtures:
    """Tests using the deterministic Q1 fixtures."""

    @pytest.fixture(scope="class")
    def fixtures(self):
        return load_fixtures()

    def test_fixture_valid_baseline_intervention(self, fixtures):
        """Test valid baseline + intervention fixture."""
        fixture = fixtures["fixture_valid_baseline_intervention"]
        input_data = fixture["input"]
        
        result = analyze_latent_structure(input_data["latent_captures"], input_data["baseline_condition"])
        
        assert "error" not in result
        assert "intervention" in result["conditions_tested"]
        coherence = result["overall_structural_coherence"]
        assert coherence > 0.8, f"Expected coherence > 0.8, got {coherence}"
        
        intervention = result["conditions"]["intervention"]
        sensitivity = intervention["mean_intervention_sensitivity"]
        assert sensitivity < 0.3, f"Expected sensitivity < 0.3, got {sensitivity}"

    def test_fixture_valid_multiple_conditions(self, fixtures):
        """Test valid multiple conditions fixture."""
        fixture = fixtures["fixture_valid_multiple_conditions"]
        input_data = fixture["input"]
        
        result = analyze_latent_structure(input_data["latent_captures"], input_data["baseline_condition"])
        
        assert "error" not in result
        expected_conditions = {"intervention", "counterfactual", "ablation", "noise", "patch"}
        actual_conditions = set(result["conditions_tested"])
        assert expected_conditions.issubset(actual_conditions)
        
        coherence = result["overall_structural_coherence"]
        assert coherence > 0.5, f"Expected coherence > 0.5, got {coherence}"

    def test_fixture_valid_high_coherence(self, fixtures):
        """Test valid high coherence fixture."""
        fixture = fixtures["fixture_valid_high_coherence"]
        input_data = fixture["input"]
        
        result = analyze_latent_structure(input_data["latent_captures"], input_data["baseline_condition"])
        
        assert "error" not in result
        coherence = result["overall_structural_coherence"]
        assert coherence > 0.85, f"Expected coherence > 0.85, got {coherence}"
        
        intervention = result["conditions"]["intervention"]
        sensitivity = intervention["mean_intervention_sensitivity"]
        assert sensitivity < 0.2, f"Expected sensitivity < 0.2, got {sensitivity}"

    def test_fixture_valid_low_coherence(self, fixtures):
        """Test valid low coherence fixture (should escalate)."""
        fixture = fixtures["fixture_valid_low_coherence"]
        input_data = fixture["input"]
        
        result = analyze_latent_structure(input_data["latent_captures"], input_data["baseline_condition"])
        
        assert "error" not in result
        coherence = result["overall_structural_coherence"]
        assert coherence < 0.4, f"Expected coherence < 0.4, got {coherence}"
        
        # Check if any condition has high intervention sensitivity (escalate trigger)
        max_sensitivity = max(
            cond.get("mean_intervention_sensitivity", 0) 
            for cond in result.get("conditions", {}).values()
        )
        assert max_sensitivity > 0.6, f"Expected max sensitivity > 0.6, got {max_sensitivity}"

    def test_fixture_empty_captures(self, fixtures):
            """Test empty captures fixture (error handling)."""
            fixture = fixtures["fixture_empty_captures"]
            input_data = fixture["input"]
        
            result = analyze_latent_structure(input_data["latent_captures"], input_data["baseline_condition"])
        
            assert "error" in result
            assert "Baseline" in result["error"]

    def test_fixture_mismatched_dimensions(self, fixtures):
        """Test mismatched dimensions fixture."""
        fixture = fixtures["fixture_mismatched_dimensions"]
        input_data = fixture["input"]
        
        result = analyze_latent_structure(input_data["latent_captures"], input_data["baseline_condition"])
        
        # Should handle gracefully (skips mismatched)
        assert "error" not in result or "skip_mismatched" in result.get("expected_analysis", {})

    def test_fixture_missing_baseline(self, fixtures):
        """Test missing baseline fixture."""
        fixture = fixtures["fixture_missing_baseline"]
        input_data = fixture["input"]
        
        result = analyze_latent_structure(input_data["latent_captures"], input_data["baseline_condition"])
        
        assert "error" in result
        assert "Baseline" in result["error"]

    def test_fixture_single_capture(self, fixtures):
        """Test single capture fixture."""
        fixture = fixtures["fixture_single_capture"]
        input_data = fixture["input"]
        
        integrity = compute_manifold_integrity(input_data["latent_captures"])
        assert integrity == 1.0
        
        result = analyze_latent_structure(input_data["latent_captures"], input_data["baseline_condition"])
        assert result["conditions_tested"] == []


class TestNOESIS_Q1_AuthorityBoundary:
    """Tests for authority boundary enforcement."""

    @pytest.fixture(scope="class")
    def fixtures(self):
        return load_fixtures()

    def _valid_envelope(self):
        """Create a valid NOESIS envelope dict for assert_not_authoritative."""
        return {
            "source": "noesis.latent.v1",
            "authority": "advisory",
            "semantic_truth": False,
            "influence_policy": "NONE",
            "valid_for_forecast": False,
            "may_authorize": False,
            "may_mutate_governing_state": False,
            "kind": "SHADOW_SIGNAL",
        }

    def test_semantic_truth_true_rejected(self, fixtures):
        """semantic_truth=true must be rejected by assert_not_authoritative."""
        envelope = self._valid_envelope()
        envelope["semantic_truth"] = True
        
        with pytest.raises(Exception) as exc:
            assert_not_authoritative(envelope)
        assert "semantic_truth" in str(exc.value).lower()

    def test_non_advisory_authority_rejected(self, fixtures):
        """authority != advisory must be rejected."""
        envelope = self._valid_envelope()
        envelope["authority"] = "authoritative"
        
        with pytest.raises(Exception) as exc:
            assert_not_authoritative(envelope)
        assert "authority" in str(exc.value).lower()

    def test_valid_for_forecast_true_rejected(self, fixtures):
        """valid_for_forecast=true must be rejected."""
        envelope = self._valid_envelope()
        envelope["valid_for_forecast"] = True
        
        with pytest.raises(Exception) as exc:
            assert_not_authoritative(envelope)
        assert "valid_for_forecast" in str(exc.value).lower()

    def test_influence_policy_not_none_rejected(self, fixtures):
        """influence_policy != NONE must be rejected."""
        envelope = self._valid_envelope()
        envelope["influence_policy"] = "INFLUENCE"
        
        with pytest.raises(Exception) as exc:
            assert_not_authoritative(envelope)
        assert "influence_policy" in str(exc.value).lower()

    def test_may_mutate_governing_state_true_rejected(self, fixtures):
        """may_mutate_governing_state=true must be rejected."""
        envelope = self._valid_envelope()
        envelope["may_mutate_governing_state"] = True
        
        with pytest.raises(Exception) as exc:
            assert_not_authoritative(envelope)
        assert "may_mutate_governing_state" in str(exc.value).lower()

    def test_authoritative_kind_rejected(self, fixtures):
        """authoritative evidence type must be rejected."""
        envelope = self._valid_envelope()
        envelope["kind"] = "CANONICAL_STATE"
        
        with pytest.raises(Exception) as exc:
            assert_not_authoritative(envelope)
        assert "kind" in str(exc.value).lower() or "canonical" in str(exc.value).lower()


class TestNOESIS_Q1_Verifier:
    """Tests for LatentStructureVerifier."""

    def test_latent_verifier_exists(self):
        """LatentStructureVerifier should be importable and instantiable."""
        verifier = LatentStructureVerifier()
        assert verifier.evidence_type == "LATENT_STRUCTURAL"
        assert verifier.name == "LatentStructureVerifier"

    def test_latent_verifier_verify_passed(self):
        """LatentStructureVerifier should pass high-quality evidence."""
        verifier = LatentStructureVerifier()
        
        envelope = EvidenceEnvelope(
            engine="noesis",
            engine_version="noesis.latent.v1",
            model_identity="noesis.latent.v1",
            request_id="test-001",
            claim="Test",
            candidate_outputs=[
                CandidateOutput(
                    answer="Structurally coherent",
                    confidence=0.85,
                    reasoning_trace="High coherence",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LATENT_STRUCTURAL,
            confidence=0.85,
            uncertainty=0.15,
            provenance={
                "source": "noesis.latent.v1",
                "structural_coherence": 0.85,
                "intervention_sensitivity": 0.15,
                "rsa_correlation": 0.9,
                "geometric_integrity": 0.85,
                "manifold_integrity": 0.8,
            }
        )
        
        result = verifier.verify(envelope)
        
        assert result["passed"] is True
        assert result["escalate"] is False
        assert "details" in result
        assert result["details"]["structural_coherence"] == 0.85
        assert result["details"]["intervention_sensitivity"] == 0.15
        assert "calibrated_confidence" in result["details"]

    def test_latent_verifier_verify_escalate(self):
        """LatentStructureVerifier should escalate low-quality evidence."""
        verifier = LatentStructureVerifier()
        
        envelope = EvidenceEnvelope(
            engine="noesis",
            engine_version="noesis.latent.v1",
            model_identity="noesis.latent.v1",
            request_id="test-002",
            claim="Test",
            candidate_outputs=[
                CandidateOutput(
                    answer="Structurally unstable",
                    confidence=0.3,
                    reasoning_trace="Low coherence",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LATENT_STRUCTURAL,
            confidence=0.3,
            uncertainty=0.7,
            provenance={
                "source": "noesis.latent.v1",
                "structural_coherence": 0.3,
                "intervention_sensitivity": 0.7,
                "rsa_correlation": 0.2,
                "geometric_integrity": 0.3,
                "manifold_integrity": 0.2,
            }
        )
        
        result = verifier.verify(envelope)
        
        assert result["passed"] is False
        assert result["escalate"] is True

    def test_latent_verifier_verify_borderline_jev(self):
        """LatentStructureVerifier should suggest JEV for borderline cases."""
        verifier = LatentStructureVerifier(use_jev_fallback=True)
        
        envelope = EvidenceEnvelope(
            engine="noesis",
            engine_version="noesis.latent.v1",
            model_identity="noesis.latent.v1",
            request_id="test-003",
            claim="Test",
            candidate_outputs=[
                CandidateOutput(
                    answer="Borderline",
                    confidence=0.65,
                    reasoning_trace="Borderline coherence",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LATENT_STRUCTURAL,
            confidence=0.65,
            uncertainty=0.35,
            provenance={
                "source": "noesis.latent.v1",
                "structural_coherence": 0.65,
                "intervention_sensitivity": 0.35,
                "rsa_correlation": 0.65,
                "geometric_integrity": 0.65,
                "manifold_integrity": 0.55,
            }
        )
        
        result = verifier.verify(envelope)
        
        # Should be borderline (not passed, not escalated)
        assert result["passed"] is False
        assert result["escalate"] is False
        # JEV recommendation should be present
        assert "jev_recommendation" in result
        if result["jev_recommendation"]:
            assert result["jev_recommendation"]["trigger"] == "latent_structure_borderline"

    def test_latent_verifier_no_jev_when_disabled(self):
        """LatentStructureVerifier should not suggest JEV when disabled."""
        verifier = LatentStructureVerifier(use_jev_fallback=False)
        
        envelope = EvidenceEnvelope(
            engine="noesis",
            engine_version="noesis.latent.v1",
            model_identity="noesis.latent.v1",
            request_id="test-004",
            claim="Test",
            candidate_outputs=[
                CandidateOutput(
                    answer="Borderline",
                    confidence=0.65,
                    reasoning_trace="Borderline",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LATENT_STRUCTURAL,
            confidence=0.65,
            uncertainty=0.35,
            provenance={
                "source": "noesis.latent.v1",
                "structural_coherence": 0.65,
                "intervention_sensitivity": 0.35,
                "rsa_correlation": 0.65,
                "geometric_integrity": 0.65,
                "manifold_integrity": 0.55,
            }
        )
        
        result = verifier.verify(envelope)
        
        assert result.get("jev_recommendation") is None

    def test_latent_verifier_calibrated_confidence(self):
        """LatentStructureVerifier should include calibrated confidence."""
        verifier = LatentStructureVerifier()
        
        # Add some history
        verifier.record_brier_outcome(0.8, 1)
        verifier.record_brier_outcome(0.7, 1)
        verifier.record_brier_outcome(0.6, 0)
        
        envelope = EvidenceEnvelope(
            engine="noesis",
            engine_version="noesis.latent.v1",
            model_identity="noesis.latent.v1",
            request_id="test-005",
            claim="Test",
            candidate_outputs=[
                CandidateOutput(
                    answer="Test",
                    confidence=0.8,
                    reasoning_trace="Test",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LATENT_STRUCTURAL,
            confidence=0.8,
            uncertainty=0.2,
            provenance={
                "source": "noesis.latent.v1",
                "structural_coherence": 0.8,
                "intervention_sensitivity": 0.2,
                "rsa_correlation": 0.9,
                "geometric_integrity": 0.8,
                "manifold_integrity": 0.8,
            }
        )
        
        result = verifier.verify(envelope)
        
        assert "calibrated_confidence" in result["details"]
        calibrated = result["details"]["calibrated_confidence"]
        assert 0.0 <= calibrated <= 1.0

    def test_latent_verifier_non_noesis_engine_rejected(self):
        """LatentStructureVerifier should reject non-noesis engines."""
        verifier = LatentStructureVerifier()
        
        envelope = EvidenceEnvelope(
            engine="hyperlex",
            engine_version="v1",
            model_identity="hyperlex-instrument-v1",
            request_id="test-006",
            claim="Test",
            candidate_outputs=[],
            evidence_type=EvidenceType.LATENT_STRUCTURAL,
            confidence=0.8,
            uncertainty=0.2,
            provenance={}
        )
        
        result = verifier.verify(envelope)
        
        assert result["passed"] is False
        assert result["escalate"] is True
        assert "Engine is not noesis" in result["details"]["reason"]


class TestNOESIS_Q1_Provider:
    """Tests for NoesisEvidenceProvider."""

    def test_provider_engine_identity(self):
        """NoesisEvidenceProvider should have correct identity."""
        provider = NoesisEvidenceProvider()
        assert provider.engine_name == "noesis"
        assert provider.engine_version == "noesis.latent.v1"
        assert provider.get_model_identity() == "noesis.latent.v1"
        assert EvidenceType.LATENT_STRUCTURAL in provider.supported_evidence_types

    def test_provider_produces_evidence(self):
        """NoesisEvidenceProvider should produce valid evidence."""
        provider = NoesisEvidenceProvider()
        
        envelope_dict = provider.produce_evidence(
            request_id="test-provider-001",
            claim="Test latent structure",
            context={}
        )
        
        assert envelope_dict["engine"] == "noesis"
        assert envelope_dict["engine_version"] == "noesis.latent.v1"
        assert envelope_dict["model_identity"] == "noesis.latent.v1"
        assert envelope_dict["evidence_type"] == "LATENT_STRUCTURAL"
        assert "confidence" in envelope_dict
        assert "provenance" in envelope_dict
        assert envelope_dict["provenance"]["source"] == "noesis.latent.v1"
        assert envelope_dict["provenance"]["authority"] == "advisory"
        assert envelope_dict["provenance"]["semantic_truth"] is False

    def test_provider_provenance_completeness(self):
        """NoesisEvidenceProvider provenance should be complete."""
        provider = NoesisEvidenceProvider()
        
        envelope_dict = provider.produce_evidence(
            request_id="test-provider-002",
            claim="Test",
            context={}
        )
        
        prov = envelope_dict["provenance"]
        required_keys = [
            "source", "method", "structural_coherence", "intervention_sensitivity",
            "rsa_correlation", "geometric_integrity", "manifold_integrity",
            "conditions_tested", "authority", "semantic_truth",
            "influence_policy", "valid_for_forecast", "lane"
        ]
        
        for key in required_keys:
            assert key in prov, f"Missing provenance key: {key}"
        
        assert prov["authority"] == "advisory"
        assert prov["semantic_truth"] is False
        assert prov["influence_policy"] == "NONE"
        assert prov["valid_for_forecast"] is False
        assert prov["lane"] == "shadow"


class TestNOESIS_Q1_Integration:
    """Integration tests with ProductionArbiter."""

    def test_noesis_evidence_through_production_arbiter(self):
        """NOESIS evidence should arbitrate through ProductionArbiter."""
        from abraxas.governance.production import ProductionOrchestrator, EngineStatus
        from abraxas.evidence.provider import EvidenceProvider
        
        orchestrator = ProductionOrchestrator()
        
        # Register mock noesis provider
        class NoesisProvider(EvidenceProvider):
            engine_name = "noesis"
            engine_version = "noesis.latent.v1"
            supported_evidence_types = [EvidenceType.LATENT_STRUCTURAL]
            
            def get_model_identity(self):
                return "noesis.latent.v1"
            
            def produce_evidence(self, request_id, claim, context, budget=None):
                return EvidenceEnvelope(
                    engine=self.engine_name,
                    engine_version=self.engine_version,
                    model_identity=self.get_model_identity(),
                    request_id=request_id,
                    claim=claim,
                    candidate_outputs=[
                        CandidateOutput(
                            answer="Structurally coherent",
                            confidence=0.85,
                            reasoning_trace="Latent structure analysis",
                            relation_steps=[]
                        )
                    ],
                    evidence_type=EvidenceType.LATENT_STRUCTURAL,
                    confidence=0.85,
                    uncertainty=0.15,
                    provenance={
                        "source": "noesis.latent.v1",
                        "authority": "advisory",
                        "semantic_truth": False,
                        "influence_policy": "NONE",
                        "valid_for_forecast": False,
                        "lane": "shadow",
                        "structural_coherence": 0.85,
                        "intervention_sensitivity": 0.15,
                    }
                )
        
        orchestrator.engine_registry.register(NoesisProvider())
        orchestrator.engine_registry.update_health("noesis", EngineStatus.HEALTHY, latency_ms=10.0)
        
        envelope = EvidenceEnvelope(
            engine="noesis",
            engine_version="noesis.latent.v1",
            model_identity="noesis.latent.v1",
            request_id="test-q1-001",
            claim="Test noesis integration",
            candidate_outputs=[
                CandidateOutput(
                    answer="Structurally coherent",
                    confidence=0.85,
                    reasoning_trace="Latent structure analysis",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LATENT_STRUCTURAL,
            confidence=0.85,
            uncertainty=0.15,
            provenance={
                "source": "noesis.latent.v1",
                "authority": "advisory",
                "semantic_truth": False,
                "influence_policy": "NONE",
                "valid_for_forecast": False,
                "lane": "shadow",
            }
        )
        
        decision = orchestrator.arbiter.arbitrate(envelope)
        
        from abraxas.evidence.contract import Decision
        assert isinstance(decision, Decision)
        assert decision in [Decision.ACCEPT, Decision.VERIFY, Decision.RECOMPUTE, Decision.ABSTAIN, Decision.ESCALATE]
        
        audit = orchestrator.arbiter.get_audit_log()
        assert len(audit) >= 1
        assert audit[-1]["event"] == "ARBITRATION_COMPLETE"

    def test_noesis_evidence_through_six_gate_governor(self):
        """NOESIS evidence should pass through 6-gate governor."""
        from abraxas.governance.production import ProductionOrchestrator, EngineStatus
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.provider import EvidenceProvider
        
        orchestrator = ProductionOrchestrator()
        
        class NoesisProvider(EvidenceProvider):
            engine_name = "noesis"
            engine_version = "noesis.latent.v1"
            supported_evidence_types = [EvidenceType.LATENT_STRUCTURAL]
            
            def get_model_identity(self):
                return "noesis.latent.v1"
            
            def produce_evidence(self, request_id, claim, context, budget=None):
                return EvidenceEnvelope(
                    engine=self.engine_name,
                    engine_version=self.engine_version,
                    model_identity=self.get_model_identity(),
                    request_id=request_id,
                    claim=claim,
                    candidate_outputs=[
                        CandidateOutput(
                            answer="Structurally coherent",
                            confidence=0.9,
                            reasoning_trace="Latent structure analysis",
                            relation_steps=[]
                        )
                    ],
                    evidence_type=EvidenceType.LATENT_STRUCTURAL,
                    confidence=0.9,
                    uncertainty=0.1,
                    provenance={
                        "source": "noesis.latent.v1",
                        "authority": "advisory",
                        "semantic_truth": False,
                        "influence_policy": "NONE",
                        "valid_for_forecast": False,
                        "lane": "shadow",
                    }
                )
        
        orchestrator.engine_registry.register(NoesisProvider())
        orchestrator.engine_registry.update_health("noesis", EngineStatus.HEALTHY, latency_ms=10.0)
        
        envelope = EvidenceEnvelope(
            engine="noesis",
            engine_version="noesis.latent.v1",
            model_identity="noesis.latent.v1",
            request_id="test-q1-002",
            claim="Test noesis 6-gate",
            candidate_outputs=[
                CandidateOutput(
                    answer="Structurally coherent",
                    confidence=0.9,
                    reasoning_trace="Latent structure analysis",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LATENT_STRUCTURAL,
            confidence=0.9,
            uncertainty=0.1,
            provenance={
                "source": "noesis.latent.v1",
                "authority": "advisory",
                "semantic_truth": False,
                "influence_policy": "NONE",
                "valid_for_forecast": False,
                "lane": "shadow",
            }
        )
        
        decision = orchestrator.arbiter.arbitrate(envelope)
        
        record = DecisionRecord.from_arbitration(
            request_id="test-q1-002",
            envelopes=[envelope],
            decision=decision,
            confidence=envelope.confidence,
        )
        
        governance = orchestrator.governor.evaluate(record)
        
        assert "governed" in governance
        assert "aggregate_score" in governance
        assert "gate_results" in governance
        assert len(governance["gate_results"]) == 6
        
        gate_names = {g["gate"] for g in governance["gate_results"]}
        expected_gates = {
            "provenance", "falsifiability", "redundancy",
            "rent", "ablation", "stabilization"
        }
        assert gate_names == expected_gates


class TestNOESIS_Q1_FeatureFlag:
    """Tests for feature flag behavior (if applicable)."""

    def test_noesis_feature_flag_behavior(self):
        """Noesis integration should respect feature flag if present."""
        # Noesis currently doesn't have a feature flag like Hyperlex
        # but if added, it should default to disabled
        # This test documents expected behavior
        assert True  # Placeholder for future feature flag


class TestNOESIS_Q1_Schema:
    """Tests for schema/subsystem validation."""

    def test_noesis_verifier_module_exists(self):
        """Latent verifier module should exist."""
        import abraxas.evidence.verifiers.latent
        assert hasattr(abraxas.evidence.verifiers.latent, "LatentStructureVerifier")
        assert hasattr(abraxas.evidence.verifiers.latent, "NoesisEvidenceProvider")
        assert hasattr(abraxas.evidence.verifiers.latent, "analyze_latent_structure")

    def test_evidence_type_defined(self):
        """LATENT_STRUCTURAL should be in EvidenceType enum."""
        assert EvidenceType.LATENT_STRUCTURAL == "LATENT_STRUCTURAL"


# Entry point for manual execution
if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "--tb=short"])