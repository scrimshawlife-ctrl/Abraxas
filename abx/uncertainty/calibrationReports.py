from __future__ import annotations

from abx.uncertainty.calibrationClassification import classify_calibration
from abx.uncertainty.calibrationValidityRecords import build_calibration_validity_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_calibration_report() -> dict[str, object]:
    rows = build_calibration_validity_records()
    states = {row.calibration_id: classify_calibration(row.calibration_state) for row in rows}
    report = {
        "artifactType": "CalibrationValidityAudit.v1",
        "artifactId": "calibration-validity-audit",
        "calibration": [x.__dict__ for x in rows],
        "calibrationStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
