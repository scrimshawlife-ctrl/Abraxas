from __future__ import annotations

from abx.agency.autonomousClassification import classify_autonomous_operation_mode, classify_autonomous_posture
from abx.agency.autonomousInventory import build_autonomous_operation_inventory
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_autonomous_operation_report() -> dict[str, object]:
    inventory = build_autonomous_operation_inventory()
    mode_states = {
        row.operation_id: classify_autonomous_operation_mode(row.mode, row.status)
        for row in inventory
    }
    report = {
        "artifactType": "AutonomousOperationAudit.v1",
        "artifactId": "autonomous-operation-audit",
        "operations": [x.__dict__ for x in inventory],
        "modeStates": mode_states,
        "autonomousPosture": classify_autonomous_posture(mode_states),
        "blockedOperations": sorted(k for k, v in mode_states.items() if v == "BLOCKED"),
        "degradedOperations": sorted(k for k, v in mode_states.items() if v == "DEGRADED"),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
