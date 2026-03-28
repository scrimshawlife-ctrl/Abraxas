from __future__ import annotations

from abx.reconcile.types import LossyRepairRecord


def build_lossy_repair_records() -> list[LossyRepairRecord]:
    return [
        LossyRepairRecord("loss.001", "rec.001", "NO_LOSS", "refresh was exact"),
        LossyRepairRecord("loss.002", "rec.002", "NO_LOSS", "stale cache eviction only"),
        LossyRepairRecord("loss.003", "rec.003", "LOSSY_REPAIR_ACTIVE", "duplicate aliases collapsed"),
        LossyRepairRecord("loss.004", "rec.004", "NO_LOSS", "rollback to known schema"),
        LossyRepairRecord("loss.005", "rec.005", "NO_LOSS", "rebuild replay complete"),
        LossyRepairRecord("loss.006", "rec.006", "NO_LOSS", "authoritative overwrite replay verified"),
        LossyRepairRecord("loss.007", "rec.007", "NO_LOSS", "cosmetic quarantine"),
        LossyRepairRecord("loss.008", "rec.008", "NOT_COMPUTABLE", "legitimacy unresolved"),
        LossyRepairRecord("loss.009", "rec.009", "NOT_COMPUTABLE", "forbidden path"),
        LossyRepairRecord("loss.010", "rec.010", "NOT_COMPUTABLE", "validation pending"),
    ]
