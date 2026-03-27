from __future__ import annotations

from abx.agency.guardrailClassification import classify_guardrail_posture, classify_guardrail_state
from abx.agency.guardrailInventory import build_guardrail_inventory
from abx.agency.guardrailPolicies import build_guardrail_triggers
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_guardrail_report() -> dict[str, object]:
    policies = build_guardrail_inventory()
    triggers = build_guardrail_triggers()
    trigger_by_policy = {x.policy_id: x for x in triggers}
    states = {
        row.policy_id: classify_guardrail_state(
            enforcement_state=row.enforcement_state,
            trigger_state=trigger_by_policy[row.policy_id].trigger_state,
        )
        for row in policies
    }
    report = {
        "artifactType": "GuardrailAudit.v1",
        "artifactId": "guardrail-audit",
        "policies": [x.__dict__ for x in policies],
        "triggers": [x.__dict__ for x in triggers],
        "policyStates": states,
        "guardrailPosture": classify_guardrail_posture(states),
        "trippedPolicies": sorted(k for k, v in states.items() if v == "TRIPPED"),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
