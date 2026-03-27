from __future__ import annotations

from abx.performance.budgetInventory import build_budget_inventory, build_quota_inventory, build_throttle_inventory
from abx.performance.budgetPolicies import budget_precedence, classify_budget_state
from abx.performance.quotaThrottleClassification import (
    classify_quota_scope,
    classify_throttle_scope,
    detect_hidden_retry_or_throttle_drift,
    throttle_precedence_order,
)
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_budget_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "BudgetQuotaThrottleAudit.v1",
        "artifactId": "budget-quota-throttle-audit",
        "budgets": [x.__dict__ for x in build_budget_inventory()],
        "quotas": [x.__dict__ for x in build_quota_inventory()],
        "throttles": [x.__dict__ for x in build_throttle_inventory()],
        "budgetState": classify_budget_state(),
        "quotaClassification": classify_quota_scope(),
        "throttleClassification": classify_throttle_scope(),
        "budgetPrecedence": budget_precedence(),
        "throttlePrecedence": throttle_precedence_order(),
        "hiddenDrift": detect_hidden_retry_or_throttle_drift(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
