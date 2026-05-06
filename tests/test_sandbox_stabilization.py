"""Tests for SandboxStabilizationPacket.v1 - core/sandbox/stabilization.py"""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.sandbox.stabilization import (
    SandboxStabilizationPacket,
    build_stabilization_packet,
    compute_stabilization_state,
    VALID_STABILIZATION_STATES,
)


@pytest.fixture
def auth() -> Authority:
    return Authority(
        authority_id="auth.stab.001",
        actor="system.stabilization",
        locked=True,
        scope="sandbox_only",
    )


def test_stable_when_matches_reach_window(auth):
    pkt = build_stabilization_packet(
        "stab-001", "a" * 64, replay_match_count=3,
        replay_failure_count=0, authority=auth, stabilization_window=3
    )
    assert pkt.stabilization_state == "stable"


def test_stabilizing_when_matches_below_window(auth):
    pkt = build_stabilization_packet(
        "stab-001", "a" * 64, replay_match_count=2,
        replay_failure_count=0, authority=auth, stabilization_window=3
    )
    assert pkt.stabilization_state == "stabilizing"


def test_unstable_when_zero_matches_zero_failures(auth):
    pkt = build_stabilization_packet(
        "stab-001", "a" * 64, replay_match_count=0,
        replay_failure_count=0, authority=auth, stabilization_window=3
    )
    assert pkt.stabilization_state == "unstable"


def test_unstable_when_failures_present(auth):
    pkt = build_stabilization_packet(
        "stab-001", "a" * 64, replay_match_count=2,
        replay_failure_count=1, authority=auth, stabilization_window=3
    )
    assert pkt.stabilization_state == "unstable"


def test_failed_when_all_failures(auth):
    pkt = build_stabilization_packet(
        "stab-001", "a" * 64, replay_match_count=0,
        replay_failure_count=2, authority=auth, stabilization_window=3
    )
    assert pkt.stabilization_state == "failed"


def test_unstable_blocks_promotion(auth):
    pkt = build_stabilization_packet(
        "stab-001", "a" * 64, replay_match_count=0,
        replay_failure_count=0, authority=auth, stabilization_window=3
    )
    assert pkt.stabilization_state == "unstable"
    assert pkt.status == "pending"


def test_stabilization_hash_is_deterministic(auth):
    p1 = build_stabilization_packet("s1", "a" * 64, 3, 0, auth, 3)
    p2 = build_stabilization_packet("s1", "a" * 64, 3, 0, auth, 3)
    assert p1.stabilization_hash() == p2.stabilization_hash()


def test_stabilization_hash_differs_on_different_counts(auth):
    p1 = build_stabilization_packet("s1", "a" * 64, 3, 0, auth, 3)
    p2 = build_stabilization_packet("s1", "a" * 64, 2, 1, auth, 3)
    assert p1.stabilization_hash() != p2.stabilization_hash()


def test_authority_must_be_locked():
    bad_auth = Authority(
        authority_id="bad", actor="x", locked=False, scope="sandbox_only"
    )
    with pytest.raises(ValueError, match="authority must be locked"):
        SandboxStabilizationPacket(
            stabilization_id="s",
            sandbox_branch_hash="a" * 64,
            replay_match_count=0,
            replay_failure_count=0,
            stabilization_window=3,
            stabilization_state="unstable",
            authority=bad_auth,
            status="pending",
        )


def test_negative_match_count_raises(auth):
    with pytest.raises(ValueError, match="replay_match_count"):
        SandboxStabilizationPacket(
            stabilization_id="s",
            sandbox_branch_hash="a" * 64,
            replay_match_count=-1,
            replay_failure_count=0,
            stabilization_window=3,
            stabilization_state="unstable",
            authority=auth,
            status="pending",
        )


def test_schema_version_correct(auth):
    pkt = build_stabilization_packet("s", "a" * 64, 0, 0, auth)
    assert pkt.schema_version == "SandboxStabilizationPacket.v1"


def test_compute_stabilization_state_stable():
    assert compute_stabilization_state(3, 0, 3) == "stable"
    assert compute_stabilization_state(10, 0, 3) == "stable"


def test_compute_stabilization_state_stabilizing():
    assert compute_stabilization_state(1, 0, 3) == "stabilizing"
    assert compute_stabilization_state(2, 0, 3) == "stabilizing"


def test_compute_stabilization_state_unstable_with_failures():
    assert compute_stabilization_state(2, 1, 3) == "unstable"


def test_compute_stabilization_state_failed():
    assert compute_stabilization_state(0, 3, 3) == "failed"


def test_replay_failures_affect_stability(auth):
    """Replay failures must push state away from stable."""
    stable = build_stabilization_packet("s", "a" * 64, 5, 0, auth, 3)
    unstable = build_stabilization_packet("s", "a" * 64, 5, 1, auth, 3)
    assert stable.stabilization_state == "stable"
    assert unstable.stabilization_state == "unstable"
