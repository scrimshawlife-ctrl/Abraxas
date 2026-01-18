"""Tests for shadow patch registry proposal-only behavior."""

from __future__ import annotations

from abraxas.shadow_metrics.patch_registry import SSMPatch, apply_patch, get_ledger


def test_patch_registry_proposal_only():
    patch = SSMPatch(
        patch_id="SSM-TEST-1",
        version="1.0.1",
        base_version=get_ledger().get_current_version(),
        metrics_affected=["SEI"],
        description="Test patch proposal",
        applied_at_utc="2025-01-01T00:00:00Z",
        git_sha="test",
        backward_compatible=True,
        provenance_hash="sha256:test",
    )

    receipt = apply_patch(patch)

    assert receipt["status"] == "proposal_only"
    assert receipt["patch_id"] == "SSM-TEST-1"
