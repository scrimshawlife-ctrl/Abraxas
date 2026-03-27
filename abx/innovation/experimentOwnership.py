from __future__ import annotations

from abx.innovation.experimentInventory import build_experiment_surface_inventory


def build_experiment_ownership_map() -> dict[str, str]:
    return {rec.experiment_id: rec.owner for rec in build_experiment_surface_inventory()}


def detect_unowned_experiments() -> list[str]:
    return sorted(
        rec.experiment_id for rec in build_experiment_surface_inventory() if rec.owner in {"", "unassigned"}
    )
