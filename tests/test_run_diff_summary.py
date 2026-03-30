from __future__ import annotations

import json
from pathlib import Path

from abx.operator_views import compare_runs


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed(tmp_path: Path, run_id: str, policy_state: str) -> None:
    _write(tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID"})
    _write(tmp_path / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})
    federated = (
        {
            "external_attestation_refs": ["remote://attest/1"],
            "federated_ledger_ids": ["ledger-1"],
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        }
        if policy_state == "ALLOWED"
        else {}
    )
    _write(
        tmp_path / "out" / "attestation" / f"execution-attestation-{run_id}.json",
        {"overall_status": "PASS", "policy_gate": {"decision_state": policy_state}, "federated": federated},
    )
    _write(tmp_path / "out" / "policy" / f"promotion-policy-{run_id}.json", {"decision_state": policy_state, "blockers": [] if policy_state == "ALLOWED" else ["FEDERATED_INCOMPLETE"]})
    _write(tmp_path / "out" / "promotion" / f"promotion-readiness-{run_id}.json", {"status": "PROMOTION_READY", "local_promotion_state": "LOCAL_PROMOTION_READY", "federated_readiness_state": "FEDERATED_READY" if policy_state == "ALLOWED" else "FEDERATED_INCOMPLETE"})


def test_compare_runs_explains_policy_shift(tmp_path: Path) -> None:
    _seed(tmp_path, "RUN-A", "BLOCKED")
    _seed(tmp_path, "RUN-B", "ALLOWED")

    diff = compare_runs("RUN-A", "RUN-B", base_dir=tmp_path)

    assert diff.policy_delta["from"] == "BLOCKED"
    assert diff.policy_delta["to"] == "ALLOWED"
