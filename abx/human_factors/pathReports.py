from __future__ import annotations

from abx.human_factors.operatorPaths import build_operator_paths
from abx.human_factors.pathClassification import classify_operator_paths
from abx.human_factors.pathTransitions import build_path_transitions
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_operator_path_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "OperatorPathAudit.v1",
        "artifactId": "operator-path-audit",
        "paths": [x.__dict__ for x in build_operator_paths()],
        "classification": classify_operator_paths(),
        "transitions": build_path_transitions(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
