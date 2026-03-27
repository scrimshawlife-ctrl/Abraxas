from __future__ import annotations

from abx.failure.errorClassification import classify_error
from abx.failure.errorTaxonomyRecords import build_error_taxonomy_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_error_taxonomy_report() -> dict[str, object]:
    rows = build_error_taxonomy_records()
    states = {x.error_id: classify_error(failure_class=x.failure_class, severity=x.severity) for x in rows}
    report = {
        "artifactType": "ErrorTaxonomyAudit.v1",
        "artifactId": "error-taxonomy-audit",
        "errors": [x.__dict__ for x in rows],
        "errorStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
