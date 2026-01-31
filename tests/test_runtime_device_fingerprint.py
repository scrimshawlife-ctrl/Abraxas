"""Tests for runtime/device_fingerprint module."""

import pytest

from abraxas.runtime.device_fingerprint import get_device_fingerprint


def test_fingerprint_structure():
    """Verify fingerprint returns expected keys."""
    fp = get_device_fingerprint()

    assert "cpu_arch" in fp
    assert "platform_id" in fp
    assert "mem_total_bytes" in fp
    assert "storage_class" in fp
    assert "gpu_present" in fp
    assert "fingerprint_hash" in fp

    # Types
    assert isinstance(fp["cpu_arch"], str)
    assert isinstance(fp["platform_id"], str)
    assert isinstance(fp["mem_total_bytes"], int)
    assert isinstance(fp["gpu_present"], bool)
    assert isinstance(fp["fingerprint_hash"], str)


def test_fingerprint_determinism():
    """Verify same device produces same fingerprint hash."""
    fp1 = get_device_fingerprint()
    fp2 = get_device_fingerprint()

    assert fp1["fingerprint_hash"] == fp2["fingerprint_hash"]
    assert fp1["cpu_arch"] == fp2["cpu_arch"]
    assert fp1["platform_id"] == fp2["platform_id"]


def test_fingerprint_with_run_ctx():
    """Verify run_ctx injection adds now_utc."""
    ctx = {"now_utc": "2026-01-31T12:00:00Z"}
    fp = get_device_fingerprint(run_ctx=ctx)

    assert fp.get("now_utc") == "2026-01-31T12:00:00Z"


def test_fingerprint_without_run_ctx():
    """Verify fingerprint works without run_ctx."""
    fp = get_device_fingerprint(run_ctx=None)

    assert "now_utc" not in fp
    assert "fingerprint_hash" in fp


def test_fingerprint_hash_is_sha256():
    """Verify hash appears to be SHA-256 format."""
    fp = get_device_fingerprint()

    # SHA-256 produces 64 hex characters
    assert len(fp["fingerprint_hash"]) == 64
    assert all(c in "0123456789abcdef" for c in fp["fingerprint_hash"])
