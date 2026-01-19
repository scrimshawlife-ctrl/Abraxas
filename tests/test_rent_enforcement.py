"""
Tests for Rent Enforcement Coverage Metric

Tests for measuring rent enforcement coverage across Abraxas components.
"""

import pytest
from abraxas.governance.rent_manifest_loader import (
    load_all_manifests,
    get_manifest_summary,
    discover_component_registry,
    find_unmanifested_components,
)
from pathlib import Path


def test_coverage_computation():
    """Test rent enforcement coverage computation."""
    # Load all manifests
    repo_root = Path(__file__).parent.parent
    manifests = load_all_manifests(str(repo_root))

    # Get summary
    summary = get_manifest_summary(manifests)

    # Basic coverage check: we should have at least some manifests
    assert summary["total_manifests"] > 0, "Should have at least one manifest"

    # Coverage percentage is total manifests / total components
    # For now, just verify the data structure is correct
    assert "by_kind" in summary
    assert "metrics" in summary["by_kind"]
    assert "operators" in summary["by_kind"]
    assert "artifacts" in summary["by_kind"]


def test_unmanifested_detection():
    """Test detection of components without manifests."""
    repo_root = Path(__file__).parent.parent
    manifests = load_all_manifests(str(repo_root))

    registry = discover_component_registry(str(repo_root))
    unmanifested = find_unmanifested_components(registry, manifests)

    assert registry["metrics"]
    assert registry["operators"]
    assert registry["artifacts"]

    assert any(unmanifested.values()), "Expected at least one unmanifested component"
    for kind, modules in unmanifested.items():
        assert set(modules).issubset(set(registry[kind]))
