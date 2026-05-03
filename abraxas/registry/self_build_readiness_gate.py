from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

REQ = {
    "evolution": ("out/registry/self_build_evolution_summary.latest.json", "SelfBuildEvolutionSummary.v1"),
    "cycle": ("out/registry/self_build_batch_cycle.latest.json", "SelfBuildBatchCycle.v1"),
    "trends": ("out/registry/self_build_batch_trends.latest.json", "SelfBuildBatchTrends.v1"),
    "recs": ("out/registry/self_build_operator_action_recommendations.latest.json", "SelfBuildOperatorActionRecommendations.v1"),
    "feedback": ("out/registry/self_build_score_feedback.latest.json", "SelfBuildScoreFeedback.v1"),
    "card": ("out/operator/operator_closure_card.latest.json", "OperatorClosureCard.v1"),
    "validator": ("out/registry/binding_validator_run.latest.json", "BindingValidatorRun.v1"),
}
LINEAGE_PATH = Path("out/semantic/semantic_lineage_report.latest.json")
LINEAGE_SCHEMA = "SemanticLineageReport.v1"
POLICY_PATH = Path(".aal/readiness_policy.v1.yaml")

h = lambda v: hashlib.sha256(v.encode()).hexdigest()
c = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":"))


def _policy_hash(policy: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fail(r):
    p = {"schema_version": "SelfBuildReadinessGate.v1", "status": "NOT_COMPUTABLE", "blockers": [r], "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True}}
    p["canonical_hash"] = h(c(p))
    return p


def _load_policy() -> dict[str, Any] | None:
    if not POLICY_PATH.exists():
        return None
    raw = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != "ReadinessPolicy.v1":
        return None
    if not isinstance(raw.get("lineage_warning_threshold"), int) or raw["lineage_warning_threshold"] < 0:
        return None
    for k in ["require_lineage_report", "require_operator_green", "require_validator_pass", "require_feedback_available", "require_recommendations_available", "mutation_path_must_be_gated"]:
        if not isinstance(raw.get(k), bool):
            return None
    return raw


def _load_lineage() -> dict[str, Any] | None:
    if not LINEAGE_PATH.exists():
        return None
    j = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))
    if not isinstance(j, dict) or j.get("schema_version") != LINEAGE_SCHEMA:
        return {"invalid": True}
    return j


def run_self_build_readiness_gate() -> dict[str, Any]:
    policy = _load_policy()
    if policy is None:
        return fail("INVALID_POLICY_CONFIG")

    d = {}
    for k, (p, s) in REQ.items():
        P = Path(p)
        if not P.exists():
            return fail(f"MISSING:{k}")
        j = json.loads(P.read_text())
        if not isinstance(j, dict) or j.get("schema_version") != s:
            return fail(f"INVALID:{k}")
        d[k] = j

    lineage = _load_lineage()
    lineage_missing = lineage is None
    lineage_invalid = isinstance(lineage, dict) and lineage.get("invalid") is True
    lineage_status = lineage.get("status") if isinstance(lineage, dict) else None
    lineage_warnings = lineage.get("warnings", []) if isinstance(lineage, dict) and isinstance(lineage.get("warnings"), list) else []
    broken_parent_count = sum(1 for w in lineage_warnings if str(w).startswith("broken_parent_reference:"))

    gates = {
        "require_validator_pass": d["validator"].get("overall_status") == "PASS",
        "require_operator_green": d["card"].get("health") == "GREEN",
        "trends_available": d["trends"].get("status") == "OK",
        "require_recommendations_available": d["recs"].get("status") == "OK",
        "require_feedback_available": d["feedback"].get("status") == "OK",
        "approval_pending": d["cycle"].get("status") == "WAITING_FOR_APPROVAL",
        "mutation_path_must_be_gated": True,
        "require_lineage_report": not lineage_missing and not lineage_invalid,
        "lineage_status_ready": lineage_status == "LINEAGE_REPORT_READY",
        "lineage_no_broken_links": broken_parent_count == 0,
        "lineage_warning_count_below_threshold": len(lineage_warnings) <= policy["lineage_warning_threshold"],
    }

    policy_required = {
        "require_validator_pass": policy["require_validator_pass"],
        "require_operator_green": policy["require_operator_green"],
        "require_recommendations_available": policy["require_recommendations_available"],
        "require_feedback_available": policy["require_feedback_available"],
        "mutation_path_must_be_gated": policy["mutation_path_must_be_gated"],
        "require_lineage_report": policy["require_lineage_report"],
    }

    blockers = [name for name, required in policy_required.items() if required and not gates.get(name, False)]
    if not gates["lineage_status_ready"]:
        blockers.append("lineage_status_ready")
    if not gates["lineage_no_broken_links"]:
        blockers.append("lineage_no_broken_links")
    if not gates["lineage_warning_count_below_threshold"]:
        blockers.append("lineage_warning_count_below_threshold")
    if lineage_missing:
        blockers.append("require_lineage_report")
    if lineage_invalid:
        blockers.append("lineage_status_ready")

    status = "READY_FOR_GUARDED_LOOP"
    if gates["approval_pending"] and len(set(blockers)) == 0:
        status = "WAITING_FOR_APPROVAL"
    elif blockers:
        status = "NOT_READY"

    p = {"schema_version": "SelfBuildReadinessGate.v1", "status": status, "gates": gates, "blockers": sorted(set(blockers)), "policy": policy, "policy_path": POLICY_PATH.as_posix(), "policy_schema_version": policy.get("schema_version"), "policy_hash": _policy_hash(policy), "policy_fields_used": sorted(["schema_version", "lineage_warning_threshold", "require_lineage_report", "require_operator_green", "require_validator_pass", "require_feedback_available", "require_recommendations_available", "mutation_path_must_be_gated"]), "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True}}
    p["canonical_hash"] = h(c(p))
    return p
