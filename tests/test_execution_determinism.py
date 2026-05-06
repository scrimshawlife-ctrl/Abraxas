"""Tests for determinism of rune execution layer."""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.execution.context import RuneExecutionContext
from core.runes.execution import execute_rune
from core.runes.receipts import RuneInvocationReceipt, build_receipt_chain
from core.runes.runtime import RuneInvocationPlan, RuneInvocationStep, build_invocation_plan
from core.execution.shadow_runner import run_shadow_execution

LOCKED_AUTHORITY = Authority(
    authority_id="auth.det.001",
    actor="test.determinism",
    locked=True,
    scope="shadow_only",
)

RUNE_CATALOG = {
    "RUNE_AUDIT": {"input_schema": {}, "output_schema": {}},
    "RUNE_HASH": {"input_schema": {}, "output_schema": {}},
}

ROUTE_GRAPH = {
    "graph_hash": "e" * 64,
    "RUNE_AUDIT": {"node": "node.audit", "edges": []},
    "RUNE_HASH": {"node": "node.hash", "edges": []},
}

CONTRACT = {
    "pipeline_id": "det-test-001",
    "lane": "shadow",
    "required_runes": ["RUNE_AUDIT", "RUNE_HASH"],
    "authority": LOCKED_AUTHORITY,
    "metadata": {},
}


def test_invocation_plan_deterministic_ordering():
    plan = build_invocation_plan(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    orders = [s.deterministic_order for s in plan.steps]
    assert orders == sorted(orders)


def test_invocation_plan_hash_deterministic():
    plan1 = build_invocation_plan(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    plan2 = build_invocation_plan(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert plan1.invocation_plan_hash() == plan2.invocation_plan_hash()


def test_unknown_rune_fails_closed():
    bad_contract = dict(CONTRACT, required_runes=["UNKNOWN_RUNE_XYZ"])
    with pytest.raises((ValueError, Exception)):
        build_invocation_plan(bad_contract, ROUTE_GRAPH, RUNE_CATALOG)


def test_execution_context_hash_stable():
    ctx = RuneExecutionContext(
        execution_id="exec-stable",
        pipeline_id="pipe-001",
        lane="shadow",
        invoked_runes=["RUNE_AUDIT"],
        route_graph_hash="f" * 64,
        authority=LOCKED_AUTHORITY,
    )
    h1 = ctx.execution_context_hash()
    h2 = ctx.execution_context_hash()
    assert h1 == h2


def test_deterministic_receipt_hashing():
    step = {"step_id": "s001", "route_node": "node.audit"}
    ctx = RuneExecutionContext(
        execution_id="exec-rcpt",
        pipeline_id="pipe-001",
        lane="shadow",
        invoked_runes=["RUNE_AUDIT"],
        route_graph_hash="g" * 64,
        authority=LOCKED_AUTHORITY,
    )
    r1 = execute_rune("RUNE_AUDIT", {"val": "test"}, ctx, step)
    r2 = execute_rune("RUNE_AUDIT", {"val": "test"}, ctx, step)
    assert r1["execution_hash"] == r2["execution_hash"]


def test_shadow_execution_deterministic_plan():
    run1 = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    run2 = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert run1.invocation_plan_hash == run2.invocation_plan_hash


def test_shadow_execution_deterministic_receipt_chain():
    run1 = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    run2 = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert run1.receipt_chain_hash == run2.receipt_chain_hash
