# tests/test_hyperlex_provider_real.py
import os
import pytest
from abraxas.engines.manifest import get
from abraxas.evidence.providers.hyperlex import create_hyperlex_adapter
from abraxas.evidence.contract import EvidenceType

def test_hyperlex_provider_uses_instrument_when_enabled(monkeypatch):
    monkeypatch.setenv("ABX_HYPLEX_INSTRUMENT", "1")
    # assume sibling provides observation or use fixture
    provider = create_hyperlex_adapter()
    env = provider.produce_evidence("req1", "test claim", {})
    assert env.engine == "hyperlex"
    assert env.evidence_type == EvidenceType.LEXICAL_SEMANTIC
    assert env.confidence <= 1.0
    # must raise or return not_computable on authority violation (per instrument)