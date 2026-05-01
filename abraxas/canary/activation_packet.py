from __future__ import annotations

from hashlib import sha256
from typing import Any

from abraxas.canary.activation_models import AUTHORITY_FLAGS, ActivationPacket
from abraxas.core.canonical import canonical_json


def _sha_obj(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _invalid_recommendation(rec: dict[str, Any]) -> bool:
    required = ["recommendation_id", "overlay_id", "source_key", "status", "basis"]
    return any(rec.get(key) is None for key in required) or not isinstance(rec.get("basis"), dict)


def build_activation_packets(
    review_gate_run: dict[str, Any],
    overlay_run: dict[str, Any],
    ledger_run: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recommendations = review_gate_run.get("recommendations") if isinstance(review_gate_run.get("recommendations"), list) else []
    overlays = overlay_run.get("overlays") if isinstance(overlay_run.get("overlays"), list) else []
    entries = ledger_run.get("entries") if isinstance(ledger_run.get("entries"), list) else []

    overlay_by_id = {str(o.get("overlay_id")): o for o in overlays if isinstance(o, dict) and o.get("overlay_id")}
    ledger_by_entry_id = {str(e.get("entry_id")): e for e in entries if isinstance(e, dict) and e.get("entry_id")}

    recs_sorted = sorted(
        (r for r in recommendations if isinstance(r, dict)),
        key=lambda r: (str(r.get("source_key", "")), str(r.get("recommendation_id", ""))),
    )

    packets: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for rec in recs_sorted:
        source_key = str(rec.get("source_key", ""))
        overlay_id = str(rec.get("overlay_id", ""))

        if _invalid_recommendation(rec):
            skipped.append({"source_key": source_key, "overlay_id": overlay_id or None, "reason": "invalid_recommendation"})
            continue

        status = str(rec.get("status"))
        if status != "recommend_approve_for_activation_review":
            skipped.append(
                {
                    "source_key": source_key,
                    "overlay_id": overlay_id,
                    "reason": f"not_approved_for_activation_review:{status}",
                }
            )
            continue

        overlay = overlay_by_id.get(overlay_id)
        if overlay is None:
            skipped.append({"source_key": source_key, "overlay_id": overlay_id, "reason": "missing_overlay"})
            continue

        if overlay.get("source_key") is None:
            skipped.append({"source_key": source_key, "overlay_id": overlay_id, "reason": "invalid_overlay"})
            continue

        entry_id = str(overlay.get("entry_id")) if overlay.get("entry_id") is not None else None
        proposal_id = str(overlay.get("proposal_id")) if overlay.get("proposal_id") is not None else None
        ledger_entry = ledger_by_entry_id.get(entry_id or "") if entry_id else None
        ledger_entry_hash = _sha_obj(ledger_entry) if ledger_entry is not None else None

        basis = rec.get("basis")
        summary = {
            "improvement_direction": basis.get("improvement_direction"),
            "delta_error": basis.get("delta_error"),
            "scores_used": int(basis.get("scores_used", 0)),
        }
        evidence = {
            "baseline_error": basis.get("baseline_error"),
            "simulated_error": basis.get("simulated_error"),
            "forecasts_matched": int(basis.get("forecasts_matched", 0)),
        }
        lineage = {
            "recommendation_id": rec.get("recommendation_id"),
            "overlay_id": overlay_id,
            "ledger_entry_hash": ledger_entry_hash,
            "proposal_id": proposal_id,
        }

        base_packet = {
            "packet_version": "CanaryActivationPacket.v1",
            "overlay_id": overlay_id,
            "entry_id": entry_id,
            "proposal_id": proposal_id,
            "source_key": source_key,
            "recommendation_status": status,
            "summary": summary,
            "evidence": evidence,
            "lineage": lineage,
            "review": {"reviewer_notes": [], "approval_status": "unreviewed", "decision_reason": None},
            "authority": dict(AUTHORITY_FLAGS),
        }
        packet_id = _sha_obj(base_packet)
        packets.append(
            ActivationPacket(
                packet_id=packet_id,
                overlay_id=overlay_id,
                entry_id=entry_id,
                proposal_id=proposal_id,
                source_key=source_key,
                recommendation_status=status,
                summary=summary,
                evidence=evidence,
                lineage=lineage,
            ).to_dict()
        )

    packets = sorted(packets, key=lambda p: (p["source_key"], p["packet_id"]))
    skipped = sorted(
        skipped,
        key=lambda s: (str(s.get("source_key", "")), str(s.get("overlay_id", "")), str(s.get("reason", ""))),
    )
    return packets, skipped
