from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from abx.federated_evidence import FederatedEvidence, extract_federated_evidence


class PromotionReadinessStatus(str, Enum):
    LOCAL_CLOSURE_COMPLETE = "LOCAL_CLOSURE_COMPLETE"
    PROMOTION_READY = "PROMOTION_READY"
    PROMOTION_INCOMPLETE = "PROMOTION_INCOMPLETE"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"


class LocalPromotionState(str, Enum):
    LOCAL_ONLY_COMPLETE = "LOCAL_ONLY_COMPLETE"
    LOCAL_PROMOTION_READY = "LOCAL_PROMOTION_READY"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"


class FederatedReadinessState(str, Enum):
    FEDERATED_READY = "FEDERATED_READY"
    FEDERATED_INCOMPLETE = "FEDERATED_INCOMPLETE"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"


@dataclass(frozen=True)
class PromotionReadinessResult:
    run_id: str
    status: PromotionReadinessStatus
    local_promotion_state: LocalPromotionState
    federated_readiness_state: FederatedReadinessState
    local_closure_complete: bool
    promotion_ready: bool
    checked_at: str
    federated_evidence: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["local_promotion_state"] = self.local_promotion_state.value
        payload["federated_readiness_state"] = self.federated_readiness_state.value
        return payload


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _validator_valid(payload: dict[str, Any] | None) -> bool:
    return bool(payload and payload.get("status") == "VALID")


def _canonical_attestation_pass(payload: dict[str, Any] | None) -> bool:
    return bool(payload and payload.get("overall_status") == "PASS")


def _promotion_attestation_pass(payload: dict[str, Any] | None) -> bool:
    return bool(payload and payload.get("overall_status") == "PASS")


def _resolve_local_state(*, local_closure_complete: bool, promotion_ok: bool) -> LocalPromotionState:
    if not local_closure_complete:
        return LocalPromotionState.NOT_COMPUTABLE
    if promotion_ok:
        return LocalPromotionState.LOCAL_PROMOTION_READY
    return LocalPromotionState.LOCAL_ONLY_COMPLETE


def _resolve_federated_state(
    *,
    local_state: LocalPromotionState,
    federated_evidence: FederatedEvidence,
) -> FederatedReadinessState:
    if local_state != LocalPromotionState.LOCAL_PROMOTION_READY:
        return FederatedReadinessState.NOT_COMPUTABLE
    return (
        FederatedReadinessState.FEDERATED_READY
        if not federated_evidence.blockers
        else FederatedReadinessState.FEDERATED_INCOMPLETE
    )


def evaluate_promotion_readiness(
    run_id: str,
    *,
    base_dir: Path = Path("."),
    checked_at: str | None = None,
) -> PromotionReadinessResult:
    validator_path = base_dir / "out" / "validators" / f"execution-validation-{run_id}.json"
    local_attestation_path = base_dir / "out" / "attestation" / f"canonical_proof_{run_id}.json"
    promotion_attestation_path = base_dir / "out" / "attestation" / f"execution-attestation-{run_id}.json"

    validator_payload = _load_json(validator_path)
    local_attestation_payload = _load_json(local_attestation_path)
    promotion_attestation_payload = _load_json(promotion_attestation_path)

    errors: list[str] = []
    warnings: list[str] = []

    validator_ok = _validator_valid(validator_payload)
    local_attestation_ok = _canonical_attestation_pass(local_attestation_payload)
    local_closure_complete = validator_ok and local_attestation_ok

    if not validator_path.exists():
        errors.append("missing_validator_artifact")
    if not local_attestation_path.exists():
        errors.append("missing_local_attestation")

    promotion_ok = _promotion_attestation_pass(promotion_attestation_payload)
    local_state = _resolve_local_state(local_closure_complete=local_closure_complete, promotion_ok=promotion_ok)

    federated_evidence = extract_federated_evidence(promotion_attestation_payload, base_dir=base_dir)
    federated_state = _resolve_federated_state(local_state=local_state, federated_evidence=federated_evidence)

    if errors:
        status = PromotionReadinessStatus.NOT_COMPUTABLE
        promotion_ready = False
    else:
        if local_state == LocalPromotionState.LOCAL_PROMOTION_READY:
            status = PromotionReadinessStatus.PROMOTION_READY
            promotion_ready = True
            if federated_state == FederatedReadinessState.FEDERATED_INCOMPLETE:
                warnings.append("federated_readiness_incomplete")
        elif promotion_attestation_path.exists():
            status = PromotionReadinessStatus.PROMOTION_INCOMPLETE
            promotion_ready = False
            warnings.append("promotion_attestation_present_but_not_pass")
        else:
            status = PromotionReadinessStatus.LOCAL_CLOSURE_COMPLETE
            promotion_ready = False
            warnings.append("promotion_attestation_missing")

        if local_state == LocalPromotionState.NOT_COMPUTABLE:
            status = PromotionReadinessStatus.NOT_COMPUTABLE
            warnings.append("local_closure_not_complete")

    if federated_state == FederatedReadinessState.FEDERATED_INCOMPLETE:
        warnings.extend(federated_evidence.blockers)

    return PromotionReadinessResult(
        run_id=run_id,
        status=status,
        local_promotion_state=local_state,
        federated_readiness_state=federated_state,
        local_closure_complete=local_closure_complete,
        promotion_ready=promotion_ready,
        checked_at=checked_at or _utc_now_iso(),
        federated_evidence=federated_evidence.to_dict(),
        errors=sorted(set(errors)),
        warnings=sorted(set(warnings)),
        artifacts={
            "validator": validator_path.as_posix(),
            "local_attestation": local_attestation_path.as_posix(),
            "promotion_attestation": promotion_attestation_path.as_posix(),
        },
        provenance={
            "checker": "abx.promotion_readiness.evaluate_promotion_readiness",
            "version": "v0.4",
            "base_dir": str(base_dir),
            "federated_transport": "abx.federated_transport.verify_remote_evidence_manifest",
        },
    )


def emit_promotion_readiness(result: PromotionReadinessResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"promotion-readiness-{result.run_id}.json"
    out_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path
