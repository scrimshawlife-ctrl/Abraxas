"""
Test Rent Manifest Validation

Tests for manifest loading and schema validation.
"""

import pytest
from abraxas.governance.rent_manifest_loader import (
    validate_manifest,
    ManifestValidationError,
    load_all_manifests,
    get_manifest_summary,
)


def test_valid_metric_manifest():
    """Test that a valid metric manifest passes validation."""
    manifest = {
        "id": "test_metric",
        "kind": "metric",
        "domain": "TAU",
        "description": "A test metric",
        "owner_module": "abraxas.metrics.test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "inputs": ["input1", "input2"],
        "outputs": ["output1"],
        "cost_model": {
            "time_ms_expected": 50,
            "memory_kb_expected": 1024,
            "io_expected": "read",
        },
        "rent_claim": {
            "improves": ["auditability"],
            "measurable_by": ["golden_test"],
            "thresholds": {"accuracy_min": 0.9},
        },
        "proof": {
            "tests": ["tests/test_example.py::test_something"],
            "golden_files": ["tests/golden/example.json"],
            "ledgers_touched": ["out/ledgers/test.jsonl"],
        },
    }

    # Should not raise
    validate_manifest(manifest)


def test_valid_operator_manifest():
    """Test that a valid operator manifest passes validation."""
    manifest = {
        "id": "test_operator",
        "kind": "operator",
        "domain": "ROUTING",
        "description": "A test operator",
        "owner_module": "abraxas.operators.test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "operator_id": "test_operator",
        "inputs": ["input1"],
        "outputs": ["output1"],
        "cost_model": {
            "time_ms_expected": 25,
            "memory_kb_expected": 512,
            "io_expected": "none",
        },
        "rent_claim": {
            "improves": ["routing_determinism"],
            "measurable_by": ["golden_test"],
            "thresholds": {},
        },
        "proof": {
            "tests": ["tests/test_example.py::test_operator"],
            "golden_files": [],
            "ledgers_touched": ["out/ledgers/operator.jsonl"],
        },
        "ter_edges_claimed": [{"from": "a", "to": "b"}],
    }

    # Should not raise
    validate_manifest(manifest)


def test_valid_artifact_manifest():
    """Test that a valid artifact manifest passes validation."""
    manifest = {
        "id": "test_artifact",
        "kind": "artifact",
        "domain": "INTEGRITY",
        "description": "A test artifact",
        "owner_module": "abraxas.artifacts.test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "artifact_id": "test_artifact",
        "cost_model": {
            "time_ms_expected": 100,
            "memory_kb_expected": 2048,
            "io_expected": "write",
        },
        "rent_claim": {
            "improves": ["operational_transparency"],
            "measurable_by": ["artifact_completeness_check"],
            "thresholds": {},
        },
        "proof": {
            "tests": ["tests/test_example.py::test_artifact"],
            "golden_files": ["tests/golden/artifact.json"],
            "ledgers_touched": [],
        },
        "output_paths": ["out/artifacts/test.json"],
        "uniqueness_claim": ["contains_deltas"],
    }

    # Should not raise
    validate_manifest(manifest)


def test_missing_required_field():
    """Test that missing required field raises validation error."""
    manifest = {
        "id": "test",
        "kind": "metric",
        # Missing domain
        "description": "Test",
        "owner_module": "test",
        "version": "0.1",
        "created_at": "2025-12-26",
    }

    with pytest.raises(ManifestValidationError, match="Missing required field: domain"):
        validate_manifest(manifest)


def test_invalid_kind():
    """Test that invalid kind raises validation error."""
    manifest = {
        "id": "test",
        "kind": "invalid_kind",
        "domain": "TAU",
        "description": "Test",
        "owner_module": "test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "inputs": [],
        "outputs": [],
        "cost_model": {
            "time_ms_expected": 0,
            "memory_kb_expected": 0,
            "io_expected": "none",
        },
        "rent_claim": {
            "improves": ["test"],
            "measurable_by": ["test"],
            "thresholds": {},
        },
        "proof": {"tests": [], "golden_files": [], "ledgers_touched": []},
    }

    with pytest.raises(ManifestValidationError, match="Invalid kind"):
        validate_manifest(manifest)


def test_invalid_domain():
    """Test that invalid domain raises validation error."""
    manifest = {
        "id": "test",
        "kind": "metric",
        "domain": "INVALID_DOMAIN",
        "description": "Test",
        "owner_module": "test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "inputs": [],
        "outputs": [],
        "cost_model": {
            "time_ms_expected": 0,
            "memory_kb_expected": 0,
            "io_expected": "none",
        },
        "rent_claim": {
            "improves": ["test"],
            "measurable_by": ["test"],
            "thresholds": {},
        },
        "proof": {"tests": [], "golden_files": [], "ledgers_touched": []},
    }

    with pytest.raises(ManifestValidationError, match="Invalid domain"):
        validate_manifest(manifest)


def test_negative_cost_model_values():
    """Test that negative cost model values raise validation error."""
    manifest = {
        "id": "test",
        "kind": "metric",
        "domain": "TAU",
        "description": "Test",
        "owner_module": "test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "inputs": [],
        "outputs": [],
        "cost_model": {
            "time_ms_expected": -10,  # Invalid
            "memory_kb_expected": 1024,
            "io_expected": "none",
        },
        "rent_claim": {
            "improves": ["test"],
            "measurable_by": ["test"],
            "thresholds": {},
        },
        "proof": {"tests": [], "golden_files": [], "ledgers_touched": []},
    }

    with pytest.raises(ManifestValidationError, match="must be non-negative"):
        validate_manifest(manifest)


def test_invalid_test_format():
    """Test that invalid test format raises validation error."""
    manifest = {
        "id": "test",
        "kind": "metric",
        "domain": "TAU",
        "description": "Test",
        "owner_module": "test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "inputs": [],
        "outputs": [],
        "cost_model": {
            "time_ms_expected": 0,
            "memory_kb_expected": 0,
            "io_expected": "none",
        },
        "rent_claim": {
            "improves": ["test"],
            "measurable_by": ["test"],
            "thresholds": {},
        },
        "proof": {
            "tests": ["invalid_test_format"],  # Missing ::
            "golden_files": [],
            "ledgers_touched": [],
        },
    }

    with pytest.raises(
        ManifestValidationError, match="must be in pytest node ID format"
    ):
        validate_manifest(manifest)


def test_empty_rent_claim_lists():
    """Test that empty rent claim lists raise validation error."""
    manifest = {
        "id": "test",
        "kind": "metric",
        "domain": "TAU",
        "description": "Test",
        "owner_module": "test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "inputs": [],
        "outputs": [],
        "cost_model": {
            "time_ms_expected": 0,
            "memory_kb_expected": 0,
            "io_expected": "none",
        },
        "rent_claim": {
            "improves": [],  # Empty
            "measurable_by": ["test"],
            "thresholds": {},
        },
        "proof": {"tests": [], "golden_files": [], "ledgers_touched": []},
    }

    with pytest.raises(ManifestValidationError, match="must not be empty"):
        validate_manifest(manifest)


def test_load_all_manifests_from_repo(tmp_path):
    """Test loading manifests from repository structure."""
    # This test will use the actual repo structure
    import os
    from pathlib import Path

    repo_root = Path(__file__).parent.parent
    manifests = load_all_manifests(str(repo_root))

    # Should return dict with three keys
    assert "metrics" in manifests
    assert "operators" in manifests
    assert "artifacts" in manifests

    # Get summary
    summary = get_manifest_summary(manifests)
    assert "total_manifests" in summary
    assert "by_kind" in summary


def test_manifest_summary():
    """Test manifest summary generation."""
    manifests = {
        "metrics": [{"id": "m1"}, {"id": "m2"}],
        "operators": [{"id": "o1"}],
        "artifacts": [],
    }

    summary = get_manifest_summary(manifests)

    assert summary["total_manifests"] == 3
    assert summary["by_kind"]["metrics"] == 2
    assert summary["by_kind"]["operators"] == 1
    assert summary["by_kind"]["artifacts"] == 0
    assert summary["ids"]["metrics"] == ["m1", "m2"]
    assert summary["ids"]["operators"] == ["o1"]
