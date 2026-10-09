"""Real resonance provider tests — composes abraxas.phase detectors.

TDD: these tests FAIL until the provider is implemented with
PhaseAlignmentDetector and CouplingDetector.
"""

from __future__ import annotations

import pytest
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType


class TestResonanceProviderReal:
    """Tests for the real ResonanceEvidenceProvider composing phase detectors."""

    @pytest.fixture
    def provider(self):
        from abraxas.evidence.providers.resonance import create_resonance_adapter
        return create_resonance_adapter()

    @staticmethod
    def _sample_domain_states():
        """Return realistic domain_states for phase detection."""
        return {
            "ai-safety": {
                "alignment": "front",
                "capability": "front",
                "governance": "proto",
            },
            "crypto": {
                "defi": "front",
                "nft": "saturated",
                "l2": "front",
            },
            "biotech": {
                "gene-editing": "front",
                "synthetic-bio": "proto",
                "longevity": "front",
            },
        }

    @staticmethod
    def _sample_drift_signals():
        """Return realistic drift signals for coupling detection."""
        return {
            "ai-safety": 0.75,
            "crypto": 0.62,
            "biotech": 0.45,
        }

    @staticmethod
    def _sample_resonance_signals():
        """Return realistic resonance signals for coupling detection."""
        return {
            "ai-safety": 0.82,
            "crypto": 0.68,
            "biotech": 0.71,
        }

    # --- identity ---

    def test_engine_identity(self, provider):
        """Provider reports resonance identity."""
        assert provider.engine_name == "resonance"
        assert provider.engine_version == "resonance.phase.v0"
        assert provider.get_model_identity() == "resonance.phase.v0"

    def test_supported_evidence_types(self, provider):
        """Provider supports RESONANCE_ANALYSIS."""
        assert EvidenceType.RESONANCE_ANALYSIS in provider.supported_evidence_types

    # --- produce_evidence with phase detection ---

    def test_produce_evidence_returns_canonical_envelope(self, provider):
        """produce_evidence returns a canonical EvidenceEnvelope."""
        envelope = provider.produce_evidence(
            request_id="test-env-001",
            claim="Phase alignment across domains",
            context={"domain_states": self._sample_domain_states()},
        )
        assert isinstance(envelope, EvidenceEnvelope), (
            f"Expected EvidenceEnvelope, got {type(envelope).__name__}"
        )

    def test_produce_evidence_resonance_type(self, provider):
        """Evidence type is RESONANCE_ANALYSIS."""
        envelope = provider.produce_evidence(
            request_id="test-type-001",
            claim="Resonance detection",
            context={"domain_states": self._sample_domain_states()},
        )
        assert envelope.evidence_type == EvidenceType.RESONANCE_ANALYSIS

    def test_produce_evidence_with_domain_states(self, provider):
        """When domain_states are provided, phase alignments are detected."""
        domain_states = self._sample_domain_states()
        envelope = provider.produce_evidence(
            request_id="test-phase-001",
            claim="Cross-domain phase analysis",
            context={"domain_states": domain_states},
        )
        # The envelope must contain provenance about phase detection
        assert isinstance(envelope.provenance, dict)
        assert "source" in envelope.provenance
        assert envelope.provenance["source"] == "resonance.phase.v0"
        assert "phase_alignments_detected" in envelope.provenance
        # With 3 domains all having "front" tokens, we expect at least one alignment
        assert envelope.provenance["phase_alignments_detected"] > 0

    def test_produce_evidence_with_coupling(self, provider):
        """When drift and resonance signals are provided, coupling is detected."""
        context = {
            "domain_states": self._sample_domain_states(),
            "drift_signals": self._sample_drift_signals(),
            "resonance_signals": self._sample_resonance_signals(),
        }
        envelope = provider.produce_evidence(
            request_id="test-coupling-001",
            claim="Drift-resonance coupling analysis",
            context=context,
        )
        # With high drift + resonance for ai-safety and crypto, coupling should be detected
        assert "couplings_detected" in envelope.provenance
        assert envelope.provenance["couplings_detected"] > 0

    def test_produce_evidence_without_coupling_signals(self, provider):
        """Without drift/resonance signals, only phase detection runs."""
        envelope = provider.produce_evidence(
            request_id="test-phase-only-001",
            claim="Phase-only analysis",
            context={"domain_states": self._sample_domain_states()},
        )
        assert "couplings_detected" in envelope.provenance
        assert envelope.provenance["couplings_detected"] == 0

    # --- provenance completeness ---

    def test_provenance_completeness(self, provider):
        """Provenance carries all required fields."""
        envelope = provider.produce_evidence(
            request_id="test-prov-001",
            claim="Full resonance analysis",
            context={
                "domain_states": self._sample_domain_states(),
                "drift_signals": self._sample_drift_signals(),
                "resonance_signals": self._sample_resonance_signals(),
            },
        )
        prov = envelope.provenance
        required_keys = [
            "source", "method",
            "phase_alignments_detected",
            "couplings_detected",
            "authority", "semantic_truth",
            "influence_policy", "valid_for_forecast", "lane",
        ]
        for key in required_keys:
            assert key in prov, f"Missing provenance key: {key}"

        assert prov["authority"] == "advisory"
        assert prov["semantic_truth"] is False
        assert prov["influence_policy"] == "NONE"
        assert prov["valid_for_forecast"] is False
        assert prov["lane"] == "shadow"

    # --- confidence and uncertainty ---

    def test_confidence_in_range(self, provider):
        """Confidence is a float in [0, 1]."""
        envelope = provider.produce_evidence(
            request_id="test-conf-001",
            claim="Confidence range check",
            context={"domain_states": self._sample_domain_states()},
        )
        assert 0.0 <= envelope.confidence <= 1.0
        assert isinstance(envelope.confidence, float)

    def test_candidate_outputs_present(self, provider):
        """At least one CandidateOutput is present."""
        envelope = provider.produce_evidence(
            request_id="test-cand-001",
            claim="Candidate output check",
            context={"domain_states": self._sample_domain_states()},
        )
        assert len(envelope.candidate_outputs) >= 1
        candidate = envelope.candidate_outputs[0]
        assert candidate.confidence > 0
        assert len(candidate.reasoning_trace) > 0

    # --- empty context degrades gracefully ---

    def test_produce_evidence_empty_context(self, provider):
        """Empty context does not crash; returns envelope with zero detections."""
        envelope = provider.produce_evidence(
            request_id="test-empty-001",
            claim="Empty context test",
            context={},
        )
        assert isinstance(envelope, EvidenceEnvelope)
        assert envelope.evidence_type == EvidenceType.RESONANCE_ANALYSIS
        assert envelope.provenance["phase_alignments_detected"] == 0
        assert envelope.provenance["couplings_detected"] == 0


class TestResonanceProviderFactory:
    """Factory function contract."""

    def test_create_resonance_adapter_returns_provider(self):
        from abraxas.evidence.providers.resonance import create_resonance_adapter
        from abraxas.evidence.provider import EvidenceProvider
        provider = create_resonance_adapter()
        assert isinstance(provider, EvidenceProvider)
        assert provider.engine_name == "resonance"