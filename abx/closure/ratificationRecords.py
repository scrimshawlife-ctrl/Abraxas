from __future__ import annotations

from abx.closure.auditReports import build_audit_readiness_record
from abx.closure.closureReports import build_system_closure_record
from abx.closure.ratificationClassification import classify_ratification_state
from abx.closure.ratificationCriteria import build_ratification_criteria
from abx.closure.types import RatificationDecisionRecord


def build_ratification_decision_record() -> RatificationDecisionRecord:
    criteria = build_ratification_criteria()
    closure = build_system_closure_record()
    audit = build_audit_readiness_record()

    satisfied: list[str] = []
    unmet: list[str] = []
    waived: list[str] = []

    for row in criteria:
        missing_domains = [d for d in row.required_domains if closure.domain_states.get(d) not in {"CLOSURE_COMPLETE", "CLOSURE_COMPLETE_WITH_WAIVERS"}]
        waived_domains = [d for d in row.required_domains if d in closure.waived_domains]
        audit_gate_fail = row.requires_audit_ready and audit.readiness_state not in {"AUDIT_READY", "AUDIT_READY_WITH_GAPS"}
        if missing_domains or audit_gate_fail:
            unmet.append(row.criteria_id)
            continue
        if len(waived_domains) > row.max_waived_domains:
            unmet.append(row.criteria_id)
            continue
        if waived_domains:
            waived.append(row.criteria_id)
        else:
            satisfied.append(row.criteria_id)

    state = classify_ratification_state(
        unmet_criteria=sorted(unmet),
        waived_criteria=sorted(waived),
        audit_readiness_state=audit.readiness_state,
    )
    return RatificationDecisionRecord(
        decision_id="ratification-decision",
        scope="baseline",
        decision_state=state,
        satisfied_criteria=sorted(satisfied),
        unmet_criteria=sorted(unmet),
        waived_criteria=sorted(waived),
        evidence_bundle_ids=sorted(audit.bundle_states.keys()),
    )
