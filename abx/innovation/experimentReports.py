from __future__ import annotations

from abx.innovation.experimentClassification import (
    classify_experiment_surfaces,
    detect_experiment_taxonomy_drift,
    detect_hidden_experimental_influence,
)
from abx.innovation.experimentInventory import build_experiment_surface_inventory
from abx.innovation.experimentOwnership import build_experiment_ownership_map, detect_unowned_experiments
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_experiment_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "ExperimentSurfaceAudit.v1",
        "artifactId": "experiment-surface-audit",
        "surfaces": [x.__dict__ for x in build_experiment_surface_inventory()],
        "classification": classify_experiment_surfaces(),
        "ownership": build_experiment_ownership_map(),
        "unowned": detect_unowned_experiments(),
        "taxonomyDrift": detect_experiment_taxonomy_drift(),
        "hiddenInfluence": detect_hidden_experimental_influence(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
