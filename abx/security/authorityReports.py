from __future__ import annotations

from abx.security.actionBoundaries import (
    classify_action_permissions,
    classify_authority_boundaries,
    detect_redundant_authority_models,
)
from abx.security.authorityInventory import build_action_permissions, build_authority_inventory
from abx.security.authorityPrecedence import build_authority_precedence, detect_hidden_privilege_drift
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_authority_boundary_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "AuthorityBoundaryAudit.v1",
        "artifactId": "authority-boundary-audit",
        "authorityBoundaries": [x.__dict__ for x in build_authority_inventory()],
        "actionPermissions": [x.__dict__ for x in build_action_permissions()],
        "authorityClassification": classify_authority_boundaries(),
        "actionClassification": classify_action_permissions(),
        "precedence": build_authority_precedence(),
        "redundantModels": detect_redundant_authority_models(),
        "hiddenPrivilegeDrift": detect_hidden_privilege_drift(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
