from __future__ import annotations

from abx.operator.types import ManualInterventionRecord


_KIND_MAP = {
    "corrective": "CORRECTIVE_INTERVENTION",
    "emergency": "EMERGENCY_INTERVENTION",
    "maintenance": "MAINTENANCE_INTERVENTION",
    "investigatory": "INVESTIGATORY_INTERVENTION",
    "bypass": "BYPASS_INTERVENTION",
    "prohibited": "PROHIBITED_INTERVENTION",
}


def classify_intervention_kind(record: ManualInterventionRecord) -> str:
    return _KIND_MAP.get(record.intervention_kind_signal, "INTERVENTION_UNKNOWN")


def classify_intervention_legitimacy(record: ManualInterventionRecord) -> str:
    kind = classify_intervention_kind(record)
    if kind in {"PROHIBITED_INTERVENTION", "BYPASS_INTERVENTION"}:
        return "MANUAL_INTERVENTION_ILLEGITIMATE"
    if not record.authority_ref:
        return "MANUAL_INTERVENTION_ILLEGITIMATE"
    if kind == "INTERVENTION_UNKNOWN":
        return "NOT_COMPUTABLE"
    return "MANUAL_INTERVENTION_LEGITIMATE"
