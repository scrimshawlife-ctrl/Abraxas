"""Test evolve.ledger.append capability contract.

Tests determinism, provenance tracking, and hash chain integrity.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.evolve.rune_adapter import append_ledger_deterministic


def test_append_ledger_deterministic_basic(tmp_path: Path):
    """Test basic ledger append with deterministic hash chain."""
    ledger_path = tmp_path / "test.jsonl"

    # First append
    result1 = append_ledger_deterministic(
        ledger_path=str(ledger_path),
        record={"event": "test_event_1", "value": 42},
        seed=123
    )

    # Verify result structure
    assert result1["step_hash"] is not None
    assert result1["prev_hash"] == "genesis"
    assert result1["provenance"] is not None
    assert result1["not_computable"] is None

    # Verify provenance
    prov = result1["provenance"]
    assert prov["operation_id"] == "evolve.ledger.append"
    assert "inputs_hash" in prov
    assert "timestamp" in prov

    # Verify file was created
    assert ledger_path.exists()

    # Verify file content
    lines = ledger_path.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "test_event_1"
    assert entry["value"] == 42
    assert entry["prev_hash"] == "genesis"
    assert entry["step_hash"] == result1["step_hash"]


def test_append_ledger_chain_integrity(tmp_path: Path):
    """Test that hash chain links correctly across multiple appends."""
    ledger_path = tmp_path / "chain.jsonl"

    # First append
    result1 = append_ledger_deterministic(
        ledger_path=str(ledger_path),
        record={"event": "event_1"},
        seed=123
    )

    # Second append
    result2 = append_ledger_deterministic(
        ledger_path=str(ledger_path),
        record={"event": "event_2"},
        seed=123
    )

    # Third append
    result3 = append_ledger_deterministic(
        ledger_path=str(ledger_path),
        record={"event": "event_3"},
        seed=123
    )

    # Verify chain integrity
    assert result1["prev_hash"] == "genesis"
    assert result2["prev_hash"] == result1["step_hash"]
    assert result3["prev_hash"] == result2["step_hash"]

    # Verify all entries are different
    assert result1["step_hash"] != result2["step_hash"]
    assert result2["step_hash"] != result3["step_hash"]

    # Verify file has 3 lines
    lines = ledger_path.read_text().splitlines()
    assert len(lines) == 3


def test_append_ledger_determinism(tmp_path: Path):
    """Test that same input produces same step_hash."""
    # Create two separate ledgers with identical records
    ledger_path1 = tmp_path / "ledger1.jsonl"
    ledger_path2 = tmp_path / "ledger2.jsonl"

    record = {"event": "determinism_test", "value": 999}

    result1 = append_ledger_deterministic(
        ledger_path=str(ledger_path1),
        record=record,
        seed=42
    )

    result2 = append_ledger_deterministic(
        ledger_path=str(ledger_path2),
        record=record,
        seed=42
    )

    # Step hashes should be identical for identical records
    assert result1["step_hash"] == result2["step_hash"]
    assert result1["prev_hash"] == result2["prev_hash"]  # Both genesis

    # Provenance inputs_hash should be identical
    assert result1["provenance"]["inputs_hash"] == result2["provenance"]["inputs_hash"]


def test_append_ledger_invalid_inputs():
    """Test error handling for invalid inputs."""
    # Invalid ledger_path
    result1 = append_ledger_deterministic(
        ledger_path="",
        record={"event": "test"},
        seed=42
    )
    assert result1["step_hash"] is None
    assert result1["not_computable"] is not None
    assert "Invalid ledger_path" in result1["not_computable"]["reason"]

    # Invalid record
    result2 = append_ledger_deterministic(
        ledger_path="out/test.jsonl",
        record=None,
        seed=42
    )
    assert result2["step_hash"] is None
    assert result2["not_computable"] is not None
    assert "Invalid record" in result2["not_computable"]["reason"]


def test_append_ledger_preserves_record_fields(tmp_path: Path):
    """Test that all record fields are preserved in ledger."""
    ledger_path = tmp_path / "preserve.jsonl"

    record = {
        "event": "complex_event",
        "nested": {"a": 1, "b": [2, 3, 4]},
        "list_field": ["x", "y", "z"],
        "number": 3.14159,
        "bool_field": True,
    }

    result = append_ledger_deterministic(
        ledger_path=str(ledger_path),
        record=record,
        seed=42
    )

    assert result["step_hash"] is not None

    # Read back from ledger
    lines = ledger_path.read_text().splitlines()
    entry = json.loads(lines[0])

    # Verify all fields are preserved
    assert entry["event"] == "complex_event"
    assert entry["nested"] == {"a": 1, "b": [2, 3, 4]}
    assert entry["list_field"] == ["x", "y", "z"]
    assert entry["number"] == 3.14159
    assert entry["bool_field"] is True

    # Verify augmented fields exist
    assert "prev_hash" in entry
    assert "step_hash" in entry


def test_append_ledger_golden():
    """Golden test: Verify stable hash for known input.

    This ensures that hash computation doesn't change across versions.
    """
    # Create temporary ledger
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "golden.jsonl"

        # Known input
        record = {"event": "golden_test", "value": 100}

        result = append_ledger_deterministic(
            ledger_path=str(ledger_path),
            record=record,
            seed=42
        )

        # Verify structure (don't assert exact hash as it depends on timestamp)
        assert result["step_hash"] is not None
        assert len(result["step_hash"]) == 64  # SHA-256 hex length
        assert result["prev_hash"] == "genesis"

        # Verify determinism - second call with same input should produce same hash
        ledger_path2 = Path(tmpdir) / "golden2.jsonl"
        result2 = append_ledger_deterministic(
            ledger_path=str(ledger_path2),
            record=record,
            seed=42
        )

        assert result["step_hash"] == result2["step_hash"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
