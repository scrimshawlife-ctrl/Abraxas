from __future__ import annotations

from typing import Tuple

from abx.repair.manifest import RepairManifest


def validate_safety(manifest: RepairManifest) -> Tuple[bool, str]:
    if manifest["execution_allowed"]:
        return False, "execution_allowed_true"
    if manifest["runtime_mutation_allowed"]:
        return False, "runtime_mutation_allowed_true"
    if manifest["safety"].get("execution_triggered", False):
        return False, "execution_triggered_true"
    if manifest["safety"].get("runtime_mutation", False):
        return False, "runtime_mutation_true"
    if manifest["safety"].get("authority_leak_detected", False):
        return False, "authority_leak_detected_true"
    if manifest["readiness_status"] in {"HARD_BLOCKED", "NOT_COMPUTABLE"}:
        return False, "readiness_blocked"
    return True, "ok"
