from __future__ import annotations

from abx.performance.accountingClassification import (
    classify_accounting_modes,
    classify_accounting_necessity,
    detect_redundant_accounting_surfaces,
)
from abx.performance.costProxies import build_cost_proxy_summary
from abx.performance.resourceAccounting import build_resource_accounting_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_resource_accounting_report() -> dict[str, object]:
    report = {
        "artifactType": "ResourceAccountingAudit.v1",
        "artifactId": "resource-accounting-audit",
        "records": [x.__dict__ for x in build_resource_accounting_records()],
        "modeClassification": classify_accounting_modes(),
        "necessityClassification": classify_accounting_necessity(),
        "costProxies": build_cost_proxy_summary(),
        "redundantSurfaces": detect_redundant_accounting_surfaces(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
