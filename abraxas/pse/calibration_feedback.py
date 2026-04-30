from __future__ import annotations


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _action_for_reliability(reliability: float) -> str:
    if reliability >= 0.75:
        return "MAINTAIN_CURRENT_CONFIDENCE"
    if reliability >= 0.5:
        return "REVIEW_CALIBRATION"
    return "REDUCE_CONFIDENCE_ADVISORY"


def build_calibration_feedback(brier_ledger: dict, readiness_report: dict) -> dict:
    base = {
        "schema_version": "PSECalibrationFeedback.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "ADVISORY_ONLY",
        "global_reliability": 0.0,
        "domain_reliability": {},
        "source_reliability": {},
        "insufficient_evidence": {},
        "recommended_actions": [],
    }

    if readiness_report.get("status") != "READY":
        return base

    summary = brier_ledger.get("summary", {})
    scored_count = summary.get("scored_count", 0)
    mean_brier = summary.get("mean_brier")
    if scored_count < 3 or mean_brier is None:
        return base

    global_reliability = round(_clamp01(1.0 - float(mean_brier)), 6)

    def convert_group(groups: dict) -> tuple[dict, dict]:
        reliabilities = {}
        insufficient = {}
        for key, data in sorted(groups.items()):
            count = int(data.get("count", 0))
            if count < 2:
                insufficient[key] = "insufficient_evidence"
                continue
            reliabilities[key] = round(_clamp01(1.0 - float(data.get("mean_brier", 1.0))), 6)
        return reliabilities, insufficient

    domain_rel, domain_ins = convert_group(brier_ledger.get("by_domain", {}))
    source_rel, source_ins = convert_group(brier_ledger.get("by_source", {}))

    action = {
        "target": "global",
        "action": _action_for_reliability(global_reliability),
        "advisory_only": True,
        "applied": False,
    }

    return {
        "schema_version": "PSECalibrationFeedback.v1",
        "status": "ADVISORY_ONLY",
        "authority": "ADVISORY_ONLY",
        "global_reliability": global_reliability,
        "domain_reliability": domain_rel,
        "source_reliability": source_rel,
        "insufficient_evidence": {
            "domain": domain_ins,
            "source": source_ins,
        },
        "recommended_actions": [action],
    }
