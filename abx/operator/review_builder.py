from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from abx.schemas.operator_review_item import OperatorReviewItem


def _make_review_item(
    *,
    review_id: str,
    source_system: str,
    decision_type: str,
    priority: str,
    reason: str,
    evidence_refs: list[str],
) -> OperatorReviewItem:
    return {
        "schema_version": "OperatorReviewItem.v1",
        "review_id": review_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_system": source_system,
        "decision_type": decision_type,
        "priority": priority,
        "reason": reason,
        "evidence_refs": sorted(set(evidence_refs)),
        "operator_required": True,
        "auto_apply_allowed": False,
    }


def build_review_items(report: Mapping[str, Any], advisory: Mapping[str, Any], fusion: Mapping[str, Any]) -> list[OperatorReviewItem]:
    items: list[OperatorReviewItem] = []
    status = str(report.get("calibration_drift_status", "NOT_COMPUTABLE") or "NOT_COMPUTABLE")
    if status != "PASS":
        items.append(
            _make_review_item(
                review_id="calibration.requires_review",
                source_system="calibration",
                decision_type="REQUEST_EVIDENCE",
                priority="P0",
                reason="Calibration requires review",
                evidence_refs=list(report.get("evidence_refs", [])),
            )
        )

    drift_alerts = fusion.get("drift_alerts", []) if isinstance(fusion.get("drift_alerts", []), list) else []
    if "DOMAIN_DOMINANCE_DRIFT" in drift_alerts:
        items.append(
            _make_review_item(
                review_id="fusion.domain_dominance_drift",
                source_system="fusion",
                decision_type="REVIEW",
                priority="P1",
                reason="Dominance imbalance detected",
                evidence_refs=list(fusion.get("evidence_refs", [])),
            )
        )

    confidence = float(fusion.get("confidence", 0.0) or 0.0)
    if confidence < 0.5:
        items.append(
            _make_review_item(
                review_id="fusion.low_confidence",
                source_system="fusion",
                decision_type="REVIEW",
                priority="P1",
                reason="Low confidence fusion output",
                evidence_refs=list(fusion.get("evidence_refs", [])),
            )
        )

    if not items:
        items.append(
            _make_review_item(
                review_id="fusion.no_action",
                source_system="fusion",
                decision_type="NO_ACTION",
                priority="P2",
                reason="No operator action required",
                evidence_refs=list(fusion.get("evidence_refs", [])),
            )
        )

    return items
