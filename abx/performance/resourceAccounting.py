from __future__ import annotations

from abx.performance.types import ResourceAccountingRecord


def build_resource_accounting_records() -> list[ResourceAccountingRecord]:
    return [
        ResourceAccountingRecord(
            record_id="acct.run_execution.compute_ms",
            workflow="run_execution",
            capability="scheduler_dispatch",
            resource_type="compute_time",
            attribution_owner="runtime",
            accounting_mode="accounted",
            necessity_class="required",
            unit="ms",
            value=420.0,
        ),
        ResourceAccountingRecord(
            record_id="acct.validation.proof_ms",
            workflow="run_execution",
            capability="validation_proof_generation",
            resource_type="compute_time",
            attribution_owner="governance",
            accounting_mode="accounted",
            necessity_class="required",
            unit="ms",
            value=110.0,
        ),
        ResourceAccountingRecord(
            record_id="acct.serialization.report_bytes",
            workflow="operator_inspection",
            capability="report_generation",
            resource_type="io_serialization",
            attribution_owner="observability",
            accounting_mode="estimated_proxy",
            necessity_class="optional",
            unit="bytes",
            value=16384.0,
        ),
        ResourceAccountingRecord(
            record_id="acct.interop.handoff_calls",
            workflow="cross_system_handoff",
            capability="adapter_interop",
            resource_type="external_tooling_proxy",
            attribution_owner="federation",
            accounting_mode="heuristic",
            necessity_class="avoidable_overhead",
            unit="calls",
            value=2.0,
        ),
        ResourceAccountingRecord(
            record_id="acct.backfill.storage_mb",
            workflow="maintenance",
            capability="historical_backfill",
            resource_type="storage_artifact",
            attribution_owner="operations",
            accounting_mode="not_computable",
            necessity_class="optional",
            unit="mb",
            value=0.0,
        ),
    ]
