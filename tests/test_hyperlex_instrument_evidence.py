"""Authority-boundary tests for Hyperlex Instrument V1 Abraxas adapter."""

from __future__ import annotations

import os

import pytest

from abraxas.evidence.hyperlex_instrument import (
    HyperlexAuthorityError,
    adapt_observation,
    assert_not_authoritative,
    instrument_enabled,
    observe_text,
    promote_to_canonical_state,
)


def _sample_observation(*, advisory: bool = True) -> dict:
    return {
        "schema": "hyperlex.instrument.v1",
        "version": "HYPERLEX_INSTRUMENT_V1",
        "observation_id": "abc12345deadbeef",
        "input_hash": "0" * 64,
        "authority": {
            "kind": "advisory",
            "source": "hyperlex",
            "semantic_truth": False,
            "may_authorize": False,
            "may_mutate_governing_state": False,
            "role": "OBSERVATION",
        },
        "evidence": {
            "present": True,
            "score": 0.5,
            "abstain": False,
            "reason": None,
        },
        "representation": {
            "encoder_id": "sentence-transformers/msmarco-distilbert-base-v4",
            "encoder_hash": "a" * 64,
            "embed_mode": "STATIC_HASH_EMBEDDING",
            "embedding_ref": "b" * 64,
        },
        "candidates": [
            {
                "concept_id": "domain.crypto",
                "score": 0.8,
                "axis": "domain",
                "advisory": advisory,
                "status": "advisory",
            }
        ],
        "neighborhood": [{"concept_id": "domain.crypto", "similarity": 0.8}],
        "diagnostics": {
            "margin": 0.2,
            "ambiguity": 0.1,
            "distribution_distance": None,
            "representation_drift": None,
            "unavailable": ["distribution_distance", "representation_drift"],
        },
        "provenance": {
            "instrument_version": "HYPERLEX_INSTRUMENT_V1",
            "contract_version": "hyperlex.instrument.v1",
            "ontology_version": "HYPERLEX_V6_FAMILY_ONTOLOGY_V1_FINAL",
            "manifest_sha256": "c" * 64,
            "schema_sha256": "d" * 64,
            "settlement_ref": "specs/007-hyperlexical-model/classification-v6-program-settlement-20261002.md",
            "settlement_receipt": "4ae7cddffcf72330adad8eb3dfd453025aa02c8cb12c5e6f5499a4e6cad06ca2",
            "artifact_hashes": {},
        },
    }


def test_feature_flag_default_off(monkeypatch):
    monkeypatch.delenv("ABX_HYPERLEX_INSTRUMENT", raising=False)
    assert instrument_enabled() is False
    out = observe_text("crypto")
    assert out["ok"] is False
    assert out["error"] == "ABX_HYPERLEX_INSTRUMENT_disabled"


def test_adapt_preserves_advisory_authority():
    ev = adapt_observation(_sample_observation(), kind="SHADOW_SIGNAL")
    assert ev["source"] == "hyperlex"
    assert ev["authority"] == "advisory"
    assert ev["semantic_truth"] is False
    assert ev["kind"] == "SHADOW_SIGNAL"
    assert ev["valid_for_forecast"] is False
    assert ev["influence_policy"] == "NONE"
    assert ev["lane"] == "shadow"
    assert ev["instrument_version"] == "HYPERLEX_INSTRUMENT_V1"
    assert ev["diagnostics"]["distribution_distance"] is None
    assert_not_authoritative(ev)


def test_cannot_promote_to_canonical():
    ev = adapt_observation(_sample_observation())
    with pytest.raises(HyperlexAuthorityError):
        promote_to_canonical_state(ev)
    with pytest.raises(HyperlexAuthorityError):
        adapt_observation(_sample_observation(), kind="CANONICAL_STATE")
    with pytest.raises(HyperlexAuthorityError):
        adapt_observation(_sample_observation(), kind="GOLD")


def test_non_advisory_candidate_blocked():
    with pytest.raises(HyperlexAuthorityError):
        adapt_observation(_sample_observation(advisory=False))


def test_semantic_truth_observation_blocked():
    obs = _sample_observation()
    obs["authority"]["semantic_truth"] = True
    with pytest.raises(HyperlexAuthorityError):
        adapt_observation(obs)


def test_assert_not_authoritative_rejects_forecast_influence():
    ev = adapt_observation(_sample_observation())
    bad = dict(ev, valid_for_forecast=True)
    with pytest.raises(HyperlexAuthorityError):
        assert_not_authoritative(bad)
