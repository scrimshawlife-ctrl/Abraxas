from __future__ import annotations

from abx.interface.acceptanceRecords import build_acceptance_records, build_interpretation_records
from abx.interface.interpretationClassification import classify_acceptance
from abx.interface.types import InterfaceGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_receiver_acceptance_report() -> dict[str, object]:
    acceptance = build_acceptance_records()
    interpretation = build_interpretation_records()
    int_idx = {x.handoff_ref: x for x in interpretation}
    states = {
        x.acceptance_id: classify_acceptance(acceptance_state=x.acceptance_state, interpretation_state=int_idx[x.handoff_ref].interpretation_state)
        for x in acceptance
    }
    errors = []
    for row in acceptance:
        state = states[row.acceptance_id]
        if state in {"REJECTED", "COERCED_DEFAULTED", "INTERPRETATION_MISMATCH", "NOT_COMPUTABLE"}:
            errors.append(InterfaceGovernanceErrorRecord("ACCEPTANCE_BLOCKING", "ERROR", f"{row.handoff_ref} state={state}"))
        elif state in {"RECEIVED_UNACCEPTED", "ACCEPTED_STRUCTURAL"}:
            errors.append(InterfaceGovernanceErrorRecord("ACCEPTANCE_ATTENTION", "WARN", f"{row.handoff_ref} state={state}"))
    report = {
        "artifactType": "ReceiverAcceptanceAudit.v1",
        "artifactId": "receiver-acceptance-audit",
        "acceptance": [x.__dict__ for x in acceptance],
        "interpretation": [x.__dict__ for x in interpretation],
        "acceptanceStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
