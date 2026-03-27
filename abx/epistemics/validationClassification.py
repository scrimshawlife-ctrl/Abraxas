from __future__ import annotations

from abx.epistemics.validationInventory import build_validation_surface_inventory


TRUST = ("authoritative", "governed_derived", "monitored", "heuristic", "legacy_redundant_candidate")
KINDS = (
    "runtime_validation",
    "replay_validation",
    "invariance_validation",
    "comparison_validation",
    "incident_recovery_validation",
    "policy_integrity_validation",
)


def classify_validation_surfaces() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in TRUST}
    for row in build_validation_surface_inventory():
        out[row.trust_level].append(row.validation_id)
    return {k: sorted(v) for k, v in out.items()}


def classify_validation_kinds() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in KINDS}
    for row in build_validation_surface_inventory():
        key = row.validation_kind if row.validation_kind in out else "comparison_validation"
        out[key].append(row.validation_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_duplicate_epistemic_vocabulary() -> list[str]:
    return sorted({x.trust_level for x in build_validation_surface_inventory() if x.trust_level not in TRUST})
