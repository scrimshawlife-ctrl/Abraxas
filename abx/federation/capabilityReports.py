from __future__ import annotations

from abx.federation.capabilityDependencies import build_capability_dependencies
from abx.federation.capabilityInventory import build_capability_inventory
from abx.federation.capabilityRegistry import capability_registry_summary
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_capability_registry_report() -> dict[str, object]:
    report = {
        "artifactType": "CapabilityRegistryAudit.v1",
        "artifactId": "capability-registry-audit",
        "capabilities": [x.__dict__ for x in build_capability_inventory()],
        "ownership": capability_registry_summary(),
        "dependencies": [x.__dict__ for x in build_capability_dependencies()],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
