from __future__ import annotations

from abx.observability.types import ObservabilityErrorRecord


ERRORS = {
    "OBS_MISSING_SURFACE": "HIGH",
    "OBS_REDUNDANT_SURFACE": "MEDIUM",
    "OBS_EXPLAIN_GAP": "MEDIUM",
    "OBS_TRACE_GAP": "MEDIUM",
}


def make_observability_error(code: str, message: str) -> ObservabilityErrorRecord:
    return ObservabilityErrorRecord(code=code, severity=ERRORS.get(code, "MEDIUM"), message=message)
