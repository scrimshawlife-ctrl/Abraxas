from __future__ import annotations

from typing import Any, Dict, Tuple


DEFAULT_THRESHOLDS = {"BW_HIGH": 20.0, "MRS_HIGH": 70.0}


def collect_v2_checks(
    *,
    v1_golden_pass_rate: float = 1.0,
    drift_budget_violations: int = 0,
    evidence_bundle_overflow_rate: float = 0.0,
    ci_volatility_correlation: float = 1.0,
    interaction_noise_rate: float = 0.0,
) -> Dict[str, Any]:
    """
    Deterministic checks collector.

    Economy: until wired to real telemetry, we default to "safe green"
    *without fabricating evidence* about external sources.

    You can later patch this to pull real values from your internal test/telemetry hooks
    without changing downstream schemas.
    """
    # Clamp conservatively to schema bounds
    v1 = max(0.0, min(1.0, float(v1_golden_pass_rate)))
    drift = max(0, int(drift_budget_violations))
    overflow = max(0.0, min(1.0, float(evidence_bundle_overflow_rate)))
    ci_corr = max(0.0, min(1.0, float(ci_volatility_correlation)))
    noise = max(0.0, min(1.0, float(interaction_noise_rate)))

    return {
        "v1_golden_pass_rate": v1,
        "drift_budget_violations": drift,
        "evidence_bundle_overflow_rate": overflow,
        "ci_volatility_correlation": ci_corr,
        "interaction_noise_rate": noise,
    }


def _max_band_width_from_v2_items(v2_slang_items: Any) -> float:
    """
    Looks for v2 CI band widths if present:
      item["ci"]["SVS"]["band_width"] (preferred)
    Returns 0.0 if not available.
    """
    if not isinstance(v2_slang_items, list):
        return 0.0
    bw = 0.0
    for it in v2_slang_items:
        try:
            v = float(it["ci"]["SVS"]["band_width"])
            if v > bw:
                bw = v
        except Exception:
            continue
    return bw


def _max_MRS_from_v1(v1_scores: Dict[str, Any]) -> float:
    """
    Attempts to derive max memetic risk score from v1 if present.
    Expects v1 slang risk entries like: scores_v1["slang"]["top_risk"][i]["MRS"]
    Returns 0.0 if not available.
    """
    try:
        risks = v1_scores.get("slang", {}).get("top_risk", [])
        if not isinstance(risks, list):
            return 0.0
        m = 0.0
        for r in risks:
            v = float(r.get("MRS", 0.0))
            if v > m:
                m = v
        return m
    except Exception:
        return 0.0


def _neg_signal_count_from_v2(v2_aalmanac: Dict[str, Any]) -> int:
    """
    Counts negative signals if present:
      v2_aalmanac["negative_signals"]["signals"] where signal_type == "NEGATIVE" and confidence >= 0.6
    Returns 0 if not available.
    """
    try:
        ns = v2_aalmanac.get("negative_signals", {}).get("signals", [])
        if not isinstance(ns, list):
            return 0
        c = 0
        for s in ns:
            if s.get("signal_type") == "NEGATIVE" and float(s.get("confidence", 0.0)) >= 0.6:
                c += 1
        return c
    except Exception:
        return 0


def derive_router_input_from_envelope(
    *,
    envelope: Dict[str, Any],
    thresholds: Dict[str, float] | None = None,
    user_mode_request: str | None = None,
) -> Dict[str, Any]:
    """
    Extracts router inputs from whatever is available in the envelope.
    Economy: if v2 CI bands / negative signals aren't wired yet, returns safe defaults.
    """
    th = dict(DEFAULT_THRESHOLDS if thresholds is None else thresholds)

    v1_scores = envelope.get("oracle_signal", {}).get("scores_v1", {}) or {}
    v2_block = envelope.get("oracle_signal", {}).get("v2", {}) or {}
    v2_slang_items = v2_block.get("slang", {}).get("items", [])
    v2_aalmanac = v2_block.get("aalmanac", {}) or {}

    max_band_width = _max_band_width_from_v2_items(v2_slang_items)
    max_MRS = _max_MRS_from_v1(v1_scores)
    neg_alerts = _neg_signal_count_from_v2(v2_aalmanac)

    out: Dict[str, Any] = {
        "max_band_width": float(max_band_width),
        "max_MRS": float(max_MRS),
        "negative_signal_alerts": int(neg_alerts),
        "thresholds": {"BW_HIGH": float(th["BW_HIGH"]), "MRS_HIGH": float(th["MRS_HIGH"])},
    }
    if user_mode_request:
        out["user_mode_request"] = user_mode_request
    return out
