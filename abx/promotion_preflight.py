from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from abx.gap_closure_invariance import read_gap_closure_invariance_payload
from abx.readiness_comparison import read_latest_comparison

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "PromotionPreflightAdvisory.v1.json"
LATEST_PATH = ROOT / "out" / "reports" / "promotion_preflight.latest.json"


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _advisory_id(*, timestamp_utc: str, developer_status: str, gap_readiness_state: str, promotion_decision: str, blockers: list[str], evidence_gaps: list[str]) -> str:
    material = json.dumps(
        {
            "timestamp_utc": timestamp_utc,
            "developer_status": developer_status,
            "gap_readiness_state": gap_readiness_state,
            "promotion_decision": promotion_decision,
            "blockers": blockers,
            "evidence_gaps": evidence_gaps,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _advisory_state(*, missing: bool, blockers: list[str], evidence_gaps: list[str], developer_status: str, gap_readiness_state: str) -> str:
    if missing:
        return "NOT_COMPUTABLE"
    readiness_blocked = developer_status in {"FAIL", "PARTIAL", "NOT_COMPUTABLE"}
    invariance_blockers = [item for item in blockers if not item.startswith("developer_readiness_")]
    invariance_blocked = bool(invariance_blockers) or gap_readiness_state in {
        "NOT_COMPUTABLE",
        "PARTIAL",
        "BLOCKED",
        "DRIFT_DETECTED",
    }

    if readiness_blocked and invariance_blocked:
        return "BLOCKED_BOTH"
    if invariance_blocked:
        return "BLOCKED_INVARIANCE"
    if readiness_blocked or evidence_gaps:
        return "BLOCKED_READINESS"
    return "READY_CANDIDATE"


def build_promotion_preflight_advisory(*, timestamp_utc: str | None = None) -> dict[str, Any]:
    ts = timestamp_utc or _now_utc()
    comparison_payload = read_latest_comparison()
    invariance_payload = read_gap_closure_invariance_payload()

    missing_reasons: list[str] = []
    if str(comparison_payload.get("status", "NOT_COMPUTABLE")).upper() != "OK":
        missing_reasons.append(f"comparison:{comparison_payload.get('reason', 'unknown')}")
    if str(invariance_payload.get("status", "NOT_COMPUTABLE")).upper() == "NOT_COMPUTABLE":
        missing_reasons.append(f"invariance:{invariance_payload.get('reason', 'unknown')}")

    comparison = comparison_payload.get("comparison") if isinstance(comparison_payload.get("comparison"), dict) else {}
    dev = comparison.get("developer_readiness") if isinstance(comparison.get("developer_readiness"), dict) else {}
    gap_cmp = comparison.get("gap_closure_invariance") if isinstance(comparison.get("gap_closure_invariance"), dict) else {}

    invariance_projection = invariance_payload.get("projection") if isinstance(invariance_payload.get("projection"), dict) else {}

    developer_status = str(dev.get("status", "NOT_COMPUTABLE"))
    gap_readiness_state = str(gap_cmp.get("readiness_state", invariance_projection.get("readiness_state", "NOT_COMPUTABLE")))
    promotion_decision = str(gap_cmp.get("promotion_decision", invariance_projection.get("promotion_decision", "HOLD")))

    blockers = sorted(
        str(item)
        for item in invariance_projection.get("unmet_conditions", [])
        if str(item)
    )
    if developer_status in {"FAIL", "PARTIAL"}:
        blockers.append(f"developer_readiness_{developer_status.lower()}")
    blockers = sorted(set(blockers))

    evidence_gaps: list[str] = []
    missing_surfaces_count = int(dev.get("missing_surfaces_count", 0) or 0)
    if missing_surfaces_count > 0:
        evidence_gaps.append(f"developer_missing_surfaces:{missing_surfaces_count}")
    for reason in missing_reasons:
        evidence_gaps.append(reason)
    evidence_gaps = sorted(set(evidence_gaps))

    advisory = {
        "advisory_id": _advisory_id(
            timestamp_utc=ts,
            developer_status=developer_status,
            gap_readiness_state=gap_readiness_state,
            promotion_decision=promotion_decision,
            blockers=blockers,
            evidence_gaps=evidence_gaps,
        ),
        "timestamp_utc": ts,
        "developer_readiness_status": developer_status,
        "gap_closure_readiness_state": gap_readiness_state,
        "promotion_decision": promotion_decision,
        "blockers": blockers,
        "evidence_gaps": evidence_gaps,
        "advisory_state": _advisory_state(
            missing=bool(missing_reasons),
            blockers=blockers,
            evidence_gaps=evidence_gaps,
            developer_status=developer_status,
            gap_readiness_state=gap_readiness_state,
        ),
        "provenance": {
            "source": "abx.promotion_preflight.build_promotion_preflight_advisory",
            "comparison_reason": str(comparison_payload.get("reason", "unknown")),
            "invariance_reason": str(invariance_payload.get("reason", "unknown")),
            "deterministic_ordering": [
                "advisory_id",
                "timestamp_utc",
                "developer_readiness_status",
                "gap_closure_readiness_state",
                "promotion_decision",
                "blockers",
                "evidence_gaps",
                "advisory_state",
                "provenance",
            ],
        },
    }

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(advisory)
    return advisory


def write_latest_advisory(advisory: dict[str, Any], path: Path = LATEST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(advisory, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read_promotion_preflight(path: Path = LATEST_PATH) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "NOT_COMPUTABLE",
            "reason": f"report_missing:{path.as_posix()}",
            "advisory": None,
        }
    advisory = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": "OK",
        "reason": "ok",
        "advisory": advisory,
    }
