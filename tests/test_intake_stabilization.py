"""Tests for IntakeStabilizationPacket.v1 - core/oracle/stabilization.py"""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.stabilization import (
    IntakeStabilizationPacket,
    build_intake_stabilization_packet,
    compute_intake_stabilization_state,
    VALID_STABILIZATION_STATES,
    VALID_STATUSES,
    STABILIZATION_WINDOW_DEFAULT,
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


def test_build_stabilization_packet_stable(locked_authority):
    pkt = build_intake_stabilization_packet(
        stabilization_id="stab-001",
        intake_hash="a" * 64,
        replay_match_count=3,
        replay_failure_count=0,
        conflict_count=0,
        authority=locked_authority,
        stabilization_window=3,
    )
    assert pkt.schema_version == "IntakeStabilizationPacket.v1"
    assert pkt.stabilization_state == "stable"
    assert pkt.status == "complete"


def test_build_stabilization_packet_unstable_due_to_failures(locked_authority):
    """Replay failures affect stability."""
    pkt = build_intake_stabilization_packet(
        stabilization_id="stab-002",
        intake_hash="a" * 64,
        replay_match_count=2,
        replay_failure_count=1,
        conflict_count=0,
        authority=locked_authority,
    )
    assert pkt.stabilization_state == "unstable"


def test_unresolved_conflicts_block_stable_state(locked_authority):
    """Unresolved conflicts block stable state."""
    pkt = build_intake_stabilization_packet(
        stabilization_id="stab-003",
        intake_hash="a" * 64,
        replay_match_count=5,
        replay_failure_count=0,
        conflict_count=1,  # Conflict blocks stable
        authority=locked_authority,
    )
    assert pkt.stabilization_state == "conflicted"


def test_all_failures_produce_failed_state(locked_authority):
    pkt = build_intake_stabilization_packet(
        stabilization_id="stab-004",
        intake_hash="a" * 64,
        replay_match_count=0,
        replay_failure_count=3,
        conflict_count=0,
        authority=locked_authority,
    )
    assert pkt.stabilization_state == "failed"
    assert pkt.status == "failed"


def test_stabilizing_state(locked_authority):
    pkt = build_intake_stabilization_packet(
        stabilization_id="stab-005",
        intake_hash="a" * 64,
        replay_match_count=1,
        replay_failure_count=0,
        conflict_count=0,
        authority=locked_authority,
        stabilization_window=3,
    )
    assert pkt.stabilization_state == "stabilizing"
    assert pkt.status == "complete"


def test_stabilization_packet_requires_locked_authority(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        build_intake_stabilization_packet("stab1", "a" * 64, 3, 0, 0, unlocked_authority)


def test_stabilization_rejects_invalid_state(locked_authority):
    with pytest.raises(ValueError, match="stabilization_state"):
        IntakeStabilizationPacket(
            stabilization_id="s1",
            intake_hash="a" * 64,
            replay_match_count=1,
            replay_failure_count=0,
            conflict_count=0,
            stabilization_window=3,
            stabilization_state="unknown_state",
            authority=locked_authority,
            status="pending",
        )


def test_stabilization_rejects_negative_counts(locked_authority):
    with pytest.raises(ValueError, match="replay_match_count"):
        IntakeStabilizationPacket(
            stabilization_id="s1",
            intake_hash="a" * 64,
            replay_match_count=-1,
            replay_failure_count=0,
            conflict_count=0,
            stabilization_window=3,
            stabilization_state="unstable",
            authority=locked_authority,
            status="pending",
        )


def test_stabilization_rejects_zero_window(locked_authority):
    with pytest.raises(ValueError, match="stabilization_window"):
        IntakeStabilizationPacket(
            stabilization_id="s1",
            intake_hash="a" * 64,
            replay_match_count=0,
            replay_failure_count=0,
            conflict_count=0,
            stabilization_window=0,
            stabilization_state="unstable",
            authority=locked_authority,
            status="pending",
        )


def test_stabilization_hash_is_deterministic(locked_authority):
    pkt = build_intake_stabilization_packet("s1", "a" * 64, 3, 0, 0, locked_authority)
    h1 = pkt.stabilization_hash()
    h2 = pkt.stabilization_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_compute_stabilization_state_deterministic():
    state1 = compute_intake_stabilization_state(3, 0, 0, 3)
    state2 = compute_intake_stabilization_state(3, 0, 0, 3)
    assert state1 == state2 == "stable"


def test_all_valid_stabilization_states(locked_authority):
    for state in VALID_STABILIZATION_STATES:
        pkt = IntakeStabilizationPacket(
            stabilization_id="s1",
            intake_hash="a" * 64,
            replay_match_count=0,
            replay_failure_count=0,
            conflict_count=0,
            stabilization_window=3,
            stabilization_state=state,
            authority=locked_authority,
            status="pending",
        )
        assert pkt.stabilization_state == state
