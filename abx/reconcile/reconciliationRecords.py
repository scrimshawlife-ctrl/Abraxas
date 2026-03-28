from __future__ import annotations

from abx.reconcile.reconciliationInventory import build_reconciliation_inventory
from abx.reconcile.types import ReconciliationRecord, RepairLegitimacyRecord


def build_reconciliation_records() -> list[ReconciliationRecord]:
    return [
        ReconciliationRecord(
            reconciliation_id=reconciliation_id,
            conflict_ref=conflict_ref,
            repair_mode=repair_mode,
            reconciliation_state=reconciliation_state,
        )
        for reconciliation_id, conflict_ref, repair_mode, reconciliation_state in build_reconciliation_inventory()
    ]


def build_repair_legitimacy_records() -> list[RepairLegitimacyRecord]:
    inventory = {
        "rec.001": ("LEGITIMATE", "stale cache with canonical source available"),
        "rec.002": ("LEGITIMATE", "freshness refresh aligned with decay policy"),
        "rec.003": ("LEGITIMATE", "identity merge validated by canonical reference"),
        "rec.004": ("LEGITIMATE", "semantic rollback approved by schema authority"),
        "rec.005": ("LEGITIMATE", "lineage rebuild replayable and authorized"),
        "rec.006": ("LEGITIMATE", "authority owner approved canonical overwrite"),
        "rec.007": ("LEGITIMATE", "cosmetic divergence quarantined from truth surface"),
        "rec.008": ("NOT_COMPUTABLE", "conflict class unresolved"),
        "rec.009": ("FORBIDDEN", "upstream state incomplete and unsafe to repair"),
        "rec.010": ("UNKNOWN", "authority adjudication pending"),
    }
    return [
        RepairLegitimacyRecord(
            legitimacy_id=f"leg.{idx:03d}",
            reconciliation_ref=rid,
            legitimacy_state=state,
            legitimacy_reason=reason,
        )
        for idx, (rid, (state, reason)) in enumerate(inventory.items(), start=1)
    ]
