"""
Tests for Rent Enforcement Coverage Metric

Tests for measuring rent enforcement coverage across Abraxas components.
"""

import pytest
from abraxas.governance.rent_manifest_loader import (
    load_all_manifests,
    get_manifest_summary,
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
    # Placeholder test for detecting unmanifested components
    # TODO: Implement component registry and diff against manifests

    # For now, just verify manifest loading works
    repo_root = Path(__file__).parent.parent
    manifests = load_all_manifests(str(repo_root))

    assert manifests is not None
    assert isinstance(manifests, dict)
