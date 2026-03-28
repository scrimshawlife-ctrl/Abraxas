from __future__ import annotations

from abx.reconcile.types import CosmeticAlignmentRecord


def build_cosmetic_alignment_records() -> list[CosmeticAlignmentRecord]:
    return [
        CosmeticAlignmentRecord("cos.001", "rec.001", "COSMETIC_ALIGNMENT_INACTIVE", "ops_dashboard"),
        CosmeticAlignmentRecord("cos.002", "rec.002", "COSMETIC_ALIGNMENT_INACTIVE", "ops_dashboard"),
        CosmeticAlignmentRecord("cos.003", "rec.003", "COSMETIC_ALIGNMENT_INACTIVE", "identity_console"),
        CosmeticAlignmentRecord("cos.004", "rec.004", "COSMETIC_ALIGNMENT_INACTIVE", "schema_console"),
        CosmeticAlignmentRecord("cos.005", "rec.005", "COSMETIC_ALIGNMENT_INACTIVE", "lineage_console"),
        CosmeticAlignmentRecord("cos.006", "rec.006", "COSMETIC_ALIGNMENT_INACTIVE", "policy_console"),
        CosmeticAlignmentRecord("cos.007", "rec.007", "COSMETIC_ALIGNMENT_ACTIVE", "ui_projection"),
        CosmeticAlignmentRecord("cos.008", "rec.008", "COSMETIC_ALIGNMENT_INACTIVE", "ops_dashboard"),
        CosmeticAlignmentRecord("cos.009", "rec.009", "COSMETIC_ALIGNMENT_INACTIVE", "ops_dashboard"),
        CosmeticAlignmentRecord("cos.010", "rec.010", "COSMETIC_ALIGNMENT_INACTIVE", "ops_dashboard"),
    ]
