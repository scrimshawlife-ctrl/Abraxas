"""Tests for memetic claim extraction and clustering runes."""

from __future__ import annotations

import pytest

from abraxas.memetic.rune_adapter import (
    cluster_claims_deterministic,
    extract_claim_items_deterministic,
)


def _sample_sources() -> list[dict]:
    return [
        {
            "url": "https://alpha.example.com/report",
            "domain": "alpha.example.com",
            "type": "web",
            "title": (
                "Alpha signals are rising across the market. "
                "Beta momentum remains flat despite volatility."
            ),
        },
        {
            "url": "https://beta.example.com/brief",
            "domain": "beta.example.com",
            "type": "web",
            "snippet": (
                "Gamma adoption keeps accelerating in new regions. "
                "Delta sentiment shows early stabilization signs."
            ),
        },
    ]


def test_extract_claim_items_deterministic():
    sources = _sample_sources()
    result1 = extract_claim_items_deterministic(sources, run_id="RUN-001", seed=11)
    result2 = extract_claim_items_deterministic(sources, run_id="RUN-001", seed=11)

    assert result1["items"] == result2["items"]
    assert result1["provenance"]["operation_id"] == "memetic.claim_extract.items"
    assert result1["provenance"]["inputs_sha256"] == result2["provenance"]["inputs_sha256"]
    assert result1["not_computable"] is None


def test_cluster_claims_deterministic():
    # Clustering is token-Jaccard -- lexical, not semantic. The related pair must
    # therefore SHARE tokens to clear the canonical 0.42 threshold, which is
    # declared on four surfaces (abraxas/memetic/claim_cluster.py:116,
    # abraxas/memetic/rune_adapter.py:122, and the --sim-threshold default in
    # abx/claims_run.py:31 and abx/term_claims_run.py:69).
    #
    # Claims 0 and 1 are the same signal set differing in one token (align/drift):
    # 7 shared of 9 union = 0.78, comfortably over the threshold. The previous
    # fixture shared only 3 of 13 tokens (0.23), so it could never produce the
    # [[0, 1], [2]] clustering asserted below -- the test was born red.
    items = [
        {"claim": "Alpha beta gamma delta signals align across channels."},
        {"claim": "Alpha beta gamma delta signals drift across channels."},
        {"claim": "Zeta eta theta remain isolated in the report."},
    ]
    result1 = cluster_claims_deterministic(items, sim_threshold=0.42, seed=7)
    result2 = cluster_claims_deterministic(items, sim_threshold=0.42, seed=7)

    assert result1["clusters"] == [[0, 1], [2]]
    assert result1["clusters"] == result2["clusters"]
    assert result1["metrics"] == result2["metrics"]
    assert result1["provenance"]["operation_id"] == "RUNE.MEMETIC.CLAIM_CLUSTER.CLUSTER"
    assert result1["provenance"]["inputs_sha256"] == result2["provenance"]["inputs_sha256"]
    assert result1["not_computable"] is None

    # The threshold must genuinely govern the merge: at 0.90 nothing is similar
    # enough and the same input yields three singletons. Without this the
    # clustering could ignore sim_threshold entirely and everything above passes.
    strict = cluster_claims_deterministic(items, sim_threshold=0.90, seed=7)
    assert strict["clusters"] == [[0], [1], [2]]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
