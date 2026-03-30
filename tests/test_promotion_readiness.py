from __future__ import annotations

import json
from pathlib import Path

from abx.promotion_readiness import (
    FederatedReadinessState,
    LocalPromotionState,
    PromotionReadinessStatus,
    emit_promotion_readiness,
    evaluate_promotion_readiness,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_local_closure(base: Path, run_id: str) -> None:
    _write(base / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID"})
    _write(base / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})


def test_local_only_complete_when_no_promotion_attestation(tmp_path: Path) -> None:
    run_id = "RUN-BRIDGE-LOCAL"
    _seed_local_closure(tmp_path, run_id)

    result = evaluate_promotion_readiness(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert result.status == PromotionReadinessStatus.LOCAL_CLOSURE_COMPLETE
    assert result.local_promotion_state == LocalPromotionState.LOCAL_ONLY_COMPLETE
    assert result.federated_readiness_state == FederatedReadinessState.NOT_COMPUTABLE


def test_local_promotion_ready_but_federated_incomplete_when_no_federated_markers(tmp_path: Path) -> None:
    run_id = "RUN-BRIDGE-LOCAL-PROMO"
    _seed_local_closure(tmp_path, run_id)
    _write(tmp_path / "out" / "attestation" / f"execution-attestation-{run_id}.json", {"overall_status": "PASS"})

    result = evaluate_promotion_readiness(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert result.status == PromotionReadinessStatus.PROMOTION_READY
    assert result.local_promotion_state == LocalPromotionState.LOCAL_PROMOTION_READY
    assert result.federated_readiness_state == FederatedReadinessState.FEDERATED_INCOMPLETE
    assert "missing_external_attestation_refs_and_federated_ledger_ids" in result.warnings


def test_federated_ready_when_remote_markers_are_present_and_valid(tmp_path: Path) -> None:
    run_id = "RUN-BRIDGE-FED-READY"
    _seed_local_closure(tmp_path, run_id)
    _write(
        tmp_path / "out" / "attestation" / f"execution-attestation-{run_id}.json",
        {
            "overall_status": "PASS",
            "federated": {
                "external_attestation_refs": ["remote://attest/1"],
                "federated_ledger_ids": ["ledger-1"],
                "remote_validation_status": "VALID",
                "remote_attestation_status": "PASS",
            },
        },
    )

    result = evaluate_promotion_readiness(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert result.local_promotion_state == LocalPromotionState.LOCAL_PROMOTION_READY
    assert result.federated_readiness_state == FederatedReadinessState.FEDERATED_READY


def test_promotion_readiness_not_computable_when_local_closure_surfaces_missing(tmp_path: Path) -> None:
    result = evaluate_promotion_readiness("RUN-BRIDGE-NC", base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert result.status == PromotionReadinessStatus.NOT_COMPUTABLE
    assert result.local_promotion_state == LocalPromotionState.NOT_COMPUTABLE
    assert result.federated_readiness_state == FederatedReadinessState.NOT_COMPUTABLE
    assert "missing_validator_artifact" in result.errors


def test_promotion_readiness_is_deterministic_and_emits_artifact(tmp_path: Path) -> None:
    run_id = "RUN-BRIDGE-DET"
    _seed_local_closure(tmp_path, run_id)

    a = evaluate_promotion_readiness(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")
    b = evaluate_promotion_readiness(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert a.to_dict() == b.to_dict()

    out_path = emit_promotion_readiness(a, tmp_path / "out" / "promotion")
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == run_id
    assert payload["local_promotion_state"] == "LOCAL_ONLY_COMPLETE"
