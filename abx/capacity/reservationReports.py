from __future__ import annotations

from abx.capacity.reservationClassification import classify_reservation
from abx.capacity.resourceReservationRecords import build_resource_reservation_records
from abx.capacity.types import CapacityGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_resource_reservation_report() -> dict[str, object]:
    rows = build_resource_reservation_records()
    states = {x.reservation_id: classify_reservation(reservation_state=x.reservation_state) for x in rows}
    errors = []
    for row in rows:
        state = states[row.reservation_id]
        if state in {"RESERVATION_DENIED", "NOT_COMPUTABLE"}:
            errors.append(CapacityGovernanceErrorRecord("RESERVATION_BLOCKING", "ERROR", f"{row.resource_ref} state={state}"))
        elif state in {"PROVISIONAL_HOLD_ACTIVE", "RESERVATION_EXPIRED"}:
            errors.append(CapacityGovernanceErrorRecord("RESERVATION_ATTENTION", "WARN", f"{row.resource_ref} state={state}"))
    report = {
        "artifactType": "ResourceReservationAudit.v1",
        "artifactId": "resource-reservation-audit",
        "reservation": [x.__dict__ for x in rows],
        "reservationStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
