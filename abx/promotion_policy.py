from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from abx.promotion_readiness import (
    FederatedReadinessState,
    LocalPromotionState,
    PromotionReadinessResult,
    PromotionReadinessStatus,
    evaluate_promotion_readiness,
)


class PromotionPolicyState(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    WAIVED = "WAIVED"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"


@dataclass(frozen=True)
class PromotionPolicyDecision:
    run_id: str
    decision_state: PromotionPolicyState
    requires_federation: bool
    waived: bool
    checked_at: str
    reason_codes: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    readiness_status: str = "UNKNOWN"
    local_promotion_state: str = "UNKNOWN"
    federated_readiness_state: str = "UNKNOWN"
    federated_evidence_summary: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision_state"] = self.decision_state.value
        return payload


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _waiver_reason(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    if not bool(payload.get("waive", False)):
        return None
    if str(payload.get("scope", "")).strip() != "promotion_policy":
        return None
    reason_code = str(payload.get("reason_code", "")).strip()
    return reason_code or "waiver_applied"


def evaluate_promotion_policy(
    run_id: str,
    *,
    base_dir: Path = Path("."),
    checked_at: str | None = None,
    require_federation: bool = True,
    readiness_result: PromotionReadinessResult | None = None,
) -> PromotionPolicyDecision:
    readiness = readiness_result or evaluate_promotion_readiness(run_id, base_dir=base_dir, checked_at=checked_at)

    waiver_path = base_dir / "out" / "policy" / "waivers" / f"promotion-policy-waiver-{run_id}.json"
    waiver_payload = _load_json(waiver_path) if waiver_path.exists() else None
    waiver_reason = _waiver_reason(waiver_payload)

    reason_codes: list[str] = []
    blockers: list[str] = []

    if readiness.status == PromotionReadinessStatus.NOT_COMPUTABLE:
        reason_codes.append("promotion_readiness_not_computable")
        blockers.extend(readiness.errors)
        decision_state = PromotionPolicyState.NOT_COMPUTABLE
    elif readiness.local_promotion_state != LocalPromotionState.LOCAL_PROMOTION_READY:
        reason_codes.append("local_promotion_not_ready")
        blockers.append(readiness.local_promotion_state.value)
        decision_state = PromotionPolicyState.BLOCKED
    elif require_federation and readiness.federated_readiness_state != FederatedReadinessState.FEDERATED_READY:
        federated_evidence = readiness.federated_evidence if isinstance(readiness.federated_evidence, dict) else {}
        remote_evidence_status = str(federated_evidence.get("remote_evidence_status", "NOT_DECLARED"))
        federated_evidence_state = str(federated_evidence.get("federated_evidence_state", "ABSENT"))
        if remote_evidence_status == "MISSING":
            reason_codes.append("federated_remote_evidence_missing")
        elif remote_evidence_status == "MALFORMED" or federated_evidence_state == "MALFORMED":
            reason_codes.append("federated_remote_evidence_malformed")
        elif remote_evidence_status == "INCONSISTENT" or federated_evidence_state == "INCONSISTENT":
            reason_codes.append("federated_remote_evidence_inconsistent")
        elif remote_evidence_status == "STALE" or federated_evidence_state == "STALE":
            reason_codes.append("federated_remote_evidence_stale")
        elif remote_evidence_status == "PARTIAL" or federated_evidence_state == "PARTIAL":
            reason_codes.append("federated_remote_evidence_partial")
        else:
            reason_codes.append("federated_readiness_required")
        blockers.append(readiness.federated_readiness_state.value)
        federated_blockers = federated_evidence.get("blockers", [])
        if isinstance(federated_blockers, list):
            blockers.extend(str(code) for code in federated_blockers)

        if waiver_reason:
            reason_codes.append(waiver_reason)
            decision_state = PromotionPolicyState.WAIVED
        else:
            decision_state = PromotionPolicyState.BLOCKED
    else:
        reason_codes.append("policy_requirements_satisfied")
        decision_state = PromotionPolicyState.ALLOWED

    return PromotionPolicyDecision(
        run_id=run_id,
        decision_state=decision_state,
        requires_federation=require_federation,
        waived=decision_state == PromotionPolicyState.WAIVED,
        checked_at=checked_at or _utc_now_iso(),
        reason_codes=sorted(set(reason_codes)),
        blockers=sorted(set(blockers)),
        readiness_status=readiness.status.value,
        local_promotion_state=readiness.local_promotion_state.value,
        federated_readiness_state=readiness.federated_readiness_state.value,
        federated_evidence_summary={
            "remote_evidence_status": str((readiness.federated_evidence or {}).get("remote_evidence_status", "UNKNOWN")),
            "federated_evidence_state": str((readiness.federated_evidence or {}).get("federated_evidence_state", "UNKNOWN")),
            "remote_evidence_manifest_id": str((readiness.federated_evidence or {}).get("remote_evidence_manifest_id", "")),
            "remote_evidence_packet_count": int((readiness.federated_evidence or {}).get("remote_evidence_packet_count", 0) or 0),
            "federated_inconsistency": bool((readiness.federated_evidence or {}).get("federated_inconsistency", False)),
            "remote_evidence_packet_ids": [
                str(v) for v in ((readiness.federated_evidence or {}).get("remote_evidence_packet_ids", []) or [])
            ][:16],
            "external_attestation_refs": [
                str(v) for v in ((readiness.federated_evidence or {}).get("external_attestation_refs", []) or [])
            ][:16],
            "federated_ledger_ids": [
                str(v) for v in ((readiness.federated_evidence or {}).get("federated_ledger_ids", []) or [])
            ][:16],
        },
        artifacts={
            **readiness.artifacts,
            "waiver": waiver_path.as_posix(),
        },
        provenance={
            "checker": "abx.promotion_policy.evaluate_promotion_policy",
            "version": "v0.3",
            "base_dir": str(base_dir),
            "readiness_checker": readiness.provenance.get("checker", "unknown"),
        },
    )


def emit_promotion_policy(decision: PromotionPolicyDecision, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"promotion-policy-{decision.run_id}.json"
    out_path.write_text(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path
