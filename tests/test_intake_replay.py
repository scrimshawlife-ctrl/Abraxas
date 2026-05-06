"""Tests for IntakeReplayPacket.v1 - core/oracle/replay.py"""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.replay import (
    IntakeReplayPacket,
    run_intake_replay,
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


def test_run_intake_replay_matched(locked_authority):
    pkt = run_intake_replay(
        source_intake_hash="a" * 64,
        replay_intake_hash="a" * 64,
        replay_id="replay-001",
        authority=locked_authority,
    )
    assert pkt.schema_version == "IntakeReplayPacket.v1"
    assert pkt.deterministic_match is True
    assert pkt.status == "matched"
    assert pkt.mismatched_normalizations == []


def test_run_intake_replay_mismatch(locked_authority):
    pkt = run_intake_replay(
        source_intake_hash="a" * 64,
        replay_intake_hash="b" * 64,
        replay_id="replay-002",
        authority=locked_authority,
    )
    assert pkt.deterministic_match is False
    assert pkt.status == "mismatch"
    assert len(pkt.mismatched_normalizations) > 0


def test_replay_mismatch_invalidates_approval(locked_authority):
    """Replay mismatch must set deterministic_match=False."""
    pkt = run_intake_replay(
        source_intake_hash="a" * 64,
        replay_intake_hash="b" * 64,
        replay_id="replay-003",
        authority=locked_authority,
    )
    assert pkt.deterministic_match is False
    assert pkt.mismatched_normalizations


def test_normalization_mismatch_invalidates_replay(locked_authority):
    """Normalization hash mismatch must fail the replay."""
    pkt = run_intake_replay(
        source_intake_hash="a" * 64,
        replay_intake_hash="a" * 64,
        replay_id="replay-004",
        authority=locked_authority,
        source_normalization_hash="c" * 64,
        replay_normalization_hash="d" * 64,
    )
    assert pkt.deterministic_match is False
    assert pkt.status == "mismatch"


def test_mismatched_normalizations_force_deterministic_match_false(locked_authority):
    """Even if hash match, mismatched_normalizations must override deterministic_match."""
    pkt = IntakeReplayPacket(
        replay_id="replay-005",
        source_intake_hash="a" * 64,
        replay_intake_hash="a" * 64,
        deterministic_match=True,  # Will be overridden
        mismatched_normalizations=["some_mismatch"],
        authority=locked_authority,
        status="matched",
    )
    assert pkt.deterministic_match is False


def test_replay_requires_locked_authority(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        run_intake_replay("a" * 64, "a" * 64, "replay-006", unlocked_authority)


def test_replay_hash_is_deterministic(locked_authority):
    pkt = run_intake_replay("a" * 64, "a" * 64, "replay-001", locked_authority)
    h1 = pkt.replay_hash()
    h2 = pkt.replay_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_replay_hash_differs_for_mismatched_replay(locked_authority):
    pkt1 = run_intake_replay("a" * 64, "a" * 64, "replay-001", locked_authority)
    pkt2 = run_intake_replay("a" * 64, "b" * 64, "replay-001", locked_authority)
    assert pkt1.replay_hash() != pkt2.replay_hash()


def test_replay_rejects_invalid_status(locked_authority):
    with pytest.raises(ValueError, match="status"):
        IntakeReplayPacket(
            replay_id="replay-007",
            source_intake_hash="a" * 64,
            replay_intake_hash="a" * 64,
            deterministic_match=True,
            mismatched_normalizations=[],
            authority=locked_authority,
            status="unknown_status",
        )


def test_replay_self_replay_always_matches(locked_authority):
    """Self-replay (same hash) must always be deterministically matched."""
    hash_val = "f" * 64
    pkt = run_intake_replay(hash_val, hash_val, "replay-self", locked_authority)
    assert pkt.deterministic_match is True
    assert pkt.status == "matched"
