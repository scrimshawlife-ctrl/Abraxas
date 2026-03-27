from __future__ import annotations

from abx.evidence.conflictingEvidence import build_conflicting_evidence_records
from abx.evidence.evidenceTransitions import build_evidence_transition_records
from abx.evidence.provisionalDecisions import build_provisional_decision_records, build_unmet_burden_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_evidence_transition_report() -> dict[str, object]:
    transitions = build_evidence_transition_records()
    conflicts = build_conflicting_evidence_records()
    provisional = build_provisional_decision_records()
    unmet = build_unmet_burden_records()
    report = {
        "artifactType": "EvidenceTransitionAudit.v1",
        "artifactId": "evidence-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "conflicts": [x.__dict__ for x in conflicts],
        "provisional": [x.__dict__ for x in provisional],
        "unmetBurden": [x.__dict__ for x in unmet],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
