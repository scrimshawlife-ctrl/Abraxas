"""Test evolve.policy.enforce_non_truncation capability contract.

Tests determinism, provenance tracking, and policy enforcement.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.evolve.rune_adapter import enforce_non_truncation_deterministic


def test_enforce_non_truncation_basic():
    """Test basic non-truncation policy enforcement."""
    artifact = {
        "version": "test.v1.0",
        "data": {"key": "value"}
    }
    raw_full = {"items": [1, 2, 3], "metadata": "test"}

    result = enforce_non_truncation_deterministic(
        artifact=artifact,
        raw_full=raw_full,
        seed=123
    )

    # Verify result structure
    assert result["artifact"] is not None
    assert result["provenance"] is not None
    assert result["not_computable"] is None

    # Verify policy flag
    assert result["artifact"]["policy"]["non_truncation"] is True

    # Verify raw_full is embedded
    assert "raw_full" in result["artifact"]
    assert result["artifact"]["raw_full"] == raw_full

    # Verify default fields are added
    assert "views" in result["artifact"]
    assert "flags" in result["artifact"]
    assert "metrics" in result["artifact"]

    # Verify provenance
    prov = result["provenance"]
    assert prov["operation_id"] == "evolve.policy.enforce_non_truncation"
    assert "inputs_hash" in prov
    assert "timestamp" in prov


def test_enforce_non_truncation_with_file_path(tmp_path: Path):
    """Test non-truncation with raw_full written to disk."""
    artifact = {
        "version": "test.v1.0",
        "summary": "test summary"
    }
    raw_full = {"large_data": list(range(1000))}
    raw_full_path = tmp_path / "raw_data.json"

    result = enforce_non_truncation_deterministic(
        artifact=artifact,
        raw_full=raw_full,
        raw_full_path=str(raw_full_path),
        seed=123
    )

    # Verify artifact has path reference instead of embedded data
    assert "raw_full_path" in result["artifact"]
    assert result["artifact"]["raw_full_path"] == str(raw_full_path)
    assert "raw_full" not in result["artifact"]

    # Verify file was created
    assert raw_full_path.exists()

    # Verify file content
    with open(raw_full_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data == raw_full


def test_enforce_non_truncation_determinism():
    """Test that same input produces same artifact structure."""
    artifact = {
        "version": "test.v1.0",
        "data": {"key": "value"}
    }
    raw_full = {"items": [1, 2, 3]}

    result1 = enforce_non_truncation_deterministic(
        artifact=artifact,
        raw_full=raw_full,
        seed=42
    )

    result2 = enforce_non_truncation_deterministic(
        artifact=artifact,
        raw_full=raw_full,
        seed=42
    )

    # Provenance inputs_hash should be identical for identical inputs
    assert result1["provenance"]["inputs_hash"] == result2["provenance"]["inputs_hash"]

    # Artifact structure should be identical (except timestamp)
    assert result1["artifact"]["policy"] == result2["artifact"]["policy"]
    assert result1["artifact"]["raw_full"] == result2["artifact"]["raw_full"]


def test_enforce_non_truncation_preserves_artifact_fields():
    """Test that existing artifact fields are preserved."""
    artifact = {
        "version": "test.v1.0",
        "existing_field": "preserved",
        "nested": {"data": [1, 2, 3]},
        "policy": {"existing_policy": True}
    }
    raw_full = {"additional": "data"}

    result = enforce_non_truncation_deterministic(
        artifact=artifact,
        raw_full=raw_full,
        seed=42
    )

    # Verify all existing fields are preserved
    assert result["artifact"]["version"] == "test.v1.0"
    assert result["artifact"]["existing_field"] == "preserved"
    assert result["artifact"]["nested"] == {"data": [1, 2, 3]}

    # Verify policy is updated (not replaced)
    assert result["artifact"]["policy"]["existing_policy"] is True
    assert result["artifact"]["policy"]["non_truncation"] is True


def test_enforce_non_truncation_invalid_inputs():
    """Test error handling for invalid inputs."""
    # Invalid artifact (empty)
    result1 = enforce_non_truncation_deterministic(
        artifact={},
        raw_full={"data": [1, 2, 3]},
        seed=42
    )
    # Empty dict is actually valid, so this should succeed
    assert result1["artifact"] is not None

    # Invalid artifact (None)
    result2 = enforce_non_truncation_deterministic(
        artifact=None,
        raw_full={"data": [1, 2, 3]},
        seed=42
    )
    assert result2["artifact"] is None
    assert result2["not_computable"] is not None
    assert "Invalid artifact" in result2["not_computable"]["reason"]

    # Invalid raw_full (None without existing raw_full in artifact)
    result3 = enforce_non_truncation_deterministic(
        artifact={"version": "test"},
        raw_full=None,
        seed=42
    )
    assert result3["artifact"] is None
    assert result3["not_computable"] is not None
    assert "Invalid raw_full" in result3["not_computable"]["reason"]


def test_enforce_non_truncation_various_raw_full_types():
    """Test that raw_full can be various data types."""
    artifact_base = {"version": "test.v1.0"}

    # Dict raw_full
    result1 = enforce_non_truncation_deterministic(
        artifact=artifact_base.copy(),
        raw_full={"key": "value"},
        seed=42
    )
    assert result1["artifact"]["raw_full"] == {"key": "value"}

    # List raw_full
    result2 = enforce_non_truncation_deterministic(
        artifact=artifact_base.copy(),
        raw_full=[1, 2, 3],
        seed=42
    )
    assert result2["artifact"]["raw_full"] == [1, 2, 3]

    # String raw_full
    result3 = enforce_non_truncation_deterministic(
        artifact=artifact_base.copy(),
        raw_full="plain string data",
        seed=42
    )
    assert result3["artifact"]["raw_full"] == "plain string data"

    # Number raw_full
    result4 = enforce_non_truncation_deterministic(
        artifact=artifact_base.copy(),
        raw_full=42,
        seed=42
    )
    assert result4["artifact"]["raw_full"] == 42


def test_enforce_non_truncation_golden():
    """Golden test: Verify stable structure for known input."""
    artifact = {
        "version": "golden.v1.0",
        "data": {"key": "value"}
    }
    raw_full = {"items": [1, 2, 3]}

    result = enforce_non_truncation_deterministic(
        artifact=artifact,
        raw_full=raw_full,
        seed=123
    )

    # Verify structure (don't assert exact values as timestamp will vary)
    assert result["artifact"]["policy"]["non_truncation"] is True
    assert result["artifact"]["raw_full"] == raw_full
    assert result["artifact"]["version"] == "golden.v1.0"
    assert result["provenance"]["operation_id"] == "evolve.policy.enforce_non_truncation"

    # Verify determinism - second call should produce same inputs_hash
    result2 = enforce_non_truncation_deterministic(
        artifact=artifact,
        raw_full=raw_full,
        seed=123
    )

    assert result["provenance"]["inputs_hash"] == result2["provenance"]["inputs_hash"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
