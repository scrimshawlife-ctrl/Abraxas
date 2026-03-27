from __future__ import annotations

from abx.performance.performanceClassification import (
    classify_performance_cost_classes,
    classify_performance_surfaces,
    detect_duplicate_performance_vocabulary,
)
from abx.performance.performanceInventory import build_performance_surface_inventory
from abx.performance.performanceOwnership import build_performance_ownership
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_performance_surface_report() -> dict[str, object]:
    report = {
        "artifactType": "PerformanceSurfaceAudit.v1",
        "artifactId": "performance-surface-audit",
        "surfaces": [x.__dict__ for x in build_performance_surface_inventory()],
        "classification": classify_performance_surfaces(),
        "costClasses": classify_performance_cost_classes(),
        "ownership": build_performance_ownership(),
        "vocabularyConflicts": detect_duplicate_performance_vocabulary(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
