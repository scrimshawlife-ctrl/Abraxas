from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from abx.promotion_readiness import (
    LocalPromotionState,
    evaluate_promotion_readiness,
)
from abx.promotion_policy import evaluate_promotion_policy


@dataclass(frozen=True)
class OperatorProjectionSummary:
    schema: str
    run_id: str
    generated_at: str
    tier1_local_closure: str
    tier2_local_promotion_state: str
    tier25_federated_readiness_state: str
    validator_status: str
    local_attestation_status: str
    promotion_attestation_status: str
    proof_closure_status: str
    federated_evidence_present: bool
    federated_evidence_state_summary: str = "UNKNOWN"
    remote_evidence_packet_count: int = 0
    federated_inconsistency_flag: bool = False
    promotion_policy_state: str = "UNKNOWN"
    promotion_policy_reason_codes: list[str] = field(default_factory=list)
    promotion_policy_requires_federation: bool = True
    promotion_policy_waived: bool = False
    federated_blockers: list[str] = field(default_factory=list)
    linkage: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def build_operator_projection_summary(
    run_id: str,
    *,
    base_dir: Path = Path("."),
    generated_at: str | None = None,
) -> OperatorProjectionSummary:
    readiness = evaluate_promotion_readiness(run_id, base_dir=base_dir)
    policy = evaluate_promotion_policy(run_id, base_dir=base_dir, readiness_result=readiness)

    validator_path = base_dir / "out" / "validators" / f"execution-validation-{run_id}.json"
    local_attestation_path = base_dir / "out" / "attestation" / f"canonical_proof_{run_id}.json"
    promotion_attestation_path = base_dir / "out" / "attestation" / f"execution-attestation-{run_id}.json"
    proof_projection_path = base_dir / "out" / "operator" / f"proof_projection_{run_id}.json"

    validator = _load_json(validator_path)
    local_attestation = _load_json(local_attestation_path)
    promotion_attestation = _load_json(promotion_attestation_path)
    proof_projection = _load_json(proof_projection_path)

    validator_status = str((validator or {}).get("status", "MISSING"))
    local_attestation_status = str((local_attestation or {}).get("overall_status", "MISSING"))
    promotion_attestation_status = str((promotion_attestation or {}).get("overall_status", "MISSING"))

    proof_closure_status = "COMPLETE" if (validator_status == "VALID" and local_attestation_status == "PASS") else "INCOMPLETE"
    if readiness.local_promotion_state == LocalPromotionState.NOT_COMPUTABLE:
        proof_closure_status = "NOT_COMPUTABLE"

    pointers = []
    rune_ids: list[str] = []
    phases: list[str] = []
    if isinstance(validator, dict):
        correlation = validator.get("correlation", {})
        if isinstance(correlation, dict):
            raw = correlation.get("pointers", [])
            if isinstance(raw, list):
                pointers = [str(item) for item in raw[:20]]
        rune_context = validator.get("runeContext", {})
        if isinstance(rune_context, dict):
            raw_runes = rune_context.get("runeIds", [])
            if isinstance(raw_runes, list):
                rune_ids = sorted({str(item) for item in raw_runes if str(item)})
            raw_phases = rune_context.get("phases", [])
            if isinstance(raw_phases, list):
                phases = sorted({str(item) for item in raw_phases if str(item)})

    federated_evidence = readiness.federated_evidence if isinstance(readiness.federated_evidence, dict) else {}
    federated_blockers = [str(v) for v in federated_evidence.get("blockers", [])][:8] if isinstance(federated_evidence.get("blockers", []), list) else []
    federated_evidence_present = bool(federated_evidence.get("evidence_present", False))
    federated_evidence_state = str(federated_evidence.get("federated_evidence_state", "UNKNOWN"))
    remote_evidence_packet_count = int(federated_evidence.get("remote_evidence_packet_count", 0) or 0)
    federated_inconsistency = bool(federated_evidence.get("federated_inconsistency", False))

    linkage = {
        "has_validator": validator_path.exists(),
        "has_local_attestation": local_attestation_path.exists(),
        "has_promotion_attestation": promotion_attestation_path.exists(),
        "has_tier1_projection": proof_projection_path.exists(),
        "correlation_pointer_count": len(pointers),
        "correlation_pointers": pointers,
        "rune_id_count": len(rune_ids),
        "rune_ids": rune_ids[:20],
        "phase_count": len(phases),
        "phases": phases[:20],
        "key_artifact_ids": {
            "validator_artifact_id": str((validator or {}).get("artifactId", "MISSING")),
            "tier1_projection_artifact_type": str((proof_projection or {}).get("artifactType", "MISSING")),
        },
    }

    return OperatorProjectionSummary(
        schema="OperatorProjectionSummary.v1",
        run_id=run_id,
        generated_at=generated_at or _utc_now_iso(),
        tier1_local_closure="PASS" if proof_closure_status == "COMPLETE" else proof_closure_status,
        tier2_local_promotion_state=readiness.local_promotion_state.value,
        tier25_federated_readiness_state=readiness.federated_readiness_state.value,
        validator_status=validator_status,
        local_attestation_status=local_attestation_status,
        promotion_attestation_status=promotion_attestation_status,
        proof_closure_status=proof_closure_status,
        federated_evidence_present=federated_evidence_present,
        federated_evidence_state_summary=federated_evidence_state,
        remote_evidence_packet_count=remote_evidence_packet_count,
        federated_inconsistency_flag=federated_inconsistency,
        promotion_policy_state=policy.decision_state.value,
        promotion_policy_reason_codes=policy.reason_codes[:8],
        promotion_policy_requires_federation=policy.requires_federation,
        promotion_policy_waived=policy.waived,
        federated_blockers=federated_blockers,
        linkage=linkage,
        artifacts={
            "validator": validator_path.as_posix(),
            "local_attestation": local_attestation_path.as_posix(),
            "promotion_attestation": promotion_attestation_path.as_posix(),
            "tier1_projection": proof_projection_path.as_posix(),
        },
        provenance={
            "source": "abx.operator_projection.build_operator_projection_summary",
            "readiness_provenance": readiness.provenance,
            "policy_provenance": policy.provenance,
        },
    )


def emit_operator_projection_summary(summary: OperatorProjectionSummary, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"operator-projection-{summary.run_id}.json"
    out_path.write_text(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path
