"""Tests for CandidateMutationPacket.v1 - core/sandbox/mutations.py"""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.sandbox.mutations import (
    CandidateMutationPacket,
    build_mutation_packet,
    ALLOWED_MUTATION_TYPES,
)


@pytest.fixture
def auth() -> Authority:
    return Authority(
        authority_id="auth.mutation.001",
        actor="system.mutation",
        locked=True,
        scope="sandbox_only",
    )


def test_build_mutation_packet_returns_valid_packet(auth):
    pkt = build_mutation_packet(
        mutation_id="mut-001",
        source_branch_hash="a" * 64,
        target_branch_hash="b" * 64,
        mutation_type="route_adjustment",
        proposed_transition_hashes=["t1", "t2"],
        authority=auth,
    )
    assert pkt.schema_version == "CandidateMutationPacket.v1"
    assert pkt.mutation_id == "mut-001"
    assert pkt.status == "proposed"
    assert pkt.requires_operator_review is True


def test_mutation_hash_is_deterministic(auth):
    p1 = build_mutation_packet(
        "mut-001", "a" * 64, "b" * 64, "route_adjustment", ["t1"], auth
    )
    p2 = build_mutation_packet(
        "mut-001", "a" * 64, "b" * 64, "route_adjustment", ["t1"], auth
    )
    assert p1.deterministic_mutation_hash == p2.deterministic_mutation_hash


def test_mutation_hash_differs_for_different_inputs(auth):
    p1 = build_mutation_packet(
        "mut-001", "a" * 64, "b" * 64, "route_adjustment", ["t1"], auth
    )
    p2 = build_mutation_packet(
        "mut-002", "c" * 64, "d" * 64, "validation_adjustment", ["t2"], auth
    )
    assert p1.deterministic_mutation_hash != p2.deterministic_mutation_hash


def test_all_allowed_mutation_types(auth):
    for mt in ALLOWED_MUTATION_TYPES:
        pkt = build_mutation_packet(
            mutation_id="m",
            source_branch_hash="a" * 64,
            target_branch_hash="b" * 64,
            mutation_type=mt,
            proposed_transition_hashes=[],
            authority=auth,
        )
        assert pkt.mutation_type == mt


def test_invalid_mutation_type_raises(auth):
    with pytest.raises(ValueError, match="mutation_type"):
        build_mutation_packet(
            mutation_id="m",
            source_branch_hash="a" * 64,
            target_branch_hash="b" * 64,
            mutation_type="live_execution",
            proposed_transition_hashes=[],
            authority=auth,
        )


def test_authority_must_be_locked():
    bad_auth = Authority(
        authority_id="bad",
        actor="x",
        locked=False,
        scope="sandbox_only",
    )
    with pytest.raises(ValueError, match="authority must be locked"):
        CandidateMutationPacket(
            mutation_id="m",
            source_branch_hash="a" * 64,
            target_branch_hash="b" * 64,
            mutation_type="route_adjustment",
            proposed_transition_hashes=[],
            deterministic_mutation_hash="c" * 64,
            authority=bad_auth,
            requires_operator_review=True,
            status="proposed",
        )


def test_mutation_isolated_to_sandbox_does_not_mutate_source(auth):
    """Mutation packet does not modify source_branch_hash."""
    source = "e" * 64
    pkt = build_mutation_packet(
        "m", source, "f" * 64, "topology_adjustment", [], auth
    )
    assert pkt.source_branch_hash == source
    # The target is different
    assert pkt.target_branch_hash != pkt.source_branch_hash


def test_compute_mutation_hash_matches_build(auth):
    pkt = build_mutation_packet(
        "mut-001", "a" * 64, "b" * 64, "replay_adjustment", ["t1", "t2"], auth
    )
    computed = pkt.compute_mutation_hash()
    assert computed == pkt.deterministic_mutation_hash


def test_transition_hashes_sorted_deterministically(auth):
    p1 = build_mutation_packet(
        "m", "a" * 64, "b" * 64, "route_adjustment", ["z", "a", "m"], auth
    )
    p2 = build_mutation_packet(
        "m", "a" * 64, "b" * 64, "route_adjustment", ["a", "m", "z"], auth
    )
    assert p1.deterministic_mutation_hash == p2.deterministic_mutation_hash
    assert p1.proposed_transition_hashes == ["a", "m", "z"]


def test_invalid_status_raises(auth):
    with pytest.raises(ValueError, match="status"):
        CandidateMutationPacket(
            mutation_id="m",
            source_branch_hash="a" * 64,
            target_branch_hash="b" * 64,
            mutation_type="route_adjustment",
            proposed_transition_hashes=[],
            deterministic_mutation_hash="c" * 64,
            authority=auth,
            requires_operator_review=True,
            status="bad_status",
        )
