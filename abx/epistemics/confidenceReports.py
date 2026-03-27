from __future__ import annotations

from abx.epistemics.calibrationRecords import build_calibration_records
from abx.epistemics.confidenceClassification import (
    build_confidence_classification_records,
    classify_confidence_states,
    detect_unsupported_confidence_drift,
)
from abx.epistemics.uncertaintyVocabulary import build_uncertainty_vocabulary
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_calibration_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "CalibrationAudit.v1",
        "artifactId": "calibration-audit",
        "calibrationRecords": [x.__dict__ for x in build_calibration_records()],
        "confidenceClassification": [x.__dict__ for x in build_confidence_classification_records()],
        "confidenceStates": classify_confidence_states(),
        "uncertaintyVocabulary": build_uncertainty_vocabulary(),
        "unsupportedConfidence": detect_unsupported_confidence_drift(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
