"""Tests for SandboxReplayPacket.v1 - core/sandbox/replay.py"""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.sandbox.replay import (
    SandboxReplayPacket,
    run_sandbox_replay,
    VALID_STATUSES,
)


@pytest.fixture
def auth() -> Authority:
    return Authority(
        authority_id="auth.replay.001",
        actor="system.replay",
        locked=True,
        scope="sandbox_only",
    )


def test_replay_match_when_hashes_equal(auth):
    pkt = run_sandbox_replay(
        source_branch_hash="a" * 64,
        replay_branch_hash="a" * 64,
        replay_id="rep-001",
        authority=auth,
    )
    assert pkt.deterministic_match is True
    assert pkt.status == "matched"
    assert pkt.mismatched_mutations == []


def test_replay_mismatch_when_hashes_differ(auth):
    pkt = run_sandbox_replay(
        source_branch_hash="a" * 64,
        replay_branch_hash="b" * 64,
        replay_id="rep-002",
        authority=auth,
    )
    assert pkt.deterministic_match is False
    assert pkt.status == "mismatch"
    assert len(pkt.mismatched_mutations) > 0


def test_replay_mismatch_invalidates_deterministic_match(auth):
    """Mismatched mutations force deterministic_match to False."""
    pkt = SandboxReplayPacket(
        replay_id="rep-003",
        source_branch_hash="a" * 64,
        replay_branch_hash="b" * 64,
        deterministic_match=True,  # Would be overridden
        mismatched_mutations=["mutation_x"],
        authority=auth,
        status="mismatch",
    )
    assert pkt.deterministic_match is False


def test_authority_must_be_locked():
    bad_auth = Authority(
        authority_id="bad",
        actor="x",
        locked=False,
        scope="sandbox_only",
    )
    with pytest.raises(ValueError, match="authority must be locked"):
        SandboxReplayPacket(
            replay_id="r",
            source_branch_hash="a" * 64,
            replay_branch_hash="a" * 64,
            deterministic_match=True,
            mismatched_mutations=[],
            authority=bad_auth,
            status="matched",
        )


def test_replay_hash_is_deterministic(auth):
    p1 = run_sandbox_replay("a" * 64, "a" * 64, "rep-x", auth)
    p2 = run_sandbox_replay("a" * 64, "a" * 64, "rep-x", auth)
    assert p1.replay_hash() == p2.replay_hash()


def test_replay_hash_differs_for_mismatch(auth):
    p1 = run_sandbox_replay("a" * 64, "a" * 64, "rep-x", auth)
    p2 = run_sandbox_replay("a" * 64, "b" * 64, "rep-x", auth)
    assert p1.replay_hash() != p2.replay_hash()


def test_invalid_status_raises(auth):
    with pytest.raises(ValueError, match="status"):
        SandboxReplayPacket(
            replay_id="r",
            source_branch_hash="a" * 64,
            replay_branch_hash="a" * 64,
            deterministic_match=True,
            mismatched_mutations=[],
            authority=auth,
            status="not_a_valid_status",
        )


def test_schema_version_correct(auth):
    pkt = run_sandbox_replay("a" * 64, "a" * 64, "r", auth)
    assert pkt.schema_version == "SandboxReplayPacket.v1"


def test_replay_mismatch_blocks_promotion(auth):
    """A replay mismatch must block promotion - verify mismatch is captured."""
    pkt = run_sandbox_replay("a" * 64, "b" * 64, "r", auth)
    assert pkt.deterministic_match is False
    assert pkt.mismatched_mutations  # Non-empty = blocks promotion
