from __future__ import annotations

from abx.performance.types import BudgetRecord, QuotaRecord, ThrottleRecord


def build_budget_inventory() -> list[BudgetRecord]:
    return [
        BudgetRecord("budget.run.compute_ms", "run", "runtime", "run_budget", "max_compute", 1500.0, "ms"),
        BudgetRecord("budget.workflow.validation_ms", "workflow", "governance", "workflow_budget", "max_compute", 400.0, "ms"),
        BudgetRecord("budget.environment.network_calls", "environment", "federation", "environment_budget", "max_calls", 5.0, "calls"),
        BudgetRecord("budget.operator.report_bytes", "operator", "observability", "operator_budget", "max_io", 65536.0, "bytes"),
        BudgetRecord("budget.background.backfill_jobs", "background", "operations", "background_budget", "max_jobs", 1.0, "jobs"),
    ]


def build_quota_inventory() -> list[QuotaRecord]:
    return [
        QuotaRecord("quota.run.requests", "run", "runtime", "max_requests", 3.0, "count"),
        QuotaRecord("quota.workflow.retries", "workflow", "governance", "max_retries", 1.0, "count"),
        QuotaRecord("quota.environment.handoffs", "environment", "federation", "max_handoffs", 2.0, "count"),
    ]


def build_throttle_inventory() -> list[ThrottleRecord]:
    return [
        ThrottleRecord(
            throttle_id="throttle.interop.burst_control",
            scope="environment",
            owner="federation",
            throttle_class="token_bucket",
            trigger="quota.environment.handoffs >= 2",
            action="degrade_to_summary_only",
            precedence=20,
        ),
        ThrottleRecord(
            throttle_id="throttle.observability.report_size",
            scope="operator",
            owner="observability",
            throttle_class="hard_cap",
            trigger="budget.operator.report_bytes exceeded",
            action="truncate_optional_sections",
            precedence=30,
        ),
    ]
