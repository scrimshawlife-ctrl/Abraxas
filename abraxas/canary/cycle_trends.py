from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.trend_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _r6(x: float) -> float:
    return round(float(x), 6)


def build_cycle_trend_analysis(ledger_run: Mapping[str, Any]) -> dict:
    ledger = deepcopy(dict(ledger_run))
    entries = ledger.get("entries") if isinstance(ledger.get("entries"), list) else []
    total = len(entries)

    closed = sum(1 for e in entries if isinstance(e, dict) and e.get("closure_status") == "closed")
    open_ = sum(1 for e in entries if isinstance(e, dict) and e.get("closure_status") == "open")
    not_comp = sum(1 for e in entries if isinstance(e, dict) and e.get("closure_status") == "not_computable")

    complete_count = sum(1 for e in entries if isinstance(e, dict) and e.get("observation_symmetry_status") == "complete")
    incomplete_count = total - complete_count

    ready_count = sum(1 for e in entries if isinstance(e, dict) and e.get("reversibility_status") == "ready")
    partial_count = sum(1 for e in entries if isinstance(e, dict) and e.get("reversibility_status") == "partial")
    not_ready_count = sum(1 for e in entries if isinstance(e, dict) and e.get("reversibility_status") == "not_ready")

    if total == 0:
        rates = {"closure_rate": 0.0, "open_rate": 0.0, "not_computable_rate": 0.0}
        symmetry = {"complete_count": 0, "incomplete_count": 0, "complete_rate": 0.0}
        reversibility = {"ready_count": 0, "partial_count": 0, "not_ready_count": 0, "ready_rate": 0.0}
        trend = {"status": "not_computable", "reason": "no_cycles"}
        recommendations = ["collect_cycle_closure_data"]
    else:
        closure_rate = _r6(closed / total)
        open_rate = _r6(open_ / total)
        not_comp_rate = _r6(not_comp / total)
        complete_rate = _r6(complete_count / total)
        ready_rate = _r6(ready_count / total)

        rates = {"closure_rate": closure_rate, "open_rate": open_rate, "not_computable_rate": not_comp_rate}
        symmetry = {"complete_count": complete_count, "incomplete_count": incomplete_count, "complete_rate": complete_rate}
        reversibility = {
            "ready_count": ready_count,
            "partial_count": partial_count,
            "not_ready_count": not_ready_count,
            "ready_rate": ready_rate,
        }

        if closure_rate >= 0.8 and complete_rate >= 0.8 and ready_rate >= 0.8:
            trend = {"status": "stable", "reason": "closure_symmetry_and_reversibility_above_threshold"}
            recommendations = ["continue_shadow_observation"]
        else:
            trend = {"status": "needs_attention", "reason": "closure_symmetry_or_reversibility_below_threshold"}
            recs = []
            if closure_rate < 0.8:
                recs.append("increase_cycle_closure_rate")
            if complete_rate < 0.8:
                recs.append("improve_observation_symmetry")
            if ready_rate < 0.8:
                recs.append("improve_reversibility_readiness")
            recommendations = sorted(recs)

    counts = {
        "cycles_total": total,
        "closed": closed,
        "open": open_,
        "not_computable": not_comp,
    }

    lineage = {"closure_ledger_hash": _sha(ledger)}

    core = {
        "artifact": "CANARY-CYCLE-TREND-ANALYSIS-001",
        "schema_version": "CanaryCycleTrendAnalysis.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": counts,
        "rates": rates,
        "symmetry": symmetry,
        "reversibility": reversibility,
        "trend": trend,
        "recommendations": recommendations,
        "lineage": lineage,
    }
    analysis_id = _sha(core)
    report = {**core, "analysis_id": analysis_id}
    report_hash = _sha(report)
    report["analysis_hash"] = report_hash
    return report
