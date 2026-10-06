"""Tests for the model-agnostic inference adapter.

The adapter is the shipped path where a bespoke custom model is not available, so
it must be deterministic offline, honest in its provenance, and reachable through
a documented seam for real endpoints.
"""

from __future__ import annotations

import pytest

from abraxas.evidence.adapters.model_agnostic import (
    OFFLINE_IDENTITY,
    InferenceUnavailable,
    create_model_agnostic_inference,
)

ENV_KEYS = (
    "ABX_INFERENCE_BASE_URL",
    "ABX_INFERENCE_MODEL",
    "ABX_INFERENCE_API_KEY",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_offline_result_is_deterministic():
    infer = create_model_agnostic_inference()
    first = infer("The torus field couples to consciousness.", {"a": 1})
    second = infer("The torus field couples to consciousness.", {"a": 1})
    assert first == second


def test_offline_result_is_honest_about_itself():
    """It must never present itself as model output."""
    result = create_model_agnostic_inference()("A claim about a claim.", {})
    assert result["model_identity"] == OFFLINE_IDENTITY
    assert result["provenance"]["inference"] == "offline-deterministic"
    assert result["provenance"]["configured"] is False


def test_offline_result_has_the_adapter_contract_shape():
    result = create_model_agnostic_inference()("Some claim.", {})
    for key in ("candidates", "model_identity", "relations", "reasoning_steps", "provenance"):
        assert key in result, f"missing {key}"
    assert isinstance(result["candidates"], list) and result["candidates"]
    assert isinstance(result["relations"], list)
    assert isinstance(result["reasoning_steps"], list)


def test_different_claims_give_different_candidates():
    infer = create_model_agnostic_inference()
    a = infer("Alpha claim about networks.", {})
    b = infer("Zeta claim about thermodynamics.", {})
    assert a["candidates"] != b["candidates"]


def test_empty_claim_is_rejected():
    with pytest.raises(ValueError):
        create_model_agnostic_inference()("", {})
    with pytest.raises(ValueError):
        create_model_agnostic_inference()("   ", {})


def test_context_is_optional_and_non_dict_is_tolerated():
    infer = create_model_agnostic_inference()
    assert infer("A claim.", None)["provenance"]["context_keys"] == []
    assert infer("A claim.", "not-a-dict")["provenance"]["context_keys"] == []


def test_configured_endpoint_uses_the_transport_seam(monkeypatch):
    """With an endpoint configured the HTTP path runs; the seam replaces it."""
    seen = {}

    def transport(claim, context, *, base_url, model, api_key, timeout):
        seen.update({"claim": claim, "base_url": base_url, "model": model, "key": api_key})
        return {
            "candidates": ["a reading"],
            "model_identity": f"model-agnostic/{model}",
            "relations": ["claim->reading"],
            "reasoning_steps": ["step"],
            "provenance": {"inference": "model-agnostic-http", "configured": True},
        }

    monkeypatch.setenv("ABX_INFERENCE_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("ABX_INFERENCE_MODEL", "some-model")
    monkeypatch.setenv("ABX_INFERENCE_API_KEY", "not-a-real-key")

    result = create_model_agnostic_inference(transport=transport)("A claim.", {})
    assert seen["base_url"] == "https://example.invalid/v1"
    assert seen["model"] == "some-model"
    assert result["provenance"]["configured"] is True
    assert result["model_identity"] == "model-agnostic/some-model"


def test_no_endpoint_configured_means_offline_even_with_a_transport():
    """A transport must not be reached when nothing is configured."""
    def transport(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("transport should not be called without configuration")

    result = create_model_agnostic_inference(transport=transport)("A claim.", {})
    assert result["provenance"]["configured"] is False


def test_inference_unavailable_is_exported_for_callers():
    assert issubclass(InferenceUnavailable, RuntimeError)


def test_athanor_defaults_to_the_model_agnostic_adapter():
    """create_athanor_adapter() must be usable without a bespoke model."""
    from abraxas.evidence.provider import EvidenceProvider, create_athanor_adapter

    adapter = create_athanor_adapter()
    assert isinstance(adapter, EvidenceProvider)
    assert adapter.engine_name == "athanor"
