from __future__ import annotations

from abx.deployment.deploymentClassification import classify_deployment_surfaces, deployment_ownership_summary
from abx.deployment.deploymentContracts import build_environment_deployment_contracts
from abx.deployment.deploymentInventory import build_deployment_contract_inventory
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable



def build_deployment_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "DeploymentAudit.v1",
        "artifactId": "deployment-audit",
        "contracts": [x.__dict__ for x in build_deployment_contract_inventory()],
        "classification": classify_deployment_surfaces(),
        "ownership": deployment_ownership_summary(),
        "environmentContracts": build_environment_deployment_contracts(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
