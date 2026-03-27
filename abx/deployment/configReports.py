from __future__ import annotations

from abx.deployment.configClassification import build_config_classifications, classify_config_surface
from abx.deployment.configInventory import build_config_inventory
from abx.deployment.overrideContainment import detect_hidden_semantic_drift, override_precedence_summary
from abx.deployment.secretBoundaries import build_secret_boundaries
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable



def build_config_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "ConfigGovernanceAudit.v1",
        "artifactId": "config-audit",
        "configInventory": build_config_inventory(),
        "classification": [x.__dict__ for x in build_config_classifications()],
        "classificationSummary": classify_config_surface(),
        "secretBoundaries": [x.__dict__ for x in build_secret_boundaries()],
        "overridePrecedence": override_precedence_summary(),
        "semanticDrift": [x.__dict__ for x in detect_hidden_semantic_drift()],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
