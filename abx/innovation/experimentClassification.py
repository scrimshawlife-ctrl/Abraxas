from __future__ import annotations

from abx.innovation.experimentInventory import build_experiment_surface_inventory


ALLOWED_SURFACE_KINDS = {
    "sandbox-only",
    "prototype",
    "canary-eligible",
    "evaluation-only",
    "legacy-experiment",
    "deprecated-candidate",
}


def classify_experiment_surfaces() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {
        "sandbox_only": [],
        "prototype": [],
        "canary_eligible": [],
        "evaluation_only": [],
        "legacy_experiment": [],
        "deprecated_candidate": [],
        "production_prohibited": [],
        "unbounded_risk": [],
    }
    for rec in build_experiment_surface_inventory():
        key = rec.surface_kind.replace("-", "_")
        if key in grouped:
            grouped[key].append(rec.experiment_id)
        if rec.influence_boundary == "production-prohibited":
            grouped["production_prohibited"].append(rec.experiment_id)
        if rec.influence_boundary == "unbounded-risk":
            grouped["unbounded_risk"].append(rec.experiment_id)

    for ids in grouped.values():
        ids.sort()
    return grouped


def detect_experiment_taxonomy_drift() -> list[dict[str, str]]:
    drift: list[dict[str, str]] = []
    for rec in build_experiment_surface_inventory():
        if rec.surface_kind not in ALLOWED_SURFACE_KINDS:
            drift.append(
                {
                    "experimentId": rec.experiment_id,
                    "reason": "unknown_surface_kind",
                    "surfaceKind": rec.surface_kind,
                }
            )
    return drift


def detect_hidden_experimental_influence() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for rec in build_experiment_surface_inventory():
        if rec.runtime_scope == "shared-prod" and rec.influence_boundary != "bounded_canary":
            issues.append(
                {
                    "experimentId": rec.experiment_id,
                    "reason": "unsafe_prod_influence",
                }
            )
        if rec.influence_boundary == "unbounded-risk":
            issues.append(
                {
                    "experimentId": rec.experiment_id,
                    "reason": "unbounded_influence",
                }
            )
    return issues
