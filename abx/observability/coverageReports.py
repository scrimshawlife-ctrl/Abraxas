from __future__ import annotations

from abx.observability.coverageClassification import classify_coverage
from abx.observability.coverageRecords import build_coverage_records
from abx.observability.types import CoverageGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_observability_coverage_report() -> dict[str, object]:
    rows = build_coverage_records()
    states = {x.coverage_id: classify_coverage(coverage_state=x.coverage_state) for x in rows}
    errors = []
    for row in rows:
        state = states[row.coverage_id]
        if state in {"NO_MEANINGFUL_COVERAGE", "NOT_COMPUTABLE"}:
            errors.append(CoverageGovernanceErrorRecord("COVERAGE_BLOCKING", "ERROR", f"{row.surface_ref} state={state}"))
        elif state in {"COVERAGE_PARTIAL", "COVERAGE_DEGRADED", "COVERAGE_UNKNOWN"}:
            errors.append(CoverageGovernanceErrorRecord("COVERAGE_ATTENTION", "WARN", f"{row.surface_ref} state={state}"))
    report = {
        "artifactType": "ObservabilityCoverageAudit.v1",
        "artifactId": "observability-coverage-audit",
        "coverage": [x.__dict__ for x in rows],
        "coverageStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
