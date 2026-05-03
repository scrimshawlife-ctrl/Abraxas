from __future__ import annotations

import hashlib
import json
from pathlib import Path

h = lambda v: hashlib.sha256(v.encode()).hexdigest()
c = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":"))
REQ = [
    ("out/registry/self_build_evolution_summary.latest.json", "SelfBuildEvolutionSummary.v1"),
    ("out/registry/self_build_readiness_gate.latest.json", "SelfBuildReadinessGate.v1"),
    ("out/registry/self_build_auto_loop_plan.latest.json", "SelfBuildAutoLoopPlan.v1"),
    ("out/registry/self_build_operator_action_recommendations.latest.json", "SelfBuildOperatorActionRecommendations.v1"),
    ("out/registry/self_build_batch_cycle.latest.json", "SelfBuildBatchCycle.v1"),
]


def _lineage_summary() -> dict:
    p = Path("out/semantic/semantic_lineage_report.latest.json")
    if not p.exists():
        return {"status": "NOT_COMPUTABLE", "warning_count": 0, "missing_envelope_count": 0, "broken_parent_reference_count": 0, "orphan_contract_count": 0, "canonical_hash": None}
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "NOT_COMPUTABLE", "warning_count": 0, "missing_envelope_count": 0, "broken_parent_reference_count": 0, "orphan_contract_count": 0, "canonical_hash": None}
    warnings = j.get("warnings", []) if isinstance(j.get("warnings"), list) else []
    return {
        "status": j.get("status", "NOT_COMPUTABLE"),
        "warning_count": len(warnings),
        "missing_envelope_count": sum(1 for w in warnings if str(w).startswith("missing_envelope:")),
        "broken_parent_reference_count": sum(1 for w in warnings if str(w).startswith("broken_parent_reference:")),
        "orphan_contract_count": sum(1 for w in warnings if str(w).startswith("orphan_contract:")),
        "canonical_hash": j.get("canonical_hash"),
    }


def _policy_trends_summary() -> dict:
    p = Path("out/registry/readiness_policy_trends.latest.json")
    if not p.exists():
        return {"status": "NOT_COMPUTABLE", "active_policy_hash": None, "policy_hash_change_count": 0, "persistent_blockers": [], "readiness_status_drift_under_same_policy": [], "canonical_hash": None}
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "NOT_COMPUTABLE", "active_policy_hash": None, "policy_hash_change_count": 0, "persistent_blockers": [], "readiness_status_drift_under_same_policy": [], "canonical_hash": None}
    return {
        "status": j.get("status", "NOT_COMPUTABLE"),
        "active_policy_hash": j.get("policy_vs_state_causality", {}).get("status_variants_by_policy", {}) and sorted(j.get("policy_vs_state_causality", {}).get("status_variants_by_policy", {}).keys())[-1],
        "policy_hash_change_count": j.get("policy_hash_changes", 0),
        "persistent_blockers": j.get("persistent_blockers", []),
        "readiness_status_drift_under_same_policy": j.get("readiness_status_drift_under_same_policy", []),
        "canonical_hash": j.get("canonical_hash"),
    }


def _decision_summary(readiness: dict, recs: list[dict], lineage: dict, trends: dict, rec_hash: str | None) -> dict:
    readiness_status = readiness.get("status")
    blockers = readiness.get("blockers", []) if isinstance(readiness.get("blockers"), list) else []
    approval_only = blockers == ["approval_pending"] or blockers == []
    top_action = recs[0].get("action_type") if recs else None

    decision_state = "HOLD"
    reason = "Readiness and trend context unavailable"
    blocking_domains: list[str] = []

    if readiness_status in {"NOT_READY", "NOT_COMPUTABLE"}:
        decision_state = "INVESTIGATE" if blockers else "HOLD"
        reason = "Readiness gate blocked or not computable"
        blocking_domains.extend([str(b) for b in blockers])
    elif readiness_status == "WAITING_FOR_APPROVAL" and top_action == "APPROVE_ONE" and approval_only:
        decision_state = "APPROVE_ONE"
        reason = "Approval pending and top recommendation is APPROVE_ONE"
    elif readiness_status == "READY_FOR_GUARDED_LOOP" and not blockers:
        decision_state = "RUN_BATCH"
        reason = "Readiness clear with no blockers"

    if (lineage.get("warning_count", 0) > 0 or len(trends.get("persistent_blockers", [])) > 0) and not (readiness_status == "WAITING_FOR_APPROVAL" and approval_only):
        decision_state = "INVESTIGATE"
        reason = "Lineage warnings or persistent policy blockers require investigation"
        if lineage.get("warning_count", 0) > 0:
            blocking_domains.append("lineage")
        if len(trends.get("persistent_blockers", [])) > 0:
            blocking_domains.append("policy_trends")

    if decision_state == "NOT_COMPUTABLE":
        confidence = 0.0
    elif decision_state == "RUN_BATCH":
        confidence = 0.9
    elif decision_state == "APPROVE_ONE":
        confidence = 0.8
    elif decision_state == "INVESTIGATE":
        confidence = 0.35
    else:
        confidence = 0.5

    suggested_command = None
    if recs and recs[0].get("action_id"):
        suggested_command = f"python scripts/run_self_build_recommendation_executor.py {recs[0]['action_id']}"

    return {
        "decision_state": decision_state,
        "reason": reason,
        "confidence": confidence,
        "blocking_domains": sorted(set(blocking_domains)),
        "suggested_command": suggested_command,
        "source_hashes": {
            "readiness_hash": readiness.get("canonical_hash"),
            "recommendation_hash": rec_hash,
            "lineage_hash": lineage.get("canonical_hash"),
            "policy_trends_hash": trends.get("canonical_hash"),
        },
    }


def run_self_build_operator_packet():
    d = {}
    for p, s in REQ:
        P = Path(p)
        if not P.exists():
            x = {"schema_version": "SelfBuildOperatorPacket.v1", "status": "NOT_COMPUTABLE", "authority": {"mutation": False, "promotion": False, "execution": False, "operator_display_only": True}}
            x["canonical_hash"] = h(c(x))
            return x
        j = json.loads(P.read_text())
        if j.get("schema_version") != s:
            x = {"schema_version": "SelfBuildOperatorPacket.v1", "status": "NOT_COMPUTABLE", "authority": {"mutation": False, "promotion": False, "execution": False, "operator_display_only": True}}
            x["canonical_hash"] = h(c(x))
            return x
        d[p] = j
    recs = d[REQ[3][0]].get("actions", [])
    lineage = _lineage_summary()
    trends = _policy_trends_summary()
    recommendation_hash = h(c(recs)) if isinstance(recs, list) else None
    decision = _decision_summary(d[REQ[1][0]], recs, lineage, trends, recommendation_hash)

    x = {
        "schema_version": "SelfBuildOperatorPacket.v1",
        "status": "PACKET_READY",
        "headline_state": d[REQ[4][0]].get("status"),
        "recommended_next_action": (recs[0]["action_type"] if recs else "NONE"),
        "top_recommendations": recs[:3],
        "readiness_status": d[REQ[1][0]].get("status"),
        "approval_state": d[REQ[0][0]].get("posture", {}).get("approval_state"),
        "risks": d[REQ[0][0]].get("risks", []),
        "artifact_pointers": [p for p, _ in REQ] + ["out/semantic/semantic_lineage_report.latest.json", "out/registry/readiness_policy_trends.latest.json"],
        "semantic_lineage": lineage,
        "readiness_policy_hash": d[REQ[1][0]].get("policy_hash"),
        "readiness_policy_trends": trends,
        "operator_decision_summary": decision,
        "authority": {"mutation": False, "promotion": False, "execution": False, "operator_display_only": True},
    }
    x["canonical_hash"] = h(c(x))
    return x
