from __future__ import annotations

import json
from pathlib import Path

from abx.promotion_policy import (
    PromotionPolicyState,
    emit_promotion_policy,
    evaluate_promotion_policy,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_local_closure(base: Path, run_id: str) -> None:
    _write(base / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID"})
    _write(base / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})


def _seed_promotion(base: Path, run_id: str, *, federated: dict | None = None) -> None:
    payload = {"overall_status": "PASS"}
    if federated is not None:
        payload["federated"] = federated
    _write(base / "out" / "attestation" / f"execution-attestation-{run_id}.json", payload)


def test_policy_allowed_when_local_and_federated_ready(tmp_path: Path) -> None:
    run_id = "RUN-POLICY-ALLOW"
    _seed_local_closure(tmp_path, run_id)
    _seed_promotion(
        tmp_path,
        run_id,
        federated={
            "external_attestation_refs": ["remote://attest/1"],
            "federated_ledger_ids": ["ledger-1"],
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        },
    )

    decision = evaluate_promotion_policy(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert decision.decision_state == PromotionPolicyState.ALLOWED
    assert decision.waived is False


def test_policy_blocked_when_local_promotion_not_ready(tmp_path: Path) -> None:
    run_id = "RUN-POLICY-LOCAL-BLOCK"
    _seed_local_closure(tmp_path, run_id)

    decision = evaluate_promotion_policy(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert decision.decision_state == PromotionPolicyState.BLOCKED
    assert "local_promotion_not_ready" in decision.reason_codes


def test_policy_blocked_when_federated_required_but_missing(tmp_path: Path) -> None:
    run_id = "RUN-POLICY-FED-BLOCK"
    _seed_local_closure(tmp_path, run_id)
    _seed_promotion(tmp_path, run_id)

    decision = evaluate_promotion_policy(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert decision.decision_state == PromotionPolicyState.BLOCKED
    assert "federated_readiness_required" in decision.reason_codes
    assert decision.federated_evidence_summary["remote_evidence_status"] == "NOT_DECLARED"


def test_policy_blocked_when_remote_evidence_manifest_malformed(tmp_path: Path) -> None:
    run_id = "RUN-POLICY-REMOTE-MALFORMED"
    _seed_local_closure(tmp_path, run_id)
    _write(tmp_path / "out" / "federated" / "bad.json", {"schema": "RemoteEvidenceManifest.v0"})
    _seed_promotion(
        tmp_path,
        run_id,
        federated={
            "remote_evidence_manifest": "out/federated/bad.json",
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        },
    )

    decision = evaluate_promotion_policy(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert decision.decision_state == PromotionPolicyState.BLOCKED
    assert "federated_remote_evidence_malformed" in decision.reason_codes


def test_policy_waived_only_with_explicit_waiver_artifact(tmp_path: Path) -> None:
    run_id = "RUN-POLICY-WAIVED"
    _seed_local_closure(tmp_path, run_id)
    _seed_promotion(tmp_path, run_id)
    _write(
        tmp_path / "out" / "policy" / "waivers" / f"promotion-policy-waiver-{run_id}.json",
        {
            "waive": True,
            "scope": "promotion_policy",
            "reason_code": "documented_emergency_override",
        },
    )

    decision = evaluate_promotion_policy(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert decision.decision_state == PromotionPolicyState.WAIVED
    assert decision.waived is True
    assert "documented_emergency_override" in decision.reason_codes


def test_policy_not_computable_when_local_surfaces_missing(tmp_path: Path) -> None:
    decision = evaluate_promotion_policy("RUN-POLICY-NC", base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert decision.decision_state == PromotionPolicyState.NOT_COMPUTABLE
    assert "promotion_readiness_not_computable" in decision.reason_codes


def test_policy_is_deterministic_and_emits_artifact(tmp_path: Path) -> None:
    run_id = "RUN-POLICY-DET"
    _seed_local_closure(tmp_path, run_id)
    _seed_promotion(
        tmp_path,
        run_id,
        federated={
            "external_attestation_refs": ["remote://attest/det"],
            "federated_ledger_ids": ["ledger-det"],
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        },
    )

    a = evaluate_promotion_policy(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")
    b = evaluate_promotion_policy(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert a.to_dict() == b.to_dict()

    out_path = emit_promotion_policy(a, tmp_path / "out" / "policy")
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == run_id
    assert payload["decision_state"] == "ALLOWED"


def test_policy_blocked_when_remote_evidence_manifest_inconsistent(tmp_path: Path) -> None:
    run_id = "RUN-POLICY-REMOTE-INCONSISTENT"
    _seed_local_closure(tmp_path, run_id)
    _write(
        tmp_path / "out" / "federated" / "inconsistent.json",
        {
            "schema": "RemoteEvidenceManifest.v1",
            "manifest_id": "manifest-x",
            "run_id": run_id,
            "origin": "federation://cluster-a",
            "packets": [
                {
                    "packet_id": "pkt-1",
                    "run_id": run_id,
                    "ref": "remote://pkt/1",
                    "status": "VALID",
                    "observed_at": "2026-03-30T00:00:00+00:00",
                },
                {
                    "packet_id": "pkt-2",
                    "run_id": run_id,
                    "ref": "remote://pkt/2",
                    "status": "FAIL",
                    "observed_at": "2026-03-30T00:00:00+00:00",
                },
            ],
        },
    )
    _seed_promotion(
        tmp_path,
        run_id,
        federated={
            "remote_evidence_manifest": "out/federated/inconsistent.json",
            "external_attestation_refs": ["remote://attest/1"],
            "federated_ledger_ids": ["ledger-1"],
            "remote_validation_status": "VALID",
            "remote_attestation_status": "PASS",
        },
    )

    decision = evaluate_promotion_policy(run_id, base_dir=tmp_path, checked_at="2026-03-30T00:00:00+00:00")

    assert decision.decision_state == PromotionPolicyState.BLOCKED
    assert "federated_remote_evidence_inconsistent" in decision.reason_codes
    assert decision.federated_evidence_summary["federated_inconsistency"] is True
