from __future__ import annotations

from abx.security.integrityInventory import build_integrity_inventory


STATUSES = ("verified", "governed_unchecked", "monitored", "heuristic", "partial", "not_computable")


def classify_integrity_verification() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in STATUSES}
    for record in build_integrity_inventory():
        out[record.status].append(record.verification_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_integrity_mismatches() -> list[dict[str, str]]:
    mismatches: list[dict[str, str]] = []
    for record in build_integrity_inventory():
        if record.status in {"heuristic", "not_computable"}:
            mismatches.append(
                {
                    "verification_id": record.verification_id,
                    "reason": "weak_integrity_assurance",
                    "target_surface": record.target_surface,
                }
            )
    return sorted(mismatches, key=lambda x: x["verification_id"])
