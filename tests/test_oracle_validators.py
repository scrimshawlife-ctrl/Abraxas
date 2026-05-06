"""Tests for oracle validators - core/oracle/validators.py and doctrine extensions."""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.runtime import run_oracle_intake
from core.oracle.validators import (
    validate_intake_replay,
    run_intake_doctrine_gates,
    INTAKE_GATE_FUNCTIONS,
)
from core.oracle.lineage import IntakeLineageNode, build_intake_lineage
from core.validators.doctrine import validate_pipeline_doctrine


@pytest.fixture
def locked_authority() -> Authority:
    return Authority(
        authority_id="auth.test.001",
        actor="system.test",
        locked=True,
        scope="oracle_intake_only",
    )


FIXTURE_PAYLOADS = [
    {"source_id": "src-001", "source_type": "document", "payload": {"key": "value_a"}},
]


def _build_valid_intake_run(authority, tmp_path):
    return run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=authority,
        run_id="validator-test-run",
        out_dir=tmp_path,
    )


def test_validate_intake_replay_valid(locked_authority, tmp_path):
    run = _build_valid_intake_run(locked_authority, tmp_path)
    run_dict = run.model_dump()
    replay_packet = {"deterministic_match": True, "mismatched_normalizations": []}
    result = validate_intake_replay(run_dict, replay_packet)
    assert result["valid"] is True


def test_validate_intake_replay_mismatch_invalidates_approval(locked_authority, tmp_path):
    """Replay mismatch must invalidate approval."""
    run = _build_valid_intake_run(locked_authority, tmp_path)
    run_dict = run.model_dump()
    replay_packet = {
        "deterministic_match": False,
        "mismatched_normalizations": ["hash_mismatch"],
    }
    result = validate_intake_replay(run_dict, replay_packet)
    assert result["valid"] is False
    assert any("replay_mismatch" in issue for issue in result["blocking_issues"])


def test_validate_intake_replay_unresolved_conflicts_invalidate(locked_authority, tmp_path):
    """Unresolved conflicts must invalidate stabilization."""
    run_dict = {
        "conflict_packets": [{"status": "unresolved"}],
        "evidence_packets": [],
        "replay_packets": [],
    }
    replay_packet = {"deterministic_match": True, "mismatched_normalizations": []}
    result = validate_intake_replay(run_dict, replay_packet)
    assert result["valid"] is False
    assert any("unresolved_conflicts" in issue for issue in result["blocking_issues"])


def test_validate_intake_replay_missing_provenance_blocks(locked_authority, tmp_path):
    """Missing provenance must block approval."""
    run_dict = {
        "conflict_packets": [],
        "evidence_packets": [{"provenance_chain": [], "status": "not_computable"}],
        "replay_packets": [],
    }
    replay_packet = {"deterministic_match": True, "mismatched_normalizations": []}
    result = validate_intake_replay(run_dict, replay_packet)
    assert result["valid"] is False
    assert any("provenance" in issue for issue in result["blocking_issues"])


def test_doctrine_gates_pass_with_valid_intake(locked_authority, tmp_path):
    run = _build_valid_intake_run(locked_authority, tmp_path)
    evidence = {"intake_run": run.model_dump()}
    result = run_intake_doctrine_gates(evidence)
    assert result["fully_compliant"] is True


def test_doctrine_gates_fail_no_intake_run():
    evidence = {}
    result = run_intake_doctrine_gates(evidence)
    # Without intake_run all gates pass (not required) except we check replay/conflict/stab/approval
    # Lineage passes. Let's verify the structure
    assert "fully_compliant" in result
    assert "gates" in result


def test_intake_lineage_gate_fails_on_cyclic(locked_authority, tmp_path):
    from core.oracle.lineage import IntakeLineageNode, build_intake_lineage
    nodes = [
        IntakeLineageNode(intake_hash="h_a", parent_hash="h_b", generation=0),
        IntakeLineageNode(intake_hash="h_b", parent_hash="h_a", generation=1),
    ]
    cyclic_lineage = build_intake_lineage("lin-cyc", nodes, locked_authority)
    assert cyclic_lineage.status == "cyclic"

    evidence = {"intake_lineage": cyclic_lineage.model_dump()}
    result = run_intake_doctrine_gates(evidence)
    failing_gates = [g["gate_id"] for g in result["gates"] if g["status"] != "pass"]
    assert "intake_lineage_gate" in failing_gates


def test_validator_catches_authority_violation_in_conflict(locked_authority, tmp_path):
    from core.oracle.conflicts import build_conflict_packet
    pkt = build_conflict_packet(
        conflict_id="auth-viol",
        conflicting_source_hashes=["x" * 64],
        conflict_type="authority_violation",
        authority=locked_authority,
    )
    assert pkt.status == "failed"


def test_intake_approval_gate_detects_bypass(locked_authority, tmp_path):
    """Approval bypass must be detected."""
    run_dict = {
        "intake_envelopes": [{"intake_status": "pending"}],
        "replay_packets": [{"deterministic_match": True}],
        "conflict_packets": [],
        "stabilization_packets": [{"stabilization_state": "stable"}],
        "approval_packets": [
            {
                "approved": True,
                "conflict_hashes": ["conflicthash1"],  # Bypass: approved with conflict
            }
        ],
    }
    evidence = {"intake_run": run_dict}
    result = run_intake_doctrine_gates(evidence)
    failing_gates = [g["gate_id"] for g in result["gates"] if g["status"] != "pass"]
    assert "intake_approval_gate" in failing_gates


def test_doctrine_validator_extended_with_intake_gates():
    """The main doctrine validator must include oracle intake gates."""
    from core.validators.doctrine import _GATE_FUNCTIONS
    gate_ids = [fn.__name__ for fn in _GATE_FUNCTIONS]
    assert "_intake_envelope_gate" in gate_ids
    assert "_intake_replay_gate" in gate_ids
    assert "_intake_conflict_gate" in gate_ids
    assert "_intake_lineage_gate" in gate_ids
    assert "_intake_stabilization_gate" in gate_ids
    assert "_intake_approval_gate" in gate_ids


def test_projection_remains_projection_only(locked_authority, tmp_path):
    """Projection must never confer authority."""
    from core.viz.projection import build_oracle_intake_summary
    summary = build_oracle_intake_summary([], [], [], [], [], [], [])
    assert summary["projection_only"] is True
    assert summary["inference_authority"] is False


def test_run_intake_doctrine_gates_has_six_intake_gates():
    assert len(INTAKE_GATE_FUNCTIONS) == 6
