from __future__ import annotations

from abx.performance.budgetInventory import build_quota_inventory, build_throttle_inventory


def classify_quota_scope() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"run": [], "workflow": [], "environment": [], "operator": [], "background": []}
    for row in build_quota_inventory():
        out[row.scope].append(row.quota_id)
    return {k: sorted(v) for k, v in out.items()}


def classify_throttle_scope() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"run": [], "workflow": [], "environment": [], "operator": [], "background": []}
    for row in build_throttle_inventory():
        out[row.scope].append(row.throttle_id)
    return {k: sorted(v) for k, v in out.items()}


def throttle_precedence_order() -> list[str]:
    return [x.throttle_id for x in sorted(build_throttle_inventory(), key=lambda r: (r.precedence, r.throttle_id))]


def detect_hidden_retry_or_throttle_drift() -> list[str]:
    drift: list[str] = []
    for row in build_quota_inventory():
        if "retry" in row.limit_kind and row.scope != "workflow":
            drift.append(row.quota_id)
    return sorted(drift)
