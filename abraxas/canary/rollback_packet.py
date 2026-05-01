from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.rollback_packet_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_rollback_packet_run(
    review_run: Mapping[str, Any],
    rollback_prep_run: Mapping[str, Any],
    observation_run: Mapping[str, Any],
) -> dict:
    reviews = deepcopy(dict(review_run)).get("recommendations")
    reviews = reviews if isinstance(reviews, list) else []
    preps = deepcopy(dict(rollback_prep_run)).get("rollbacks")
    preps = preps if isinstance(preps, list) else []
    obs_entries = deepcopy(dict(observation_run)).get("entries")
    obs_entries = obs_entries if isinstance(obs_entries, list) else []

    prep_by_rollback = {str(p.get("rollback_id")): p for p in preps if isinstance(p, dict) and p.get("rollback_id")}
    obs_by_id = {str(o.get("observation_id")): o for o in obs_entries if isinstance(o, dict) and o.get("observation_id")}

    packets: list[dict] = []
    skipped: list[dict] = []

    for rec in sorted((r for r in reviews if isinstance(r, dict)), key=lambda r: (str(r.get("source_key", "")), str(r.get("recommendation_id", "")))):
        required = ["recommendation_id", "rollback_id", "observation_id", "execution_id", "source_key", "status", "lineage"]
        if any(rec.get(k) is None for k in required):
            skipped.append({"source_key": rec.get("source_key"), "rollback_id": rec.get("rollback_id"), "reason": "invalid_recommendation"})
            continue

        if rec.get("status") != "recommend_approve_for_rollback_review":
            skipped.append({"source_key": rec.get("source_key"), "rollback_id": rec.get("rollback_id"), "reason": f"not_approved_for_rollback_review:{rec.get('status')}"})
            continue

        prep = prep_by_rollback.get(str(rec.get("rollback_id")))
        if prep is None:
            skipped.append({"source_key": rec.get("source_key"), "rollback_id": rec.get("rollback_id"), "reason": "missing_rollback_prep"})
            continue

        prep_required = ["rollback_plan", "safety", "status", "rollback_key", "observation_id", "execution_id"]
        if any(prep.get(k) is None for k in prep_required):
            skipped.append({"source_key": rec.get("source_key"), "rollback_id": rec.get("rollback_id"), "reason": "invalid_rollback_prep"})
            continue

        obs = obs_by_id.get(str(prep.get("observation_id")))
        if obs is None:
            skipped.append({"source_key": rec.get("source_key"), "rollback_id": rec.get("rollback_id"), "reason": "missing_observation_entry"})
            continue

        rec_lineage = rec.get("lineage") if isinstance(rec.get("lineage"), dict) else {}
        prep_lineage = prep.get("lineage") if isinstance(prep.get("lineage"), dict) else {}

        lineage = {
            "recommendation_id": rec.get("recommendation_id"),
            "rollback_id": rec.get("rollback_id"),
            "observation_id": prep.get("observation_id"),
            "execution_id": prep.get("execution_id"),
            "rollback_hash": rec_lineage.get("rollback_hash") or _sha(prep),
            "observation_hash": rec_lineage.get("observation_hash") or prep_lineage.get("observation_hash") or _sha(obs),
            "execution_hash": rec_lineage.get("execution_hash") or prep_lineage.get("execution_hash") or (obs.get("lineage", {}) if isinstance(obs.get("lineage"), dict) else {}).get("execution_hash"),
        }

        review_obj = {"reviewer_notes": [], "approval_status": "unreviewed", "decision_reason": None}
        packet_base = {
            "packet_version": "CanaryRollbackPacket.v1",
            "rollback_id": rec.get("rollback_id"),
            "observation_id": prep.get("observation_id"),
            "execution_id": prep.get("execution_id"),
            "source_key": rec.get("source_key"),
            "recommendation_status": "recommend_approve_for_rollback_review",
            "rollback_plan": prep.get("rollback_plan"),
            "safety": prep.get("safety"),
            "evidence": {
                "rollback_status": prep.get("status"),
                "review_reason": rec.get("basis", {}).get("reason") if isinstance(rec.get("basis"), dict) else None,
            },
            "lineage": lineage,
            "review": review_obj,
            "authority": dict(AUTHORITY_FLAGS),
        }
        packet_id = _sha(packet_base)
        packets.append({
            **packet_base,
            "packet_id": packet_id,
            "packet_status": "pending_review",
        })

    packets = sorted(packets, key=lambda p: (p["source_key"], p["packet_id"]))
    skipped = sorted(skipped, key=lambda s: (str(s.get("source_key") or ""), str(s.get("rollback_id") or ""), str(s.get("reason") or "")))

    return {
        "artifact": "CANARY-ROLLBACK-PACKET-001",
        "schema_version": "CanaryRollbackPacketRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": {
            "recommendations_total": len(reviews),
            "packets_created": len(packets),
            "skipped": len(skipped),
        },
        "packets": packets,
        "skipped_recommendations": skipped,
    }
