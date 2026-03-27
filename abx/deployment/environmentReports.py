from __future__ import annotations

from abx.deployment.environmentClassification import classify_environment_taxonomy, detect_redundant_environment_taxonomy
from abx.deployment.environmentInventory import build_environment_inventory
from abx.deployment.environmentParity import build_environment_parity_records, classify_parity_status
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable



def build_environment_parity_report() -> dict[str, object]:
    report = {
        "artifactType": "EnvironmentParityAudit.v1",
        "artifactId": "environment-parity-audit",
        "environments": build_environment_inventory(),
        "taxonomy": classify_environment_taxonomy(),
        "parityRecords": [x.__dict__ for x in build_environment_parity_records()],
        "parityClassification": classify_parity_status(),
        "taxonomyRedundancy": detect_redundant_environment_taxonomy(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
