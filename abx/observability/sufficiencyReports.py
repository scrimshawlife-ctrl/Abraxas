from __future__ import annotations

from abx.observability.measurementSufficiencyRecords import build_measurement_sufficiency_records
from abx.observability.sufficiencyClassification import classify_sufficiency
from abx.observability.types import CoverageGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_measurement_sufficiency_report() -> dict[str, object]:
    rows = build_measurement_sufficiency_records()
    states = {
        x.sufficiency_id: classify_sufficiency(sufficiency_state=x.sufficiency_state, consequence_class=x.consequence_class) for x in rows
    }
    errors = []
    for row in rows:
        state = states[row.sufficiency_id]
        if state in {"INSUFFICIENT_MEASUREMENT", "MEASUREMENT_AMBIGUOUS", "HIGH_CONSEQUENCE_UNDER_OBSERVED", "NOT_COMPUTABLE"}:
            errors.append(CoverageGovernanceErrorRecord("SUFFICIENCY_BLOCKING", "ERROR", f"{row.surface_ref} state={state}"))
        elif state in {"PROVISIONALLY_SUFFICIENT", "LOW_CONSEQUENCE_TOLERABLE_UNDER_MEASUREMENT"}:
            errors.append(CoverageGovernanceErrorRecord("SUFFICIENCY_ATTENTION", "WARN", f"{row.surface_ref} state={state}"))
    report = {
        "artifactType": "MeasurementSufficiencyAudit.v1",
        "artifactId": "measurement-sufficiency-audit",
        "sufficiency": [x.__dict__ for x in rows],
        "sufficiencyStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
