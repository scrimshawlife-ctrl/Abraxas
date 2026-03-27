from __future__ import annotations

from abx.epistemics.qualityClassification import (
    build_epistemic_quality_records,
    classify_epistemic_quality_states,
    detect_inconsistent_quality_terminology,
)
from abx.epistemics.qualityCoverage import build_epistemic_coverage
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_epistemic_quality_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "EpistemicQualityAudit.v1",
        "artifactId": "epistemic-quality-audit",
        "qualityRecords": [x.__dict__ for x in build_epistemic_quality_records()],
        "qualityClassification": classify_epistemic_quality_states(),
        "coverage": [x.__dict__ for x in build_epistemic_coverage()],
        "inconsistentTerminology": detect_inconsistent_quality_terminology(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
