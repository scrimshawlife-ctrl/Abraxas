from __future__ import annotations

from abx.performance.budgetInventory import build_budget_inventory


USAGE = {
    "budget.run.compute_ms": 530.0,
    "budget.workflow.validation_ms": 130.0,
    "budget.environment.network_calls": 2.0,
    "budget.operator.report_bytes": 22100.0,
    "budget.background.backfill_jobs": 2.0,
}


def classify_budget_state() -> dict[str, list[str]]:
    out = {"under_budget": [], "over_budget": [], "degraded": [], "blocked": [], "not_computable": []}
    for budget in build_budget_inventory():
        used = USAGE.get(budget.budget_id)
        if used is None:
            out["not_computable"].append(budget.budget_id)
            continue
        if used > budget.value and budget.scope == "background":
            out["degraded"].append(budget.budget_id)
            continue
        if used > budget.value:
            out["over_budget"].append(budget.budget_id)
            continue
        out["under_budget"].append(budget.budget_id)
    return {k: sorted(v) for k, v in out.items()}


def budget_precedence() -> list[str]:
    order = {"run": 10, "workflow": 20, "environment": 30, "operator": 40, "background": 50}
    return [x.budget_id for x in sorted(build_budget_inventory(), key=lambda r: (order[r.scope], r.budget_id))]
