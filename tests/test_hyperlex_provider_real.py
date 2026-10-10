# tests/test_hyperlex_provider_real.py
import os
import pytest
from abraxas.engines.manifest import get
from abraxas.evidence.providers.hyperlex import create_hyperlex_adapter
from abraxas.evidence.contract import EvidenceType

def test_hyperlex_provider_uses_instrument_when_enabled(monkeypatch):
    monkeypatch.setenv("ABX_HYPERLEX_INSTRUMENT", "1")
    # assume sibling provides observation or use fixture
    provider = create_hyperlex_adapter()
    env = provider.produce_evidence("req1", "test claim", {})
    assert env.engine == "hyperlex"
    assert env.evidence_type == EvidenceType.LEXICAL_SEMANTIC
    assert env.confidence <= 1.0
    # must raise or return not_computable on authority violation (per instrument)

def test_hyperlex_produce_evidence_uses_real_observe_when_enabled(monkeypatch):
    monkeypatch.setenv("ABX_HYPERLEX_INSTRUMENT", "1")
    # Mock the instrument's observe_text to simulate real sibling success
    def fake_observe(text, requested=None):
        return {
            "ok": True,
            "observation": {
                "observation_id": "req-42",
                "input_hash": text[:16],
                "evidence": {"present": True, "score": 0.82, "abstain": False},
                "candidates": [{"concept_id": "lex-42", "score": 0.82, "axis": "lexical", "advisory": True}],
                "authority": {"kind": "advisory"},
            },
            "enabled": True,
        }
    monkeypatch.setattr("abraxas.evidence.providers.hyperlex.observe_text", fake_observe)
    from abraxas.evidence.providers.hyperlex import create_hyperlex_adapter
    provider = create_hyperlex_adapter()
    env = provider.produce_evidence("req-42", "some lexical claim about markets", {})
    assert env.engine == "hyperlex"
    assert env.confidence > 0.8
    assert any("lex-42" in str(c.answer) for c in env.candidate_outputs)
    assert env.provenance.get("real_call") is True