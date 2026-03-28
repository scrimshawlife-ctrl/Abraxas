from __future__ import annotations


def build_restoration_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("res.001", "rec.001", "CONSISTENCY_RESTORED_DURABLE", "VALIDATED"),
        ("res.002", "rec.002", "CONSISTENCY_RESTORED_PROVISIONAL", "PENDING_VALIDATION"),
        ("res.003", "rec.003", "CONSISTENCY_PARTIALLY_RESTORED", "VALIDATED"),
        ("res.004", "rec.004", "CONSISTENCY_RESTORED_DURABLE", "VALIDATED"),
        ("res.005", "rec.005", "CONSISTENCY_RESTORED_DURABLE", "VALIDATED"),
        ("res.006", "rec.006", "CONSISTENCY_RESTORED_DURABLE", "VALIDATED"),
        ("res.007", "rec.007", "COSMETIC_ALIGNMENT_ONLY", "VALIDATION_REQUIRED"),
        ("res.008", "rec.008", "NOT_COMPUTABLE", "NOT_COMPUTABLE"),
        ("res.009", "rec.009", "RESTORATION_FAILED", "BLOCKED"),
        ("res.010", "rec.010", "RESTORATION_PENDING_VALIDATION", "PENDING_VALIDATION"),
    )
