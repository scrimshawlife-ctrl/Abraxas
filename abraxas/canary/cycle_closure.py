from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.closure_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _r6(x: float) -> float:
    return round(float(x), 6)


def build_cycle_closure_report(
    forward_observations: Mapping[str, Any],
    rollback_observations: Mapping[str, Any],
    forward_executions: Mapping[str, Any],
    rollback_executions: Mapping[str, Any],
) -> dict:
    fo = deepcopy(dict(forward_observations))
    ro = deepcopy(dict(rollback_observations))
    fe = deepcopy(dict(forward_executions))
    re = deepcopy(dict(rollback_executions))

    fe_list = fe.get("executions") if isinstance(fe.get("executions"), list) else []
    re_list = re.get("executions") if isinstance(re.get("executions"), list) else []
    fo_list = fo.get("entries") if isinstance(fo.get("entries"), list) else []
    ro_list = ro.get("observations") if isinstance(ro.get("observations"), list) else []

    counts = {
        "forward_executions_total": len(fe_list),
        "forward_observations_total": len(fo_list),
        "rollback_executions_total": len(re_list),
        "rollback_observations_total": len(ro_list),
        "forward_completed": sum(1 for x in fe_list if isinstance(x, dict) and x.get("execution_status") == "completed"),
        "rollback_completed": sum(1 for x in re_list if isinstance(x, dict) and x.get("execution_status") == "completed"),
        "forward_failed": sum(1 for x in fe_list if isinstance(x, dict) and x.get("execution_status") == "failed"),
        "rollback_failed": sum(1 for x in re_list if isinstance(x, dict) and x.get("execution_status") == "failed"),
        "forward_blocked": sum(1 for x in fe_list if isinstance(x, dict) and x.get("execution_status") == "blocked"),
        "rollback_blocked": sum(1 for x in re_list if isinstance(x, dict) and x.get("execution_status") == "blocked"),
    }

    f_cov = 0.0 if counts["forward_executions_total"] == 0 else _r6(counts["forward_observations_total"] / counts["forward_executions_total"])
    r_cov = 0.0 if counts["rollback_executions_total"] == 0 else _r6(counts["rollback_observations_total"] / counts["rollback_executions_total"])

    if f_cov >= 1.0 and r_cov >= 1.0:
        sym = "complete"
    elif f_cov < 1.0 and r_cov >= 1.0:
        sym = "forward_missing_observations"
    elif f_cov >= 1.0 and r_cov < 1.0:
        sym = "rollback_missing_observations"
    else:
        sym = "both_missing_observations"

    symmetry = {
        "forward_observation_coverage": f_cov,
        "rollback_observation_coverage": r_cov,
        "observation_symmetry_status": sym,
    }

    rollback_ready_count = sum(1 for x in fo_list if isinstance(x, dict) and isinstance(x.get("rollback"), dict) and x["rollback"].get("rollback_key") is not None)
    rollback_replayable_count = sum(1 for x in fo_list if isinstance(x, dict) and isinstance(x.get("replay"), dict) and x["replay"].get("replayable") is True)
    rollback_observed_count = counts["rollback_observations_total"]

    if rollback_ready_count > 0 and rollback_replayable_count > 0 and rollback_observed_count > 0:
        rev_status = "ready"
    elif rollback_ready_count > 0 or rollback_replayable_count > 0 or rollback_observed_count > 0:
        rev_status = "partial"
    else:
        rev_status = "not_ready"

    reversibility = {
        "rollback_ready_count": rollback_ready_count,
        "rollback_replayable_count": rollback_replayable_count,
        "rollback_observed_count": rollback_observed_count,
        "reversibility_status": rev_status,
    }

    if counts["forward_executions_total"] == 0 and counts["rollback_executions_total"] == 0:
        closure = {"closure_status": "not_computable", "reason": "no_executions"}
    elif sym == "complete" and rev_status == "ready":
        closure = {"closure_status": "closed", "reason": "forward_and_rollback_observed_with_reversibility_ready"}
    else:
        closure = {"closure_status": "open", "reason": "cycle_incomplete"}

    lineage = {
        "forward_execution_hash": _sha(fe),
        "forward_observation_hash": _sha(fo),
        "rollback_execution_hash": _sha(re),
        "rollback_observation_hash": _sha(ro),
    }

    core = {
        "artifact": "CANARY-CYCLE-CLOSURE-REPORT-001",
        "schema_version": "CanaryCycleClosureReport.v1",
        "counts": counts,
        "symmetry": symmetry,
        "reversibility": reversibility,
        "closure": closure,
        "lineage": lineage,
        "authority": dict(AUTHORITY_FLAGS),
    }
    report_id = _sha(core)
    report = {**core, "report_id": report_id}
    report_hash = _sha(report)
    report["report_hash"] = report_hash
    return report
