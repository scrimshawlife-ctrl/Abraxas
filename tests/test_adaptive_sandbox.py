"""Tests for AdaptiveSandboxBranch.v1 - core/sandbox/models.py"""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.sandbox.models import (
    AdaptiveSandboxBranch,
    build_sandbox_branch,
    VALID_STABILIZATION_STATES,
    VALID_STATUSES,
)


@pytest.fixture
def locked_authority() -> Authority:
    return Authority(
        authority_id="auth.test.001",
        actor="system.test",
        locked=True,
        scope="sandbox_only",
    )


@pytest.fixture
def unlocked_authority() -> Authority:
    return Authority(
        authority_id="auth.test.bad",
        actor="system.test",
        locked=False,
        scope="sandbox_only",
    )


def test_build_sandbox_branch_returns_valid_branch(locked_authority):
    branch = build_sandbox_branch(
        branch_id="branch-001",
        source_state_hash="a" * 64,
        sandbox_scope="test_scope",
        branch_generation=0,
        authority=locked_authority,
    )
    assert branch.schema_version == "AdaptiveSandboxBranch.v1"
    assert branch.branch_id == "branch-001"
    assert branch.branch_generation == 0
    assert branch.status == "active"


def test_sandbox_branch_hash_is_deterministic(locked_authority):
    b1 = build_sandbox_branch("b1", "a" * 64, "scope", 0, locked_authority)
    b2 = build_sandbox_branch("b1", "a" * 64, "scope", 0, locked_authority)
    assert b1.deterministic_branch_hash == b2.deterministic_branch_hash


def test_sandbox_branch_hash_differs_for_different_inputs(locked_authority):
    b1 = build_sandbox_branch("b1", "a" * 64, "scope", 0, locked_authority)
    b2 = build_sandbox_branch("b2", "b" * 64, "scope", 1, locked_authority)
    assert b1.deterministic_branch_hash != b2.deterministic_branch_hash


def test_sandbox_branch_isolated_from_source(locked_authority):
    """Sandbox state hash must differ from source state hash."""
    source = "c" * 64
    branch = build_sandbox_branch("b", source, "scope", 0, locked_authority)
    assert branch.sandbox_state_hash != source


def test_sandbox_branch_authority_locked_required(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        AdaptiveSandboxBranch(
            branch_id="b",
            source_state_hash="a" * 64,
            sandbox_state_hash="b" * 64,
            branch_generation=0,
            sandbox_scope="s",
            deterministic_branch_hash="c" * 64,
            authority=unlocked_authority,
            stabilization_state="unstable",
            status="active",
        )


def test_sandbox_branch_generation_monotonic(locked_authority):
    with pytest.raises(ValueError, match="branch_generation"):
        AdaptiveSandboxBranch(
            branch_id="b",
            source_state_hash="a" * 64,
            sandbox_state_hash="b" * 64,
            branch_generation=-1,
            sandbox_scope="s",
            deterministic_branch_hash="c" * 64,
            authority=locked_authority,
            stabilization_state="unstable",
            status="active",
        )


def test_sandbox_branch_invalid_stabilization_state(locked_authority):
    with pytest.raises(ValueError, match="stabilization_state"):
        AdaptiveSandboxBranch(
            branch_id="b",
            source_state_hash="a" * 64,
            sandbox_state_hash="b" * 64,
            branch_generation=0,
            sandbox_scope="s",
            deterministic_branch_hash="c" * 64,
            authority=locked_authority,
            stabilization_state="invalid_state",
            status="active",
        )


def test_sandbox_branch_invalid_status(locked_authority):
    with pytest.raises(ValueError, match="status"):
        AdaptiveSandboxBranch(
            branch_id="b",
            source_state_hash="a" * 64,
            sandbox_state_hash="b" * 64,
            branch_generation=0,
            sandbox_scope="s",
            deterministic_branch_hash="c" * 64,
            authority=locked_authority,
            stabilization_state="unstable",
            status="bad_status",
        )


def test_sandbox_branch_all_valid_stabilization_states(locked_authority):
    for state in VALID_STABILIZATION_STATES:
        branch = AdaptiveSandboxBranch(
            branch_id="b",
            source_state_hash="a" * 64,
            sandbox_state_hash="b" * 64,
            branch_generation=0,
            sandbox_scope="s",
            deterministic_branch_hash="c" * 64,
            authority=locked_authority,
            stabilization_state=state,
            status="active",
        )
        assert branch.stabilization_state == state


def test_sandbox_branch_all_valid_statuses(locked_authority):
    for status in VALID_STATUSES:
        branch = AdaptiveSandboxBranch(
            branch_id="b",
            source_state_hash="a" * 64,
            sandbox_state_hash="b" * 64,
            branch_generation=0,
            sandbox_scope="s",
            deterministic_branch_hash="c" * 64,
            authority=locked_authority,
            stabilization_state="unstable",
            status=status,
        )
        assert branch.status == status


def test_compute_branch_hash_matches_build(locked_authority):
    branch = build_sandbox_branch("b", "a" * 64, "scope", 0, locked_authority)
    computed = branch.compute_branch_hash()
    assert computed == branch.deterministic_branch_hash


def test_sandbox_isolated_from_runtime_state(locked_authority):
    """Sandbox must not share state hash with runtime source."""
    source = "d" * 64
    b1 = build_sandbox_branch("x", source, "scope_a", 0, locked_authority)
    b2 = build_sandbox_branch("x", source, "scope_b", 0, locked_authority)
    assert b1.sandbox_state_hash != source
    assert b2.sandbox_state_hash != source
    # Different scopes produce different sandbox state hashes
    assert b1.sandbox_state_hash != b2.sandbox_state_hash
