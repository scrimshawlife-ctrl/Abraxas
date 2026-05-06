"""Tests for ExecutionRollbackPacket."""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.runes.rollback import ExecutionRollbackPacket, generate_rollback_packet

LOCKED_AUTHORITY = Authority(
    authority_id="auth.test.001",
    actor="test.actor",
    locked=True,
    scope="shadow_only",
)

UNLOCKED_AUTHORITY = Authority(
    authority_id="auth.test.bad",
    actor="test.actor",
    locked=False,
    scope="shadow_only",
)


def test_rollback_packet_creation():
    pkt = generate_rollback_packet(
        source_execution_id="exec-001",
        reverted_receipts=["rcpt-001", "rcpt-002"],
        reason="validation failed",
        authority=LOCKED_AUTHORITY,
    )
    assert pkt.schema_version == "ExecutionRollbackPacket.v1"


def test_rollback_packet_authority_locked():
    pkt = generate_rollback_packet(
        source_execution_id="exec-001",
        reverted_receipts=["rcpt-001"],
        reason="test",
        authority=LOCKED_AUTHORITY,
    )
    assert pkt.authority.is_locked()


def test_rollback_packet_unlocked_authority_fails():
    with pytest.raises((ValueError, Exception)):
        generate_rollback_packet(
            source_execution_id="exec-001",
            reverted_receipts=["rcpt-001"],
            reason="test",
            authority=UNLOCKED_AUTHORITY,
        )


def test_rollback_possible_when_receipts_present():
    pkt = generate_rollback_packet(
        source_execution_id="exec-001",
        reverted_receipts=["rcpt-001", "rcpt-002"],
        reason="validation failed",
        authority=LOCKED_AUTHORITY,
    )
    assert pkt.rollback_possible is True


def test_rollback_not_possible_when_no_receipts():
    pkt = generate_rollback_packet(
        source_execution_id="exec-001",
        reverted_receipts=[],
        reason="no receipts",
        authority=LOCKED_AUTHORITY,
    )
    assert pkt.rollback_possible is False


def test_rollback_id_deterministic():
    pkt1 = generate_rollback_packet(
        source_execution_id="exec-001",
        reverted_receipts=["rcpt-001"],
        reason="test",
        authority=LOCKED_AUTHORITY,
    )
    pkt2 = generate_rollback_packet(
        source_execution_id="exec-001",
        reverted_receipts=["rcpt-001"],
        reason="test",
        authority=LOCKED_AUTHORITY,
    )
    assert pkt1.rollback_id == pkt2.rollback_id


def test_rollback_id_changes_with_different_execution():
    pkt1 = generate_rollback_packet(
        source_execution_id="exec-001",
        reverted_receipts=["rcpt-001"],
        reason="test",
        authority=LOCKED_AUTHORITY,
    )
    pkt2 = generate_rollback_packet(
        source_execution_id="exec-002",
        reverted_receipts=["rcpt-001"],
        reason="test",
        authority=LOCKED_AUTHORITY,
    )
    assert pkt1.rollback_id != pkt2.rollback_id


def test_rollback_validation_field_present():
    pkt = generate_rollback_packet(
        source_execution_id="exec-001",
        reverted_receipts=["rcpt-001"],
        reason="route validation failed",
        authority=LOCKED_AUTHORITY,
    )
    assert pkt.rollback_reason == "route validation failed"
    assert pkt.source_execution_id == "exec-001"
