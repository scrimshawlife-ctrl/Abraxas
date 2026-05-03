from __future__ import annotations

import hashlib
import json
from pathlib import Path

from abraxas.operator.self_build_operator_packet import run_self_build_operator_packet
from abraxas.registry.self_build_auto_loop_plan import run_self_build_auto_loop_plan
from abraxas.registry.self_build_evolution_summary import run_self_build_evolution_summary
from abraxas.registry.self_build_readiness_gate import run_self_build_readiness_gate

h = lambda v: hashlib.sha256(v.encode()).hexdigest()
c = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":"))




def _load_policy_trends() -> dict:
    p = Path("out/registry/readiness_policy_trends.latest.json")
    if not p.exists():
        return {"status": "NOT_COMPUTABLE", "persistent_blockers": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "NOT_COMPUTABLE", "persistent_blockers": []}

def _load_lineage_report() -> dict:
    p = Path("out/semantic/semantic_lineage_report.latest.json")
    if not p.exists():
        return {"status": "NOT_COMPUTABLE", "warnings": [], "links": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "NOT_COMPUTABLE", "warnings": [], "links": []}


def run_self_build_final_stack_runner():
    s = run_self_build_evolution_summary()
    r = run_self_build_readiness_gate()
    a = run_self_build_auto_loop_plan()
    o = run_self_build_operator_packet()
    lineage = _load_lineage_report()
    trends = _load_policy_trends()

    ok = all(x.get("status") in {"SUMMARY_READY", "WAITING_FOR_APPROVAL", "READY_FOR_GUARDED_LOOP", "NOT_READY", "PLAN_READY", "BLOCKED", "PACKET_READY"} for x in [s, r, a, o]) and o.get("status") == "PACKET_READY"
    broken_link_count = sum(1 for link in lineage.get("links", []) if isinstance(link, dict) and link.get("valid") is False)
    p = {
        "schema_version": "SelfBuildFinalStackResult.v1",
        "status": "FINAL_STACK_READY" if ok else "NOT_COMPUTABLE",
        "generated_artifacts": [
            "out/registry/self_build_evolution_summary.latest.json",
            "out/registry/self_build_readiness_gate.latest.json",
            "out/registry/self_build_auto_loop_plan.latest.json",
            "out/operator/self_build_operator_packet.latest.json",
            "out/semantic/semantic_lineage_report.latest.json",
        ],
        "summary_hash": s.get("canonical_hash"),
        "readiness_hash": r.get("canonical_hash"),
        "readiness_policy_hash": r.get("policy_hash"),
        "auto_loop_plan_hash": a.get("canonical_hash"),
        "operator_packet_hash": o.get("canonical_hash"),
        "lineage_report_hash": lineage.get("canonical_hash"),
        "lineage_status": lineage.get("status", "NOT_COMPUTABLE"),
        "lineage_warning_count": len(lineage.get("warnings", [])) if isinstance(lineage.get("warnings", []), list) else 0,
        "lineage_broken_link_count": broken_link_count,
        "policy_trends_hash": trends.get("canonical_hash"),
        "policy_trends_status": trends.get("status", "NOT_COMPUTABLE"),
        "policy_hash_change_count": trends.get("policy_hash_changes", 0),
        "persistent_blocker_count": len(trends.get("persistent_blockers", [])) if isinstance(trends.get("persistent_blockers", []), list) else 0,
        "authority_integrity": True,
        "authority": {"mutation": False, "promotion": False, "execution": False, "final_stack_orchestration_only": True},
    }
    p["canonical_hash"] = h(c(p))
    return p
