from __future__ import annotations

from abx.operator.interventionClassification import classify_intervention_kind, classify_intervention_legitimacy
from abx.operator.manualInterventionRecords import build_manual_intervention_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_intervention_report() -> dict[str, object]:
    records = build_manual_intervention_records()
    kind_states = {x.intervention_id: classify_intervention_kind(x) for x in records}
    legitimacy = {x.intervention_id: classify_intervention_legitimacy(x) for x in records}
    report = {
        "artifactType": "ManualInterventionAudit.v1",
        "artifactId": "manual-intervention-audit",
        "interventions": [x.__dict__ for x in records],
        "interventionKinds": kind_states,
        "interventionLegitimacy": legitimacy,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
