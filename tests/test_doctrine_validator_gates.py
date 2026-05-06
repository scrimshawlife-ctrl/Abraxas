"""Tests for doctrine validator gates."""
from __future__ import annotations
import pytest
from core.validators.doctrine import (
    validate_pipeline_doctrine,
    doctrine_result_to_dict,
    GateStatus,
)


_SENTINEL = object()


def _full_evidence(
    *,
    invocation_plan=_SENTINEL,
    receipt_chain=_SENTINEL,
    replay_packet=_SENTINEL,
    rollback_packet=_SENTINEL,
):
    """Helper to build a passing evidence dict. Pass the sentinel to use defaults."""
    default_plan = {
        "schema_version": "RuneInvocationPlan.v1",
        "plan_id": "plan-001",
        "pipeline_id": "pipe-001",
        "steps": [
            {
                "step_id": "s-001",
                "rune_id": "RUNE_AUDIT",
                "route_node": "node.audit",
                "deterministic_order": 0,
                "input_schema": {},
                "output_schema": {},
                "required_receipts": [],
            }
        ],
    }
    default_chain = {
        "chain_hash": "a" * 64,
        "receipt_count": 1,
    }
    default_replay = {
        "schema_version": "RuneReplayPacket.v1",
        "replay_id": "rep-001",
        "deterministic_match": True,
        "mismatched_receipts": [],
        "status": "matched",
    }
    default_rollback = {
        "schema_version": "ExecutionRollbackPacket.v1",
        "rollback_id": "roll-001",
        "rollback_possible": True,
        "rollback_reason": "test",
    }
    return {
        "invocation_plan": default_plan if invocation_plan is _SENTINEL else invocation_plan,
        "receipt_chain": default_chain if receipt_chain is _SENTINEL else receipt_chain,
        "replay_packet": default_replay if replay_packet is _SENTINEL else replay_packet,
        "rollback_packet": default_rollback if rollback_packet is _SENTINEL else rollback_packet,
    }


def test_fully_compliant_with_all_evidence():
    result = validate_pipeline_doctrine("pipe-001", _full_evidence())
    assert result.fully_compliant is True
    assert result.blocking_gates == []


def test_execution_plan_gate_fails_when_no_plan():
    ev = _full_evidence(invocation_plan=None)
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert not result.fully_compliant
    assert "execution_plan_gate" in result.blocking_gates


def test_execution_plan_gate_fails_when_empty_steps():
    ev = _full_evidence(invocation_plan={"plan_id": "p", "pipeline_id": "x", "steps": []})
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "execution_plan_gate" in result.blocking_gates


def test_execution_plan_gate_fails_duplicate_orders():
    plan = {
        "plan_id": "p",
        "pipeline_id": "x",
        "steps": [
            {"step_id": "s1", "rune_id": "A", "route_node": "n", "deterministic_order": 0, "input_schema": {}, "output_schema": {}, "required_receipts": []},
            {"step_id": "s2", "rune_id": "B", "route_node": "n", "deterministic_order": 0, "input_schema": {}, "output_schema": {}, "required_receipts": []},
        ],
    }
    ev = _full_evidence(invocation_plan=plan)
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "execution_plan_gate" in result.blocking_gates


def test_execution_receipt_gate_fails_when_no_chain():
    ev = _full_evidence(receipt_chain=None)
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "execution_receipt_gate" in result.blocking_gates


def test_execution_receipt_gate_fails_invalid_hash():
    ev = _full_evidence(receipt_chain={"chain_hash": "short", "receipt_count": 1})
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "execution_receipt_gate" in result.blocking_gates


def test_execution_receipt_gate_fails_zero_receipts():
    ev = _full_evidence(receipt_chain={"chain_hash": "a" * 64, "receipt_count": 0})
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "execution_receipt_gate" in result.blocking_gates


def test_replayability_gate_fails_when_no_packet():
    ev = _full_evidence(replay_packet=None)
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "replayability_gate" in result.blocking_gates


def test_replayability_gate_fails_when_not_deterministic():
    replay = {
        "deterministic_match": False,
        "mismatched_receipts": ["rcpt-001"],
        "status": "mismatch",
    }
    ev = _full_evidence(replay_packet=replay)
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "replayability_gate" in result.blocking_gates


def test_rollback_gate_fails_when_no_packet():
    ev = _full_evidence(rollback_packet=None)
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "rollback_gate" in result.blocking_gates


def test_rollback_gate_fails_missing_rollback_id():
    rollback = {"rollback_id": "", "rollback_possible": True, "rollback_reason": "test"}
    ev = _full_evidence(rollback_packet=rollback)
    result = validate_pipeline_doctrine("pipe-001", ev)
    assert "rollback_gate" in result.blocking_gates


def test_result_hash_deterministic():
    ev = _full_evidence()
    r1 = validate_pipeline_doctrine("pipe-001", ev)
    r2 = validate_pipeline_doctrine("pipe-001", ev)
    assert r1.result_hash == r2.result_hash


def test_doctrine_result_to_dict_shape():
    result = validate_pipeline_doctrine("pipe-001", _full_evidence())
    d = doctrine_result_to_dict(result)
    assert d["schema_version"] == "DoctrineValidationResult.v1"
    assert "gates" in d
    # v2.0.6 adds 6 oracle intake gates: 4 original + 6 new = 10
    assert len(d["gates"]) == 10
    assert all("gate_id" in g and "status" in g and "reason" in g for g in d["gates"])


def test_all_core_gates_present():
    result = validate_pipeline_doctrine("pipe-001", _full_evidence())
    gate_ids = {g.gate_id for g in result.gates}
    # Original 4 gates must still be present
    assert {"execution_plan_gate", "execution_receipt_gate", "replayability_gate", "rollback_gate"}.issubset(gate_ids)
    # v2.0.6 oracle intake gates must also be present
    assert {"intake_envelope_gate", "intake_replay_gate", "intake_conflict_gate",
            "intake_lineage_gate", "intake_stabilization_gate", "intake_approval_gate"}.issubset(gate_ids)
