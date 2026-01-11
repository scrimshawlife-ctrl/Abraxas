"""Tests for economics.costing.compute capability contract."""

from __future__ import annotations

import pytest

from abraxas.economics.rune_adapter import compute_cost_deterministic


def test_compute_cost_basic():
    result = compute_cost_deterministic(
        n_sources=3,
        n_claims=4,
        n_clusters=2,
        n_terms=1,
        n_predictions=5,
        seed=123,
    )

    assert result["cost"]["sources"] == 3
    assert result["cost"]["claims"] == 4
    assert result["cost"]["clusters"] == 2
    assert result["cost"]["terms"] == 1
    assert result["cost"]["predictions"] == 5
    assert result["cost"]["base_credits"] == 5
    assert result["cost"]["total_credits"] >= 5
    assert result["provenance"]["operation_id"] == "economics.costing.compute"
    assert result["not_computable"] is None


def test_compute_cost_deterministic():
    result1 = compute_cost_deterministic(
        n_sources=1,
        n_claims=2,
        n_clusters=3,
        n_terms=4,
        n_predictions=5,
        seed=42,
    )
    result2 = compute_cost_deterministic(
        n_sources=1,
        n_claims=2,
        n_clusters=3,
        n_terms=4,
        n_predictions=5,
        seed=42,
    )

    assert result1["cost"] == result2["cost"]
    assert result1["provenance"]["inputs_sha256"] == result2["provenance"]["inputs_sha256"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
