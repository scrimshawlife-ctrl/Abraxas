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