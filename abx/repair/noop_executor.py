from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from abx.repair.manifest import RepairManifest
from abx.repair.safety_gate import validate_safety


def run_noop_executor(manifest: RepairManifest) -> Dict[str, Any]:
    ok, reason = validate_safety(manifest)
    status = "PASS" if ok else ("BLOCKED" if reason != "readiness_blocked" else "NOT_COMPUTABLE")
    return {
        "schema_version": "Patch004SandboxReceipt.v1",
        "run_id": f"patch004-sandbox-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "manifest_id": manifest["manifest_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "actions_planned": len(manifest.get("proposed_actions", [])),
        "actions_executed": 0,
        "files_modified": [],
        "execution_triggered": False,
        "runtime_mutation": False,
        "authority_leak_detected": False,
        "sandbox_only": True,
        "patch_004_execution_allowed": False,
        "status": status,
    }
