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
    assert True  # placeholder asserting the declared state
