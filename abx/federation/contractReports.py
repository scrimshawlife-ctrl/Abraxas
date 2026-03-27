from __future__ import annotations

from abx.federation.contractCompatibility import classify_contract_compatibility, detect_duplicate_contract_shapes
from abx.federation.contractOwnership import contract_ownership_report
from abx.federation.crossSystemContracts import build_cross_system_contracts
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_cross_system_contract_report() -> dict[str, object]:
    report = {
        "artifactType": "CrossSystemContractAudit.v1",
        "artifactId": "cross-system-contract-audit",
        "contracts": [x.__dict__ for x in build_cross_system_contracts()],
        "ownership": contract_ownership_report(),
        "compatibility": classify_contract_compatibility(),
        "duplicateShapes": detect_duplicate_contract_shapes(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
