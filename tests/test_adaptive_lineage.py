"""Tests for AdaptiveBranchLineage.v1 - core/sandbox/lineage.py"""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.sandbox.lineage import (
    AdaptiveBranchNode,
    AdaptiveBranchLineage,
    build_branch_lineage,
    detect_cycles,
    validate_parent_references,
)


@pytest.fixture
def auth() -> Authority:
    return Authority(
        authority_id="auth.lineage.001",
        actor="system.lineage",
        locked=True,
        scope="sandbox_only",
    )


def _make_node(branch_hash: str, parent: str | None = None, gen: int = 0) -> AdaptiveBranchNode:
    return AdaptiveBranchNode(
        branch_hash=branch_hash,
        parent_branch_hash=parent,
        generation=gen,
    )


def test_build_valid_lineage(auth):
    nodes = [
        _make_node("hash_a", parent=None, gen=0),
        _make_node("hash_b", parent="hash_a", gen=1),
        _make_node("hash_c", parent="hash_b", gen=2),
    ]
    lineage = build_branch_lineage("lin-001", nodes, auth)
    assert lineage.status == "valid"
    assert lineage.lineage_depth == 3


def test_lineage_hash_is_deterministic(auth):
    nodes = [_make_node("h1", None, 0), _make_node("h2", "h1", 1)]
    l1 = build_branch_lineage("lin", nodes, auth)
    l2 = build_branch_lineage("lin", nodes, auth)
    assert l1.deterministic_lineage_hash == l2.deterministic_lineage_hash


def test_cyclic_lineage_fails_closed(auth):
    """Cyclic lineage must fail closed."""
    nodes = [
        _make_node("hash_a", parent="hash_c", gen=0),  # A -> C (cycle)
        _make_node("hash_b", parent="hash_a", gen=1),
        _make_node("hash_c", parent="hash_b", gen=2),  # C -> B -> A -> C
    ]
    lineage = build_branch_lineage("lin-cycle", nodes, auth)
    assert lineage.status == "cyclic"


def test_invalid_parent_reference_fails(auth):
    """Invalid parent references must produce 'invalid' status."""
    nodes = [
        _make_node("hash_a", parent="non_existent_hash", gen=0),
    ]
    lineage = build_branch_lineage("lin-invalid", nodes, auth)
    assert lineage.status == "invalid"


def test_detect_cycles_true_for_cycle():
    nodes = [
        _make_node("a", "c", 0),
        _make_node("b", "a", 1),
        _make_node("c", "b", 2),
    ]
    assert detect_cycles(nodes) is True


def test_detect_cycles_false_for_no_cycle():
    nodes = [
        _make_node("a", None, 0),
        _make_node("b", "a", 1),
        _make_node("c", "b", 2),
    ]
    assert detect_cycles(nodes) is False


def test_validate_parent_references_true_when_all_exist():
    nodes = [
        _make_node("a", None, 0),
        _make_node("b", "a", 1),
    ]
    assert validate_parent_references(nodes) is True


def test_validate_parent_references_false_when_missing():
    nodes = [_make_node("a", "missing_parent", 0)]
    assert validate_parent_references(nodes) is False


def test_authority_must_be_locked():
    bad_auth = Authority(
        authority_id="bad", actor="x", locked=False, scope="sandbox_only"
    )
    with pytest.raises(ValueError, match="authority must be locked"):
        build_branch_lineage("lin", [], bad_auth)


def test_branch_node_negative_generation_raises():
    with pytest.raises(ValueError, match="generation"):
        AdaptiveBranchNode(
            branch_hash="h1",
            parent_branch_hash=None,
            generation=-1,
        )


def test_lineage_depth_matches_node_count(auth):
    nodes = [_make_node(f"hash_{i}", f"hash_{i-1}" if i > 0 else None, i) for i in range(5)]
    lineage = build_branch_lineage("lin", nodes, auth)
    assert lineage.lineage_depth == 5


def test_schema_version_correct(auth):
    lineage = build_branch_lineage("lin", [_make_node("h", None, 0)], auth)
    assert lineage.schema_version == "AdaptiveBranchLineage.v1"


def test_single_root_node_valid(auth):
    nodes = [_make_node("root", None, 0)]
    lineage = build_branch_lineage("lin", nodes, auth)
    assert lineage.status == "valid"


def test_lineage_hash_differs_for_different_nodes(auth):
    n1 = [_make_node("a", None, 0)]
    n2 = [_make_node("b", None, 0)]
    l1 = build_branch_lineage("lin", n1, auth)
    l2 = build_branch_lineage("lin", n2, auth)
    assert l1.deterministic_lineage_hash != l2.deterministic_lineage_hash
