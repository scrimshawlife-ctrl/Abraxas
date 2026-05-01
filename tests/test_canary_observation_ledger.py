from __future__ import annotations

import copy

from abraxas.canary.observation_runner import run_observation_ledger
from abraxas.core.canonical import canonical_json


def _execution(created_at: str = "2026-01-01T00:00:00Z", status: str = "completed", source_key: str = "s1") -> dict:
    return {
        "schema_version": "CanaryActivationExecutionRun.v1",
        "created_at": created_at,
        "execution_scope": {"scope_id": "scope1", "sandbox_root": "/tmp/sb"},
        "executions": [
            {
                "execution_id": "ex1",
                "packet_id": "p1",
                "source_key": source_key,
                "execution_status": status,
                "applied_artifact": {"artifact_hash": "ah1", "artifact_path": "/tmp/sb/canary_activation_receipts/ex1.json"},
                "execution_scope": {"scope_id": "scope1"},
                "lineage": {},
                "reason": None,
            }
        ],
    }


def test_create_dedupe_determinism_ordering_replay_rollback_authority_counts_immutability() -> None:
    ex_run = _execution()
    ex_run_2 = _execution(created_at="2027-01-01T00:00:00Z")
    ex0 = copy.deepcopy(ex_run)

    out1 = run_observation_ledger(ex_run)
    out2 = run_observation_ledger(ex_run_2)
    assert out1["counts"]["entries_created"] == 1
    assert out1["counts"]["entries_existing"] == 0
    assert out1["entries"][0]["replay"]["replayable"] is True
    assert out1["entries"][0]["rollback"]["rollback_prepared"] is False
    assert out1["entries"][0]["rollback"]["rollback_key"] is not None
    assert out1["authority"] == {
        "observation_ledger_write": True,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }

    # created_at not in observation hash
    assert out1["entries"][0]["observation_id"] == out2["entries"][0]["observation_id"]

    # dedupe
    out3 = run_observation_ledger(ex_run, out1)
    assert out3["counts"]["entries_created"] == 0
    assert out3["counts"]["entries_existing"] == 1
    assert out3["counts"]["entries_total"] == 1

    # ordering deterministic
    ex_multi = {
        "schema_version": "CanaryActivationExecutionRun.v1",
        "created_at": "2026-01-01T00:00:00Z",
        "execution_scope": {"scope_id": "scope1", "sandbox_root": None},
        "executions": [
            {"execution_id": "ex2", "packet_id": "p2", "source_key": "s2", "execution_status": "completed", "applied_artifact": {"artifact_hash": "b", "artifact_path": None}, "execution_scope": {"scope_id": "scope1"}, "lineage": {}, "reason": None},
            {"execution_id": "ex1", "packet_id": "p1", "source_key": "s1", "execution_status": "failed", "applied_artifact": {"artifact_hash": "a", "artifact_path": None}, "execution_scope": {"scope_id": "scope1"}, "lineage": {}, "reason": "x"},
        ],
    }
    out4 = run_observation_ledger(ex_multi)
    assert out4["entries"] == sorted(out4["entries"], key=lambda e: (e["source_key"], e["observation_id"]))
    failed_entry = [e for e in out4["entries"] if e["execution_id"] == "ex1"][0]
    assert failed_entry["replay"]["replayable"] is False
    assert failed_entry["rollback"]["rollback_key"] is None

    # input immutable
    assert ex_run == ex0

    # byte identical
    assert canonical_json(run_observation_ledger(ex_run)) == canonical_json(run_observation_ledger(ex_run))
