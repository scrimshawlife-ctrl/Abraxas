"""Tests for sandbox validators - core/sandbox/validators.py"""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.sandbox.models import build_sandbox_branch
from core.sandbox.replay import run_sandbox_replay
from core.sandbox.validators import (
    validate_adaptive_replay,
    sandbox_branch_gate,
    adaptive_replay_gate,
    adaptive_stabilization_gate,
    promotion_candidate_gate,
    mutation_receipt_gate,
    validate_sandbox_doctrine,
    SANDBOX_GATE_FUNCTIONS,
)
from core.validators.doctrine import GateStatus


@pytest.fixture
def auth() -> Authority:
    return Authority(
        authority_id="auth.validator.001",
        actor="system.validator",
        locked=True,
        scope="sandbox_only",
    )


def _make_valid_evidence(auth: Authority) -> dict:
    branch = build_sandbox_branch("b", "a" * 64, "scope", 0, auth)
    branch_dict = {
        "branch_id": branch.branch_id,
        "source_state_hash": branch.source_state_hash,
        "sandbox_state_hash": branch.sandbox_state_hash,
        "deterministic_branch_hash": branch.deterministic_branch_hash,
        "stabilization_state": "stable",
        "authority": {"locked": True, "authority_id": auth.authority_id},
    }
    replay_dict = {
        "deterministic_match": True,
        "mismatched_mutations": [],
        "status": "matched",
    }
    stab_dict = {
        "stabilization_state": "stable",
        "replay_match_count": 3,
        "replay_failure_count": 0,
    }
    candidate_dict = {
        "operator_review_required": True,
        "promotion_allowed": False,
        "status": "pending",
    }
    receipts = []
    return {
        "sandbox_branch": branch_dict,
        "sandbox_replay_packet": replay_dict,
        "sandbox_stabilization_packet": stab_dict,
        "promotion_candidate": candidate_dict,
        "mutation_receipts": receipts,
    }


# ── validate_adaptive_replay tests ────────────────────────────────────────

def test_adaptive_replay_valid_when_match(auth):
    from core.sandbox.models import AdaptiveSandboxBranch
    branch = AdaptiveSandboxBranch(
        branch_id="b",
        source_state_hash="a" * 64,
        sandbox_state_hash="b" * 64,
        branch_generation=0,
        sandbox_scope="scope",
        deterministic_branch_hash="c" * 64,
        authority=auth,
        stabilization_state="stable",
        status="active",
    )
    replay = run_sandbox_replay("c" * 64, "c" * 64, "rep", auth)
    result = validate_adaptive_replay(branch, replay)
    assert result["valid"] is True
    assert result["blocks_promotion"] is False


def test_adaptive_replay_invalid_on_mismatch(auth):
    branch = build_sandbox_branch("b", "a" * 64, "scope", 0, auth)
    replay = run_sandbox_replay("a" * 64, "b" * 64, "rep", auth)
    result = validate_adaptive_replay(branch, replay)
    assert result["valid"] is False
    assert result["blocks_promotion"] is True


def test_adaptive_replay_blocks_unstable_branch(auth):
    from core.sandbox.models import AdaptiveSandboxBranch
    branch = AdaptiveSandboxBranch(
        branch_id="b",
        source_state_hash="a" * 64,
        sandbox_state_hash="b" * 64,
        branch_generation=0,
        sandbox_scope="scope",
        deterministic_branch_hash="c" * 64,
        authority=auth,
        stabilization_state="unstable",
        status="active",
    )
    replay = run_sandbox_replay("c" * 64, "c" * 64, "rep", auth)
    result = validate_adaptive_replay(branch, replay)
    assert result["valid"] is False
    assert result["blocks_promotion"] is True


# ── Doctrine gate tests ────────────────────────────────────────────────────

def test_sandbox_branch_gate_passes_with_valid_evidence(auth):
    ev = _make_valid_evidence(auth)
    result = sandbox_branch_gate(ev)
    assert result.status == GateStatus.PASS


def test_sandbox_branch_gate_fails_when_no_branch(auth):
    ev = _make_valid_evidence(auth)
    ev["sandbox_branch"] = None
    result = sandbox_branch_gate(ev)
    assert result.status == GateStatus.FAIL


def test_sandbox_branch_gate_fails_authority_not_locked(auth):
    ev = _make_valid_evidence(auth)
    ev["sandbox_branch"]["authority"] = {"locked": False}
    result = sandbox_branch_gate(ev)
    assert result.status == GateStatus.FAIL
    assert "Authority leak" in result.reason or "not locked" in result.reason


def test_sandbox_branch_gate_fails_when_not_isolated(auth):
    ev = _make_valid_evidence(auth)
    same_hash = "f" * 64
    ev["sandbox_branch"]["source_state_hash"] = same_hash
    ev["sandbox_branch"]["sandbox_state_hash"] = same_hash
    result = sandbox_branch_gate(ev)
    assert result.status == GateStatus.FAIL


def test_adaptive_replay_gate_passes(auth):
    ev = _make_valid_evidence(auth)
    result = adaptive_replay_gate(ev)
    assert result.status == GateStatus.PASS


def test_adaptive_replay_gate_fails_when_no_packet(auth):
    ev = _make_valid_evidence(auth)
    ev["sandbox_replay_packet"] = None
    result = adaptive_replay_gate(ev)
    assert result.status == GateStatus.FAIL


def test_adaptive_replay_gate_fails_on_mismatch(auth):
    ev = _make_valid_evidence(auth)
    ev["sandbox_replay_packet"]["deterministic_match"] = False
    ev["sandbox_replay_packet"]["mismatched_mutations"] = ["m1"]
    result = adaptive_replay_gate(ev)
    assert result.status == GateStatus.FAIL


def test_adaptive_stabilization_gate_passes(auth):
    ev = _make_valid_evidence(auth)
    result = adaptive_stabilization_gate(ev)
    assert result.status == GateStatus.PASS


def test_adaptive_stabilization_gate_fails_unstable(auth):
    ev = _make_valid_evidence(auth)
    ev["sandbox_stabilization_packet"]["stabilization_state"] = "unstable"
    result = adaptive_stabilization_gate(ev)
    assert result.status == GateStatus.FAIL


def test_adaptive_stabilization_gate_fails_cyclic_lineage(auth):
    ev = _make_valid_evidence(auth)
    ev["sandbox_lineage"] = {"status": "cyclic"}
    result = adaptive_stabilization_gate(ev)
    assert result.status == GateStatus.FAIL


def test_promotion_candidate_gate_passes(auth):
    ev = _make_valid_evidence(auth)
    result = promotion_candidate_gate(ev)
    assert result.status == GateStatus.PASS


def test_promotion_candidate_gate_fails_when_no_review(auth):
    ev = _make_valid_evidence(auth)
    ev["promotion_candidate"]["operator_review_required"] = False
    result = promotion_candidate_gate(ev)
    assert result.status == GateStatus.FAIL


def test_promotion_candidate_gate_fails_when_allowed(auth):
    ev = _make_valid_evidence(auth)
    ev["promotion_candidate"]["promotion_allowed"] = True
    result = promotion_candidate_gate(ev)
    assert result.status == GateStatus.FAIL


def test_mutation_receipt_gate_passes_with_empty_receipts(auth):
    ev = _make_valid_evidence(auth)
    result = mutation_receipt_gate(ev)
    assert result.status == GateStatus.PASS


def test_mutation_receipt_gate_fails_with_unlocked_authority_receipt(auth):
    ev = _make_valid_evidence(auth)
    ev["mutation_receipts"] = [
        {"authority": {"locked": False}, "receipt_id": "r1"}
    ]
    result = mutation_receipt_gate(ev)
    assert result.status == GateStatus.FAIL


def test_mutation_receipt_gate_fails_when_none(auth):
    ev = _make_valid_evidence(auth)
    ev["mutation_receipts"] = None
    result = mutation_receipt_gate(ev)
    assert result.status == GateStatus.FAIL


def test_validate_sandbox_doctrine_fully_compliant(auth):
    ev = _make_valid_evidence(auth)
    result = validate_sandbox_doctrine("pipe-sandbox-001", ev)
    assert result["fully_compliant"] is True
    assert result["blocking_gates"] == []


def test_validate_sandbox_doctrine_noncompliant_on_replay_mismatch(auth):
    ev = _make_valid_evidence(auth)
    ev["sandbox_replay_packet"]["deterministic_match"] = False
    result = validate_sandbox_doctrine("pipe-sandbox-001", ev)
    assert result["fully_compliant"] is False
    assert "adaptive_replay_gate" in result["blocking_gates"]


def test_five_sandbox_gates_present(auth):
    ev = _make_valid_evidence(auth)
    result = validate_sandbox_doctrine("pipe", ev)
    gate_ids = {g["gate_id"] for g in result["gates"]}
    assert gate_ids == {
        "sandbox_branch_gate",
        "adaptive_replay_gate",
        "adaptive_stabilization_gate",
        "promotion_candidate_gate",
        "mutation_receipt_gate",
    }


def test_sandbox_doctrine_result_hash_deterministic(auth):
    ev = _make_valid_evidence(auth)
    r1 = validate_sandbox_doctrine("pipe", ev)
    r2 = validate_sandbox_doctrine("pipe", ev)
    assert r1["result_hash"] == r2["result_hash"]


def test_validator_catches_authority_leak(auth):
    """Authority leak (unlocked authority) must fail sandbox_branch_gate."""
    ev = _make_valid_evidence(auth)
    ev["sandbox_branch"]["authority"]["locked"] = False
    result = validate_sandbox_doctrine("pipe", ev)
    assert result["fully_compliant"] is False
    assert "sandbox_branch_gate" in result["blocking_gates"]


def test_projection_inference_authority_false():
    """Projection sandbox_summary must have inference_authority=False."""
    from core.viz.projection import build_sandbox_summary
    summary = build_sandbox_summary([], [], [], [], [])
    assert summary["inference_authority"] is False
    assert summary["projection_only"] is True
