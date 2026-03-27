from __future__ import annotations

from abx.uncertainty.confidenceExpressionClassification import classify_confidence_expression
from abx.uncertainty.confidenceExpressionRecords import build_confidence_expression_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_confidence_expression_report() -> dict[str, object]:
    rows = build_confidence_expression_records()
    states = {row.expression_id: classify_confidence_expression(row.expression_mode) for row in rows}
    report = {
        "artifactType": "ConfidenceExpressionAudit.v1",
        "artifactId": "confidence-expression-audit",
        "expressions": [x.__dict__ for x in rows],
        "expressionStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
