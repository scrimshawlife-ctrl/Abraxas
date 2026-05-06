"""Tests for RuneExecutionContext and execute_rune."""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.execution.context import RuneExecutionContext
from core.runes.execution import execute_rune

LOCKED_AUTHORITY = Authority(
    authority_id="auth.test.001",
    actor="test.actor",
    locked=True,
    scope="shadow_only",
)

UNLOCKED_AUTHORITY = Authority(
    authority_id="auth.test.002",
    actor="test.actor",
    locked=False,
    scope="shadow_only",
)


def make_context(**overrides):
    defaults = dict(
        execution_id="exec-001",
        pipeline_id="pipe-001",
        lane="shadow",
        invoked_runes=["RUNE_AUDIT"],
        route_graph_hash="a" * 64,
        authority=LOCKED_AUTHORITY,
    )
    defaults.update(overrides)
    return RuneExecutionContext(**defaults)


def test_context_creation_succeeds():
    ctx = make_context()
    assert ctx.schema_version == "RuneExecutionContext.v1"
    assert ctx.execution_mode == "shadow_only"


def test_context_authority_must_be_locked():
    with pytest.raises((ValueError, Exception)):
        make_context(authority=UNLOCKED_AUTHORITY)


def test_context_execution_mode_shadow_only():
    ctx = make_context()
    assert ctx.execution_mode == "shadow_only"


def test_context_invoked_runes_cannot_be_empty():
    with pytest.raises((ValueError, Exception)):
        make_context(invoked_runes=[])


def test_context_hash_deterministic():
    ctx1 = make_context(execution_id="exec-det-001")
    ctx2 = make_context(execution_id="exec-det-001")
    assert ctx1.execution_context_hash() == ctx2.execution_context_hash()


def test_context_hash_changes_with_different_inputs():
    ctx1 = make_context(execution_id="exec-a")
    ctx2 = make_context(execution_id="exec-b")
    assert ctx1.execution_context_hash() != ctx2.execution_context_hash()


def test_execute_rune_returns_correct_fields():
    ctx = make_context()
    step = {"step_id": "step-001", "route_node": "node.audit"}
    result = execute_rune("RUNE_AUDIT", {"data": "test"}, ctx, step)
    assert "rune_id" in result
    assert "payload_hash" in result
    assert "execution_hash" in result
    assert "status" in result


def test_execute_rune_status_is_completed():
    ctx = make_context()
    step = {"step_id": "step-001", "route_node": "node.audit"}
    result = execute_rune("RUNE_AUDIT", {}, ctx, step)
    assert result["status"] == "completed"


def test_execute_rune_payload_hash_deterministic():
    ctx = make_context(execution_id="exec-det")
    step = {"step_id": "step-001", "route_node": "node.audit"}
    r1 = execute_rune("RUNE_AUDIT", {"x": 1}, ctx, step)
    r2 = execute_rune("RUNE_AUDIT", {"x": 1}, ctx, step)
    assert r1["payload_hash"] == r2["payload_hash"]


def test_execute_rune_execution_hash_deterministic():
    ctx = make_context(execution_id="exec-det")
    step = {"step_id": "step-001", "route_node": "node.audit"}
    r1 = execute_rune("RUNE_AUDIT", {"x": 1}, ctx, step)
    r2 = execute_rune("RUNE_AUDIT", {"x": 1}, ctx, step)
    assert r1["execution_hash"] == r2["execution_hash"]


def test_execute_rune_different_payload_different_hash():
    ctx = make_context()
    step = {"step_id": "step-001", "route_node": "node.audit"}
    r1 = execute_rune("RUNE_AUDIT", {"x": 1}, ctx, step)
    r2 = execute_rune("RUNE_AUDIT", {"x": 2}, ctx, step)
    assert r1["payload_hash"] != r2["payload_hash"]


def test_execute_rune_no_mutation_authority():
    """Execution must not produce mutation authority."""
    ctx = make_context()
    step = {"step_id": "step-001", "route_node": "node.audit"}
    result = execute_rune("RUNE_AUDIT", {}, ctx, step)
    assert "mutation_authority" not in result
    assert "canon_mutation" not in result
    assert "forecast_activation" not in result
