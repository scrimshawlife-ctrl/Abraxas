from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from abx.schemas.calibration_drift_report import CalibrationDriftReport


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_evidence_refs(evidence_refs: Iterable[Any]) -> list[str]:
    refs = sorted({str(item).strip() for item in evidence_refs if str(item).strip()})
    return refs


def build_calibration_report(
    drift_metrics: Mapping[str, Any],
    gate_state: Mapping[str, Any],
    evidence_refs: Sequence[Any],
) -> CalibrationDriftReport:
    drift_class = str(drift_metrics.get("drift_class", "unknown") or "unknown")
    mean_brier = _as_float(drift_metrics.get("mean_brier"), 0.0)
    sample_size = max(0, _as_int(drift_metrics.get("sample_size"), 0))
    not_computable_count = max(0, _as_int(drift_metrics.get("not_computable_count"), 0))

    has_missing = bool(drift_metrics.get("has_missing_inputs", False))
    gate_failure_mode = str(gate_state.get("dominant_failure_mode", "") or "")
    gate_status = str(gate_state.get("promotion_gate_status", "") or str(gate_state.get("status", "") or "")).upper()

    if not isinstance(drift_metrics, Mapping) or sample_size == 0:
        calibration_drift_status = "NOT_COMPUTABLE"
    elif sample_size < 3:
        calibration_drift_status = "REVIEW_REQUIRED"
    elif mean_brier < 0.1:
        calibration_drift_status = "PASS"
    elif mean_brier < 0.25:
        calibration_drift_status = "REVIEW_REQUIRED"
    else:
        calibration_drift_status = "FAIL"

    gate_code = str(gate_state.get("promotion_gate_status", "") or "")
    if not gate_code:
        gate_code = str(gate_state.get("status", "") or "")
    gate_code = gate_code.upper()
    if gate_code in {"PASS", "BLOCKED", "FAIL", "NOT_COMPUTABLE"}:
        promotion_gate_status = gate_code
    else:
        promotion_gate_status = "NOT_COMPUTABLE"

    dominant_failure_mode = str(gate_state.get("dominant_failure_mode", "") or "")
    if not dominant_failure_mode:
        dominant_failure_mode = str(drift_metrics.get("dominant_failure_mode", "") or "")
    if not dominant_failure_mode:
        dominant_failure_mode = (
            "missing_inputs" if has_missing else (f"drift_class:{drift_class}" if drift_class not in {"none", "unknown"} else "none")
        )

    return {
        "schema_version": "CalibrationDriftReport.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mean_brier": mean_brier,
        "sample_size": sample_size,
        "not_computable_count": not_computable_count,
        "calibration_drift_status": calibration_drift_status,
        "promotion_gate_status": promotion_gate_status,
        "dominant_failure_mode": dominant_failure_mode,
        "evidence_refs": _normalize_evidence_refs(evidence_refs),
    }
