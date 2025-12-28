from __future__ import annotations

from typing import Any, Dict, List


def route_mode_v2(inp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Priority order:
      1) user override
      2) compliance RED -> ANALYST
      3) high uncertainty/risk/negative signals -> ANALYST
      4) else SNAPSHOT

    RITUAL is never auto-selected (only via user override).
    """
    cfg = inp["config_hash"]

    req = inp.get("user_mode_request")
    if req:
        return {
            "mode": req,
            "reasons": ["USER_OVERRIDE"],
            "tags": {"state": "INFERRED", "confidence": 1.0},
            "provenance": {"config_hash": cfg},
        }

    if inp["compliance_status"] == "RED":
        return {
            "mode": "ANALYST",
            "reasons": ["COMPLIANCE_RED"],
            "tags": {"state": "INFERRED", "confidence": 0.95},
            "provenance": {"config_hash": cfg},
        }

    BW_HIGH = inp["thresholds"]["BW_HIGH"]
    MRS_HIGH = inp["thresholds"]["MRS_HIGH"]

    reasons: List[str] = []
    if inp["max_band_width"] >= BW_HIGH:
        reasons.append("UNCERTAINTY_HIGH")
    if inp["max_MRS"] >= MRS_HIGH:
        reasons.append("RISK_HIGH")
    if inp["negative_signal_alerts"] >= 1:
        reasons.append("NEGATIVE_SIGNAL")

    if reasons:
        return {
            "mode": "ANALYST",
            "reasons": reasons[:10],
            "tags": {"state": "INFERRED", "confidence": 0.9},
            "provenance": {"config_hash": cfg},
        }

    return {
        "mode": "SNAPSHOT",
        "reasons": ["DEFAULT"],
        "tags": {"state": "INFERRED", "confidence": 0.9},
        "provenance": {"config_hash": cfg},
    }
