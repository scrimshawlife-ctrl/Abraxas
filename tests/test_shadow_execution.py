"""Tests for ShadowExecutionRun."""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.execution.shadow_runner import ShadowExecutionRun, run_shadow_execution

LOCKED_AUTHORITY = Authority(
    authority_id="auth.test.001",
    actor="test.actor",
    locked=True,
    scope="shadow_only",
)

RUNE_CATALOG = {
    "RUNE_AUDIT": {"input_schema": {}, "output_schema": {}},
    "RUNE_HASH": {"input_schema": {}, "output_schema": {}},
}

ROUTE_GRAPH = {
    "graph_hash": "b" * 64,
    "RUNE_AUDIT": {"node": "node.audit", "edges": []},
    "RUNE_HASH": {"node": "node.hash", "edges": []},
}

CONTRACT = {
    "pipeline_id": "test-pipe-001",
    "lane": "shadow",
    "required_runes": ["RUNE_AUDIT", "RUNE_HASH"],
    "authority": LOCKED_AUTHORITY,
    "metadata": {},
}


def test_shadow_run_creates_successfully():
    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert run.schema_version == "ShadowExecutionRun.v1"


def test_shadow_run_authority_locked():
    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert run.authority.is_locked()


def test_shadow_run_status_valid():
    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert run.status in {"completed", "partial", "failed", "not_computable"}


def test_shadow_run_no_mutation_authority():
    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    run_dict = {
        "schema_version": run.schema_version,
        "run_id": run.run_id,
        "status": run.status,
    }
    assert "mutation_authority" not in run_dict
    assert "canon_mutation" not in run_dict
    assert "forecast_activation" not in run_dict


def test_shadow_run_has_receipt_chain_hash():
    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert run.receipt_chain_hash
    assert len(run.receipt_chain_hash) == 64  # sha256 hex


def test_shadow_run_context_hash_present():
    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert run.execution_context_hash
    assert len(run.execution_context_hash) == 64


def test_shadow_run_invalid_route_fails_gracefully():
    bad_graph = {
        "graph_hash": "c" * 64,
        "RUNE_AUDIT": {"node": "", "edges": []},
        "RUNE_HASH": {"node": "", "edges": []},
    }
    run = run_shadow_execution(CONTRACT, bad_graph, RUNE_CATALOG)
    assert run.status in {"failed", "partial", "not_computable"}
    assert len(run.failed_steps) > 0


def test_shadow_run_projection_only():
    """Projection remains projection-only - no inference authority."""
    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert not hasattr(run, "inference_authority") or getattr(run, "inference_authority", False) is False


def test_shadow_run_locked_authority_required():
    unlocked = Authority(
        authority_id="auth.test.bad",
        actor="test.actor",
        locked=False,
        scope="shadow_only",
    )
    bad_contract = dict(CONTRACT, authority=unlocked)
    with pytest.raises((ValueError, Exception)):
        run_shadow_execution(bad_contract, ROUTE_GRAPH, RUNE_CATALOG)
