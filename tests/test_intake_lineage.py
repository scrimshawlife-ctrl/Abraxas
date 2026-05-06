"""Tests for IntakeLineagePacket.v1 - core/oracle/lineage.py"""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.lineage import (
    IntakeLineageNode,
    IntakeLineagePacket,
    build_intake_lineage,
    detect_lineage_cycles,
    validate_lineage_parent_references,
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


def _node(intake_hash: str, parent: str | None = None, gen: int = 0) -> IntakeLineageNode:
    return IntakeLineageNode(
        intake_hash=intake_hash,
        parent_hash=parent,
        generation=gen,
    )


def test_build_intake_lineage_valid(locked_authority):
    nodes = [
        _node("hash_a", None, 0),
        _node("hash_b", "hash_a", 1),
        _node("hash_c", "hash_b", 2),
    ]
    lineage = build_intake_lineage("lineage-001", nodes, locked_authority)
    assert lineage.schema_version == "IntakeLineagePacket.v1"
    assert lineage.status == "valid"
    assert lineage.lineage_depth == 3
    assert len(lineage.deterministic_lineage_hash) == 64


def test_cyclic_lineage_fails_closed(locked_authority):
    """Cyclic lineage must fail closed."""
    nodes = [
        _node("hash_a", "hash_b", 0),
        _node("hash_b", "hash_a", 1),  # Cycle: a -> b -> a
    ]
    lineage = build_intake_lineage("lineage-cyc", nodes, locked_authority)
    assert lineage.status == "cyclic"


def test_invalid_parent_reference_fails(locked_authority):
    """Invalid parent references must result in invalid status."""
    nodes = [
        _node("hash_a", "nonexistent_hash", 0),
    ]
    lineage = build_intake_lineage("lineage-inv", nodes, locked_authority)
    assert lineage.status == "invalid"


def test_lineage_hash_is_deterministic(locked_authority):
    nodes = [_node("hash_a", None, 0), _node("hash_b", "hash_a", 1)]
    lin1 = build_intake_lineage("lin1", nodes, locked_authority)
    lin2 = build_intake_lineage("lin1", nodes, locked_authority)
    assert lin1.deterministic_lineage_hash == lin2.deterministic_lineage_hash


def test_lineage_requires_locked_authority(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        build_intake_lineage("lin1", [_node("h1", None, 0)], unlocked_authority)


def test_lineage_node_rejects_negative_generation():
    with pytest.raises(ValueError, match="generation"):
        IntakeLineageNode(intake_hash="h1", parent_hash=None, generation=-1)


def test_detect_lineage_cycles_simple():
    nodes = [
        _node("hash_a", "hash_b", 0),
        _node("hash_b", "hash_a", 1),
    ]
    assert detect_lineage_cycles(nodes) is True


def test_detect_lineage_cycles_no_cycle():
    nodes = [
        _node("hash_a", None, 0),
        _node("hash_b", "hash_a", 1),
        _node("hash_c", "hash_b", 2),
    ]
    assert detect_lineage_cycles(nodes) is False


def test_validate_parent_references_valid():
    nodes = [_node("a", None, 0), _node("b", "a", 1)]
    assert validate_lineage_parent_references(nodes) is True


def test_validate_parent_references_invalid():
    nodes = [_node("a", "missing", 0)]
    assert validate_lineage_parent_references(nodes) is False


def test_empty_lineage_valid(locked_authority):
    lineage = build_intake_lineage("lin-empty", [], locked_authority)
    assert lineage.status == "valid"
    assert lineage.lineage_depth == 0


def test_lineage_packet_rejects_invalid_status(locked_authority):
    with pytest.raises(ValueError, match="status"):
        IntakeLineagePacket(
            lineage_id="lin1",
            lineage_depth=0,
            lineage_nodes=[],
            deterministic_lineage_hash="a" * 64,
            authority=locked_authority,
            status="unknown_status",
        )


def test_lineage_with_normalization_hash(locked_authority):
    node = IntakeLineageNode(
        intake_hash="hash_a",
        parent_hash=None,
        generation=0,
        normalization_hash="norm_" + "x" * 60,
    )
    lineage = build_intake_lineage("lin-norm", [node], locked_authority)
    assert lineage.status == "valid"
    assert lineage.lineage_nodes[0].normalization_hash is not None
