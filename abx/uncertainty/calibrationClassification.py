from __future__ import annotations


def classify_calibration(state: str) -> str:
    allowed = {
        "CALIBRATED",
        "PROVISIONALLY_CALIBRATED",
        "PARTIALLY_CALIBRATED",
        "STALE_CALIBRATION",
        "UNCALIBRATED",
        "RECALIBRATION_REQUIRED",
        "BLOCKED_FOR_INVALID_CALIBRATION",
        "NOT_COMPUTABLE",
    }
    return state if state in allowed else "NOT_COMPUTABLE"
