from __future__ import annotations

from abx.admission.admissionInventory import build_admission_inventory
from abx.admission.types import ChangeAdmissionRecord


def build_change_admission_records() -> list[ChangeAdmissionRecord]:
    return [
        ChangeAdmissionRecord(admission_id=aid, change_ref=cref, admission_state=state, evidence_state=evidence)
        for aid, cref, state, evidence in build_admission_inventory()
    ]
