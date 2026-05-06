"""Tests for OracleIntakeRun.v1 - core/oracle/runtime.py"""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from core.models.governance import Authority
from core.oracle.runtime import (
    OracleIntakeRun,
    run_oracle_intake,
    _compute_run_hash,
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


FIXTURE_PAYLOADS = [
    {"source_id": "src-001", "source_type": "document", "payload": {"key": "value_a"}},
    {"source_id": "src-002", "source_type": "receipt", "payload": {"receipt_id": "r1"}},
]


def test_run_oracle_intake_returns_valid(locked_authority, tmp_path):
    run = run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=locked_authority,
        run_id="test-run-001",
        out_dir=tmp_path,
    )
    assert run.schema_version == "OracleIntakeRun.v1"
    assert run.run_id == "test-run-001"
    assert len(run.intake_envelopes) == 2
    assert len(run.evidence_packets) == 2
    assert len(run.normalization_packets) == 2
    assert len(run.replay_packets) == 2
    assert len(run.stabilization_packets) == 2
    assert len(run.approval_packets) == 2
    assert run.status == "complete"


def test_run_oracle_intake_deterministic_run_hash(locked_authority, tmp_path):
    run1 = run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=locked_authority,
        run_id="test-run-002",
        out_dir=tmp_path,
    )
    run2 = run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=locked_authority,
        run_id="test-run-002",
        out_dir=tmp_path,
    )
    assert run1.deterministic_run_hash == run2.deterministic_run_hash


def test_run_oracle_intake_writes_artifacts(locked_authority, tmp_path):
    run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=locked_authority,
        run_id="test-run-003",
        out_dir=tmp_path,
    )
    assert (tmp_path / "out/oracle/latest.json").exists()
    assert (tmp_path / "out/intake_conflicts/latest.json").exists()
    assert (tmp_path / "out/intake_approvals/latest.json").exists()


def test_run_oracle_intake_artifacts_parseable(locked_authority, tmp_path):
    run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=locked_authority,
        run_id="test-run-004",
        out_dir=tmp_path,
    )
    oracle_data = json.loads((tmp_path / "out/oracle/latest.json").read_text())
    assert oracle_data["run_id"] == "test-run-004"
    conflicts_data = json.loads((tmp_path / "out/intake_conflicts/latest.json").read_text())
    assert "conflicts" in conflicts_data
    approvals_data = json.loads((tmp_path / "out/intake_approvals/latest.json").read_text())
    assert "approvals" in approvals_data


def test_run_oracle_intake_requires_locked_authority(unlocked_authority, tmp_path):
    with pytest.raises(ValueError, match="authority must be locked"):
        run_oracle_intake(FIXTURE_PAYLOADS, unlocked_authority, out_dir=tmp_path)


def test_run_oracle_intake_empty_payloads_fails(locked_authority, tmp_path):
    run = run_oracle_intake([], locked_authority, out_dir=tmp_path)
    assert run.status == "failed"
    assert run.intake_envelopes == []


def test_run_oracle_intake_self_replay_always_matches(locked_authority, tmp_path):
    run = run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=locked_authority,
        run_id="test-run-self-replay",
        out_dir=tmp_path,
    )
    for rp in run.replay_packets:
        assert rp.get("deterministic_match") is True


def test_run_oracle_intake_approvals_default_false(locked_authority, tmp_path):
    """Approval defaults to False (operator review required)."""
    run = run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=locked_authority,
        run_id="test-run-approval",
        out_dir=tmp_path,
    )
    for ap in run.approval_packets:
        assert ap.get("approved") is False


def test_compute_run_hash_deterministic():
    envelopes = [{"raw_payload_hash": "a" * 64}, {"raw_payload_hash": "b" * 64}]
    h1 = _compute_run_hash("run-1", envelopes)
    h2 = _compute_run_hash("run-1", envelopes)
    assert h1 == h2
    assert len(h1) == 64


def test_run_oracle_intake_duplicate_sources_detected(locked_authority, tmp_path):
    """Duplicate source hashes should be detected."""
    dup_payloads = [
        {"source_id": "src-001", "source_type": "document", "payload": {"key": "same"}},
        {"source_id": "src-002", "source_type": "document", "payload": {"key": "same"}},
    ]
    run = run_oracle_intake(dup_payloads, locked_authority, run_id="dup-test", out_dir=tmp_path)
    # Both have same payload hash => duplicate detected
    conflict_pkts = run.conflict_packets
    conflict_types = [c.get("conflict_type") for c in conflict_pkts]
    assert "duplicate_source" in conflict_types


def test_run_oracle_intake_unique_run_id_generated(locked_authority, tmp_path):
    run = run_oracle_intake(FIXTURE_PAYLOADS, locked_authority, out_dir=tmp_path)
    assert run.run_id is not None
    assert len(run.run_id) > 0
