"""Tests for IntakeApprovalPacket.v1 - core/oracle/approvals.py"""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.approvals import (
    IntakeApprovalPacket,
    build_approval_packet,
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


def test_build_approval_packet_defaults_false(locked_authority):
    """Approval defaults to False (operator review required)."""
    pkt = build_approval_packet(
        approval_id="appr-001",
        intake_hash="a" * 64,
        stabilization_hash="b" * 64,
        conflict_hashes=[],
        authority=locked_authority,
    )
    assert pkt.schema_version == "IntakeApprovalPacket.v1"
    assert pkt.approved is False
    assert pkt.status == "pending"
    assert pkt.approval_required is True


def test_approval_with_conflicts_is_blocked(locked_authority):
    """Unresolved conflicts block approval."""
    pkt = build_approval_packet(
        approval_id="appr-002",
        intake_hash="a" * 64,
        stabilization_hash="b" * 64,
        conflict_hashes=["conflict_hash_1"],
        authority=locked_authority,
    )
    assert pkt.approved is False
    assert pkt.status == "blocked"
    assert pkt.resolution_required_via_conflicts


def test_approval_requires_locked_authority(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        build_approval_packet("a1", "a" * 64, "b" * 64, [], unlocked_authority)


def test_approval_cannot_be_granted_with_conflicts(locked_authority):
    """Cannot approve if conflict_hashes present."""
    with pytest.raises(ValueError, match="unresolved conflicts"):
        IntakeApprovalPacket(
            approval_id="appr-bypass",
            intake_hash="a" * 64,
            stabilization_hash="b" * 64,
            conflict_hashes=["conflict1"],
            approval_required=True,
            approved=True,  # Should fail
            authority=locked_authority,
            status="approved",
        )


def test_approval_can_be_granted_without_conflicts(locked_authority):
    pkt = build_approval_packet(
        approval_id="appr-003",
        intake_hash="a" * 64,
        stabilization_hash="b" * 64,
        conflict_hashes=[],
        authority=locked_authority,
        approved=True,
    )
    assert pkt.approved is True
    assert pkt.status == "approved"


def test_approval_hash_is_deterministic(locked_authority):
    pkt = build_approval_packet("a1", "a" * 64, "b" * 64, [], locked_authority)
    h1 = pkt.approval_hash()
    h2 = pkt.approval_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_approval_rejects_invalid_status(locked_authority):
    with pytest.raises(ValueError, match="status"):
        IntakeApprovalPacket(
            approval_id="a1",
            intake_hash="a" * 64,
            stabilization_hash="b" * 64,
            conflict_hashes=[],
            approval_required=True,
            approved=False,
            authority=locked_authority,
            status="unknown_status",
        )


def test_all_valid_statuses(locked_authority):
    for status in VALID_STATUSES:
        # Skip "approved" with no conflicts only when approved=True
        if status == "approved":
            pkt = IntakeApprovalPacket(
                approval_id="a1",
                intake_hash="a" * 64,
                stabilization_hash="b" * 64,
                conflict_hashes=[],
                approval_required=True,
                approved=True,
                authority=locked_authority,
                status=status,
            )
        else:
            pkt = IntakeApprovalPacket(
                approval_id="a1",
                intake_hash="a" * 64,
                stabilization_hash="b" * 64,
                conflict_hashes=[],
                approval_required=True,
                approved=False,
                authority=locked_authority,
                status=status,
            )
        assert pkt.status == status


def test_approval_hash_differs_for_different_inputs(locked_authority):
    pkt1 = build_approval_packet("a1", "a" * 64, "b" * 64, [], locked_authority)
    pkt2 = build_approval_packet("a1", "c" * 64, "b" * 64, [], locked_authority)
    assert pkt1.approval_hash() != pkt2.approval_hash()


def test_blocked_approval_has_conflict_hashes(locked_authority):
    pkt = build_approval_packet(
        approval_id="a-blk",
        intake_hash="a" * 64,
        stabilization_hash="b" * 64,
        conflict_hashes=["ch1", "ch2"],
        authority=locked_authority,
    )
    assert pkt.conflict_hashes == ["ch1", "ch2"]
    assert pkt.approved is False
