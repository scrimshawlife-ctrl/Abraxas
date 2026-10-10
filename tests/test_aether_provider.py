# tests/test_aether_provider.py
import pytest
from abraxas.engines.manifest import get
from abraxas.evidence.providers.aether import create_aether_adapter, AetherNotImplemented
from abraxas.evidence.contract import EvidenceType

def test_aether_provider_raises_on_produce_evidence():
    provider = create_aether_adapter()
    with pytest.raises(AetherNotImplemented) as exc:
        provider.produce_evidence("req-1", "any claim", {})
    assert "aether cannot produce evidence" in str(exc.value)
    assert "not_implemented" in str(exc.value).lower()
    assert "encoders" in str(exc.value).lower() or "fusion" in str(exc.value).lower()

def test_aether_provider_raises_on_get_model_identity():
    provider = create_aether_adapter()
    with pytest.raises(AetherNotImplemented):
        provider.get_model_identity()

def test_aether_interface_conformance():
    provider = create_aether_adapter()
    assert provider.engine_name == "aether"
    assert EvidenceType.MULTIMODAL_INTEGRATION in provider.supported_evidence_types


def test_aether_behavioral_verification_deliberately_absent():
    """Per Aether/SPEC.md §6: behavioral tests (fusion correctness etc.) are absent
    because the engine does not exist. This test documents the UNKNOWN."""
    provider = create_aether_adapter()
    with pytest.raises(AetherNotImplemented):
        provider.produce_evidence("behavioral-verification", "fusion correctness", {"modalities": {}})

def test_aether_never_returns_envelope_always_raises():
    """Aether boundary must always raise, never return an EvidenceEnvelope.
    This enforces the refusing spec per sibling Aether/SPEC.md §5."""
    provider = create_aether_adapter()
    with pytest.raises(AetherNotImplemented) as exc:
        provider.produce_evidence("r1", "claim", {"modalities": {"text": "foo"}})
    msg = str(exc.value)
    assert "not_implemented" in msg.lower()
    assert "per-modality provenance" in msg or "fail closed" in msg
    # Explicitly ensure no envelope was returned (the raise is the contract)
    assert "EvidenceEnvelope" not in str(type(exc.value))
