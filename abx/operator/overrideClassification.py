from __future__ import annotations

from abx.operator.types import HumanOverrideRecord, OverrideLegitimacyRecord


_OVERRIDE_STATUS_MAP = {
    "requested": "OVERRIDE_REQUESTED",
    "approved": "OVERRIDE_APPROVED",
    "approved_active": "OVERRIDE_ACTIVE",
    "denied": "OVERRIDE_DENIED",
    "forbidden": "OVERRIDE_FORBIDDEN",
}


def classify_override_state(record: HumanOverrideRecord) -> str:
    return _OVERRIDE_STATUS_MAP.get(record.status_signal, "NOT_COMPUTABLE")


def classify_override_legitimacy(record: HumanOverrideRecord) -> OverrideLegitimacyRecord:
    state = classify_override_state(record)
    if state == "OVERRIDE_FORBIDDEN":
        legitimacy = "ILLEGITIMATE_OVERRIDE"
        reason = "Override attempts prohibited bypass of protected boundary"
    elif state in {"OVERRIDE_DENIED", "NOT_COMPUTABLE"}:
        legitimacy = "UNRESOLVED_OVERRIDE"
        reason = "Override denied or insufficiently typed"
    elif record.authority_ref and state in {"OVERRIDE_APPROVED", "OVERRIDE_ACTIVE", "OVERRIDE_REQUESTED"}:
        legitimacy = "LEGITIMATE_OVERRIDE"
        reason = "Authority link present and boundary declared"
    else:
        legitimacy = "UNRESOLVED_OVERRIDE"
        reason = "Missing authority linkage"
    return OverrideLegitimacyRecord(
        record_id=f"leg.{record.override_id}",
        override_id=record.override_id,
        legitimacy=legitimacy,
        reason=reason,
    )


def build_override_state_index(records: tuple[HumanOverrideRecord, ...]) -> dict[str, str]:
    return {r.override_id: classify_override_state(r) for r in records}
