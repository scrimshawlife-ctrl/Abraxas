from __future__ import annotations

from abx.innovation.experimentConditions import build_experiment_conditions
from abx.innovation.hypothesisRecords import build_hypothesis_records
from abx.innovation.outcomeClassification import build_experiment_outcomes, classify_outcome_comparability
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_research_artifact_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "ResearchArtifactAudit.v1",
        "artifactId": "research-artifact-audit",
        "hypotheses": [x.__dict__ for x in build_hypothesis_records()],
        "conditions": [x.__dict__ for x in build_experiment_conditions()],
        "outcomes": [x.__dict__ for x in build_experiment_outcomes()],
        "comparability": classify_outcome_comparability(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
