"""Tests for IntakeConflictPacket.v1 - core/oracle/conflicts.py"""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.conflicts import (
    IntakeConflictPacket,
    build_conflict_packet,
    detect_duplicate_sources,
    VALID_CONFLICT_TYPES,
    VALID_SEVERITIES,
    VALID_STATUSES,
)


@pytest.fixture
def locked_authority() -> Authority:
    return Authority(
        authority_id="auth.test.001",
        actor="system.test",
        locked=True,
        scope="oracle_intake_only",
    )


@pytest.fixture
def unlocked_authority() -> Authority:
    return Authority(
        authority_id="auth.test.bad",
        actor="system.test",
        locked=False,
        scope="oracle_intake_only",
    )


def test_build_conflict_packet_unresolved(locked_authority):
    pkt = build_conflict_packet(
        conflict_id="conflict-001",
        conflicting_source_hashes=["a" * 64, "b" * 64],
        conflict_type="provenance_mismatch",
        authority=locked_authority,
    )
    assert pkt.schema_version == "IntakeConflictPacket.v1"
    assert pkt.status == "unresolved"
    assert pkt.resolution_required is True


def test_duplicate_source_collapses_cleanly(locked_authority):
    """Duplicate deterministic sources must collapse cleanly."""
    dup_hash = "a" * 64
    pkt = build_conflict_packet(
        conflict_id="conflict-dup",
        conflicting_source_hashes=[dup_hash, dup_hash],
        conflict_type="duplicate_source",
        authority=locked_authority,
        severity="low",
    )
    assert pkt.status == "collapsed"
    assert pkt.resolution_required is False


def test_authority_violation_fails_closed(locked_authority):
    """Authority violations must fail closed."""
    pkt = build_conflict_packet(
        conflict_id="conflict-auth",
        conflicting_source_hashes=["a" * 64],
        conflict_type="authority_violation",
        authority=locked_authority,
    )
    assert pkt.status == "failed"
    assert pkt.severity == "critical"
    assert pkt.resolution_required is True


def test_conflict_packet_requires_locked_authority(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        build_conflict_packet("c1", ["a" * 64], "provenance_mismatch", unlocked_authority)


def test_conflict_packet_rejects_invalid_type(locked_authority):
    with pytest.raises(ValueError, match="conflict_type"):
        IntakeConflictPacket(
            conflict_id="c1",
            conflicting_source_hashes=["a" * 64],
            conflict_type="unknown_type",
            severity="medium",
            authority=locked_authority,
            resolution_required=True,
            status="unresolved",
        )


def test_conflict_packet_rejects_invalid_severity(locked_authority):
    with pytest.raises(ValueError, match="severity"):
        IntakeConflictPacket(
            conflict_id="c1",
            conflicting_source_hashes=["a" * 64],
            conflict_type="provenance_mismatch",
            severity="extreme",
            authority=locked_authority,
            resolution_required=True,
            status="unresolved",
        )


def test_conflict_packet_rejects_invalid_status(locked_authority):
    with pytest.raises(ValueError, match="status"):
        IntakeConflictPacket(
            conflict_id="c1",
            conflicting_source_hashes=["a" * 64],
            conflict_type="provenance_mismatch",
            severity="medium",
            authority=locked_authority,
            resolution_required=True,
            status="unknown",
        )


def test_all_conflict_types_accepted(locked_authority):
    for ctype in VALID_CONFLICT_TYPES:
        if ctype == "authority_violation":
            pkt = build_conflict_packet("c1", ["a" * 64], ctype, locked_authority)
            assert pkt.status == "failed"
        elif ctype == "duplicate_source":
            pkt = build_conflict_packet("c1", ["a" * 64, "a" * 64], ctype, locked_authority)
            assert pkt.status == "collapsed"
        else:
            pkt = build_conflict_packet("c1", ["a" * 64, "b" * 64], ctype, locked_authority)
            assert pkt.status == "unresolved"


def test_detect_duplicate_sources_identifies_duplicates():
    hashes = ["a" * 64, "b" * 64, "a" * 64]
    dups = detect_duplicate_sources(hashes)
    assert "a" * 64 in dups
    assert "b" * 64 not in dups


def test_detect_duplicate_sources_empty_for_unique():
    hashes = ["a" * 64, "b" * 64, "c" * 64]
    dups = detect_duplicate_sources(hashes)
    assert dups == []


def test_conflict_hash_is_deterministic(locked_authority):
    pkt = build_conflict_packet("c1", ["a" * 64, "b" * 64], "provenance_mismatch", locked_authority)
    h1 = pkt.conflict_hash()
    h2 = pkt.conflict_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_non_duplicate_source_conflict_unresolved(locked_authority):
    """Non-duplicate duplicate_source conflict stays unresolved."""
    pkt = build_conflict_packet(
        "c1", ["a" * 64, "b" * 64], "duplicate_source", locked_authority
    )
    # No actual duplicates, so it falls through to unresolved
    assert pkt.status == "unresolved"
