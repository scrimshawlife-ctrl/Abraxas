from __future__ import annotations


def run_activation_review(readiness: dict, preview: dict, state: dict) -> dict:
    base = {
        "schema_version": "CalibrationActivationReviewReport.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "ACTIVATION_REVIEW_ONLY",
        "decision": "BLOCK_ACTIVATION_REVIEW",
        "runtime_activation_allowed": False,
        "activation_next_step": "PATCH-022_REQUIRED",
        "review_summary": {
            "baseline": None,
            "candidate": None,
            "delta": None,
            "improvement": False,
            "multiplier": None,
        },
        "locked": True,
    }

    baseline = preview.get("baseline", {}).get("mean_brier")
    candidate = preview.get("candidate_preview", {}).get("mean_brier")
    delta = preview.get("delta", {}).get("mean_brier_delta")
    improvement = preview.get("delta", {}).get("improvement") is True
    preview_multiplier = preview.get("candidate_preview", {}).get("multiplier")
    state_multiplier = state.get("calibration", {}).get("global_confidence_multiplier")

    checks = [
        readiness.get("status") == "READY",
        preview.get("status") == "PREVIEW_ONLY",
        preview.get("recommendation") == "ELIGIBLE_FOR_ACTIVATION_REVIEW",
        improvement,
        delta is not None and float(delta) < 0,
        candidate is not None and baseline is not None and float(candidate) < float(baseline),
        state.get("runtime_wiring_enabled") is False,
        preview_multiplier == state_multiplier,
    ]

    if not all(checks):
        base["review_summary"] = {
            "baseline": baseline,
            "candidate": candidate,
            "delta": delta,
            "improvement": improvement,
            "multiplier": preview_multiplier,
        }
        return base

    return {
        "schema_version": "CalibrationActivationReviewReport.v1",
        "status": "ACTIVATION_REVIEW_PASSED",
        "authority": "ACTIVATION_REVIEW_ONLY",
        "decision": "ELIGIBLE_FOR_ACTIVATION",
        "runtime_activation_allowed": False,
        "activation_next_step": "PATCH-022_REQUIRED",
        "review_summary": {
            "baseline": baseline,
            "candidate": candidate,
            "delta": delta,
            "improvement": True,
            "multiplier": preview_multiplier,
        },
        "locked": True,
    }
