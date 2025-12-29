"""Tests for Shadow Structural Metrics patch registry.

Verifies patch management and version tracking.
"""

import pytest

from abraxas.shadow_metrics.patch_registry import (
    SSMPatch,
    SSMPatchLedger,
    get_ledger,
    validate_patch_chain,
)


def test_baseline_exists():
    """Verify baseline patch exists in ledger."""
    ledger = get_ledger()

    assert ledger.baseline_version == "1.0.0"
    assert ledger.baseline_date == "2025-12-29"
    assert len(ledger.patches) >= 1

    baseline = ledger.patches[0]
    assert baseline.patch_id == "SSM-BASELINE-1.0.0"
    assert baseline.version == "1.0.0"
    assert baseline.backward_compatible is True


def test_patch_chain_valid():
    """Verify patch chain is valid."""
    assert validate_patch_chain() is True


def test_backward_incompatible_patch_rejected():
    """Verify backward-incompatible patches are rejected."""
    ledger = SSMPatchLedger()

    patch = SSMPatch(
        patch_id="TEST-INVALID",
        version="1.1.0",
        base_version="1.0.0",
        metrics_affected=["SEI"],
        description="Breaking change",
        applied_at_utc="2025-12-29T12:00:00Z",
        backward_compatible=False,  # NOT allowed
        provenance_hash="sha256:test",
    )

    with pytest.raises(ValueError) as exc_info:
        ledger.add_patch(patch)

    assert "backward compatibility" in str(exc_info.value)


def test_same_version_patch_rejected():
    """Verify patches with same base and target version are rejected."""
    ledger = SSMPatchLedger()

    patch = SSMPatch(
        patch_id="TEST-SAME-VERSION",
        version="1.0.0",
        base_version="1.0.0",  # Same as version
        metrics_affected=["SEI"],
        description="Invalid patch",
        applied_at_utc="2025-12-29T12:00:00Z",
        backward_compatible=True,
        provenance_hash="sha256:test",
    )

    with pytest.raises(ValueError) as exc_info:
        ledger.add_patch(patch)

    assert "same base and target version" in str(exc_info.value)


def test_get_current_version():
    """Verify current version retrieval."""
    ledger = get_ledger()
    version = ledger.get_current_version()

    assert version == "1.0.0"  # Current baseline


def test_patch_append_only():
    """Verify patches are append-only (write-once)."""
    ledger = SSMPatchLedger()

    patch1 = SSMPatch(
        patch_id="PATCH-1",
        version="1.0.1",
        base_version="1.0.0",
        metrics_affected=["SEI"],
        description="First patch",
        applied_at_utc="2025-12-29T12:00:00Z",
        backward_compatible=True,
        provenance_hash="sha256:patch1",
    )

    patch2 = SSMPatch(
        patch_id="PATCH-2",
        version="1.0.2",
        base_version="1.0.1",
        metrics_affected=["CLIP"],
        description="Second patch",
        applied_at_utc="2025-12-29T13:00:00Z",
        backward_compatible=True,
        provenance_hash="sha256:patch2",
    )

    ledger.add_patch(patch1)
    ledger.add_patch(patch2)

    # Both patches should be in ledger
    assert len(ledger.patches) == 2
    assert ledger.patches[0].patch_id == "PATCH-1"
    assert ledger.patches[1].patch_id == "PATCH-2"

    # Current version should be 1.0.2
    assert ledger.get_current_version() == "1.0.2"
