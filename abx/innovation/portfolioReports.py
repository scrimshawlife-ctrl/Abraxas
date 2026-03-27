from __future__ import annotations

from abx.innovation.portfolioClassification import classify_innovation_portfolio, detect_stale_experiment_drift
from abx.innovation.portfolioInventory import build_innovation_portfolio_inventory
from abx.innovation.retirementRecords import build_retirement_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_innovation_portfolio_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "InnovationPortfolioAudit.v1",
        "artifactId": "innovation-portfolio-audit",
        "portfolio": [x.__dict__ for x in build_innovation_portfolio_inventory()],
        "classification": classify_innovation_portfolio(),
        "stale": detect_stale_experiment_drift(),
        "retirement": [x.__dict__ for x in build_retirement_records()],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
