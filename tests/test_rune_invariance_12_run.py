"""
ABX-Runes Invariance Test: 12-Run Determinism

Validates that the same rune invocation produces byte-for-byte identical
outputs across 12 consecutive runs with identical inputs and ASE_KEY.
"""
from __future__ import annotations

import os
import pytest
from typing import Any, Dict, List

from abraxas_ase.runes import invoke_rune, clear_caches
from abraxas_ase.provenance import stable_json_dumps


# Test data: deterministic items
TEST_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "item-001",
        "source": "reuters",
        "published_at": "2026-01-24T10:00:00Z",
        "title": "TRADE WAR ESCALATES AFTER NEW TARIFFS",
        "text": "The ongoing trade dispute intensified today. Leaders warned of economic war.",
        "url": "https://example.com/1",
    },
    {
        "id": "item-002",
        "source": "ap",
        "published_at": "2026-01-24T11:00:00Z",
        "title": "PEACE TALKS COLLAPSE AS NEGOTIATIONS FAIL",
        "text": "Diplomatic efforts ended without agreement. War fears rise.",
        "url": "https://example.com/2",
    },
    {
        "id": "item-003",
        "source": "bbc",
        "published_at": "2026-01-24T12:00:00Z",
        "title": "MARKET CRASH TRIGGERS PANIC SELLING",
        "text": "Stock markets plunged amid trade war concerns. Investors fear recession.",
        "url": "https://example.com/3",
    },
]

TEST_PAYLOAD = {
    "items": TEST_ITEMS,
    "params": {
        "min_token_len": 4,
        "min_sub_len": 3,
    },
}

TEST_CTX = {
    "run_id": "INVARIANCE-TEST-001",
    "date": "2026-01-24",
    "tier": "academic",
}


@pytest.fixture(autouse=True)
def set_ase_key():
    """Set deterministic ASE_KEY for all tests."""
    original = os.environ.get("ASE_KEY")
    os.environ["ASE_KEY"] = "test-invariance-key-12run"
    yield
    if original is not None:
        os.environ["ASE_KEY"] = original
    else:
        os.environ.pop("ASE_KEY", None)


@pytest.fixture(autouse=True)
def clear_rune_caches():
    """Clear caches before each test."""
    clear_caches()
    yield
    clear_caches()


class TestRuneInvariance12Run:
    """Test 12-run invariance for rune invocations."""

    def test_text_subword_12_run_invariance(self):
        """
        Invoke sdct.text_subword.v1 rune 12 times with identical inputs.
        Assert all outputs are byte-for-byte identical.
        """
        rune_id = "sdct.text_subword.v1"
        results: List[str] = []

        for run_num in range(12):
            result = invoke_rune(rune_id, TEST_PAYLOAD, TEST_CTX)

            # Remove any non-deterministic fields (if any)
            # The rune should already be fully deterministic
            output_json = stable_json_dumps(result)
            results.append(output_json)

        # All 12 outputs must be identical
        first_output = results[0]
        for i, output in enumerate(results[1:], start=2):
            assert output == first_output, (
                f"Run {i} differs from run 1.\n"
                f"First 500 chars of run 1: {first_output[:500]}\n"
                f"First 500 chars of run {i}: {output[:500]}"
            )

    def test_text_subword_hash_stability(self):
        """
        Verify that input_hash in provenance is stable across runs.
        """
        rune_id = "sdct.text_subword.v1"
        hashes: List[str] = []

        for _ in range(12):
            result = invoke_rune(rune_id, TEST_PAYLOAD, TEST_CTX)
            hashes.append(result["provenance"]["input_hash"])

        # All input hashes must be identical
        assert len(set(hashes)) == 1, f"Input hashes vary: {set(hashes)}"

    def test_evidence_row_ordering_stability(self):
        """
        Verify that evidence rows maintain stable ordering across runs.
        """
        rune_id = "sdct.text_subword.v1"
        orderings: List[List[str]] = []

        for _ in range(12):
            result = invoke_rune(rune_id, TEST_PAYLOAD, TEST_CTX)
            motif_ids = [row["motif_id"] for row in result["evidence_rows"]]
            orderings.append(motif_ids)

        # All orderings must be identical
        first_ordering = orderings[0]
        for i, ordering in enumerate(orderings[1:], start=2):
            assert ordering == first_ordering, (
                f"Evidence row ordering differs at run {i}"
            )

    def test_motif_stats_ordering_stability(self):
        """
        Verify that motif_stats maintain stable ordering across runs.
        """
        rune_id = "sdct.text_subword.v1"
        orderings: List[List[str]] = []

        for _ in range(12):
            result = invoke_rune(rune_id, TEST_PAYLOAD, TEST_CTX)
            motif_ids = [stat["motif_id"] for stat in result["motif_stats"]]
            orderings.append(motif_ids)

        # All orderings must be identical
        first_ordering = orderings[0]
        for i, ordering in enumerate(orderings[1:], start=2):
            assert ordering == first_ordering, (
                f"Motif stats ordering differs at run {i}"
            )

    def test_empty_items_invariance(self):
        """
        Verify invariance with empty items (not_computable case).
        """
        rune_id = "sdct.text_subword.v1"
        payload = {"items": []}
        results: List[str] = []

        for _ in range(12):
            result = invoke_rune(rune_id, payload, TEST_CTX)
            results.append(stable_json_dumps(result))

        # All outputs must be identical
        assert len(set(results)) == 1, "Empty items outputs vary"

    def test_single_item_invariance(self):
        """
        Verify invariance with a single item.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {"items": [TEST_ITEMS[0]]}
        results: List[str] = []

        for _ in range(12):
            result = invoke_rune(rune_id, payload, TEST_CTX)
            results.append(stable_json_dumps(result))

        # All outputs must be identical
        assert len(set(results)) == 1, "Single item outputs vary"


class TestDeterministicProvenance:
    """Test provenance determinism."""

    def test_provenance_fields_present(self):
        """Verify all required provenance fields are present."""
        rune_id = "sdct.text_subword.v1"
        result = invoke_rune(rune_id, TEST_PAYLOAD, TEST_CTX)

        prov = result["provenance"]
        assert "rune_id" in prov
        assert "rune_version" in prov
        assert "input_hash" in prov
        assert "schema_versions" in prov

    def test_provenance_rune_id_matches(self):
        """Verify provenance rune_id matches invoked rune."""
        rune_id = "sdct.text_subword.v1"
        result = invoke_rune(rune_id, TEST_PAYLOAD, TEST_CTX)

        assert result["provenance"]["rune_id"] == rune_id

    def test_input_hash_is_sha256(self):
        """Verify input_hash is a valid SHA-256 hex string."""
        rune_id = "sdct.text_subword.v1"
        result = invoke_rune(rune_id, TEST_PAYLOAD, TEST_CTX)

        input_hash = result["provenance"]["input_hash"]
        assert len(input_hash) == 64
        assert all(c in "0123456789abcdef" for c in input_hash)


# Import clear_caches for cleanup
from abraxas_ase.runes.invoke import clear_caches
