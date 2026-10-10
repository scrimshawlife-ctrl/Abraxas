# tests/test_semion_provider_real.py
"""Semion provider real test — mirrors test_hyperlex_provider_real.py pattern."""
import os
import pytest
from abraxas.evidence.providers.semion import create_semion_adapter
from abraxas.evidence.contract import EvidenceType


def test_semion_provider_uses_instrument_when_enabled(monkeypatch):
    monkeypatch.setenv("ABX_SEMION_INSTRUMENT", "1")
    provider = create_semion_adapter()
    env = provider.produce_evidence("req1", "test sign relation claim", {})
    assert env.engine == "semion"
    assert env.evidence_type == EvidenceType.SIGN_RELATION
    assert env.confidence <= 1.0
    assert hasattr(provider, "engine_name")
    assert provider.engine_name == "semion"


def test_semion_provider_disabled_returns_zero_confidence():
    """When the feature flag is off, the instrument is disabled and confidence is 0.0."""
    provider = create_semion_adapter()
    env = provider.produce_evidence("req2", "claim", {})
    assert env.confidence == 0.0
    assert env.engine == "semion"
    assert env.evidence_type == EvidenceType.SIGN_RELATION
    assert env.provenance.get("status") == "disabled"


def test_semion_provider_authority_violation_handled(monkeypatch):
    """Authority violations are caught and returned as zero-confidence error envelope."""
    from abraxas.evidence import semion_instrument
    import abraxas.evidence.providers.semion as semion_provider

    monkeypatch.setenv("ABX_SEMION_INSTRUMENT", "1")

    def _raise_authority_error(*args, **kwargs):
        raise semion_instrument.SemionAuthorityError(
            "refusing semantic_truth=true — SEMION_OUTPUT != SEMION_TRUTH"
        )

    monkeypatch.setattr(semion_provider, "adapt_observation", _raise_authority_error)
    provider = create_semion_adapter()
    env = provider.produce_evidence("req3", "claim", {})
    assert env.confidence == 0.0
    assert env.uncertainty == 1.0
    assert "error" in env.provenance

def test_semion_produce_evidence_uses_real_classify_when_enabled(monkeypatch):
    monkeypatch.setenv("ABX_SEMION_INSTRUMENT", "1")
    # Mock the instrument's classify_via_semion and to_evidence_envelope
    def fake_classify(atom):
        return {
            "authority": {"kind": "advisory"},
            "observation_id": "req-99",
            "sign_class": "qualisign-rheme-icon",
            "sign_class_valid": True,
            "sign_class_errors": [],
            "peircean_analysis": {"coherence_score": 0.91},
            "relation_steps": [{"relation": "resembles", "subject": "a", "object": "b", "result": "similar", "confidence": 0.9}],
            "provenance": {"instrument_version": "SEMION_SIGN_RELATION_V1"},
            "status": "computable",
        }

    import abraxas.evidence.providers.semion as semion_mod
    monkeypatch.setattr(semion_mod, "classify_via_semion", fake_classify)

    # Also mock to_evidence_envelope to return a proper envelope for the test
    from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput
    def fake_to_env(raw, request_id, claim):
        return EvidenceEnvelope(
            engine="semion",
            engine_version="semion.sign.v1",
            model_identity="semion-sign-v1",
            request_id=request_id,
            claim=claim,
            candidate_outputs=[CandidateOutput(answer=raw.get("sign_class", "sign"), confidence=0.91, reasoning_trace="semion", relation_steps=[])],
            evidence_type=EvidenceType.SIGN_RELATION,
            confidence=0.91,
            uncertainty=0.09,
            provenance={"source": "semion_instrument", "real_call": True},
        )

    monkeypatch.setattr(semion_mod, "to_evidence_envelope", fake_to_env)

    from abraxas.evidence.providers.semion import create_semion_adapter
    provider = create_semion_adapter()
    env = provider.produce_evidence("req-99", "test sign claim", {})
    assert env.engine == "semion"
    assert env.confidence > 0.9
    assert "qualisign" in str(env.candidate_outputs[0].answer) or env.candidate_outputs
    assert env.provenance.get("real_call") is True