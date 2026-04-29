from __future__ import annotations

from typing import Any, Mapping

from abx.repair.manifest import RepairManifest, utc_now_iso


def build_repair_manifest(readiness_summary: Mapping[str, Any]) -> RepairManifest:
    run_id = str(readiness_summary.get("run_id", "NOT_COMPUTABLE") or "NOT_COMPUTABLE")
    manifest_id = f"patch004-manifest-{str(readiness_summary.get('cycle_count_observed', '0'))}"
    return {
        "schema_version": "RepairManifest.v1",
        "manifest_id": manifest_id,
        "created_at": utc_now_iso(),
        "source_run_id": run_id,
        "readiness_status": str(readiness_summary.get("readiness_status", "NOT_COMPUTABLE")),
        "design_pass_allowed": bool(readiness_summary.get("design_pass_allowed", False)),
        "execution_allowed": bool(readiness_summary.get("execution_allowed", False)),
        "runtime_mutation_allowed": bool(readiness_summary.get("runtime_mutation_allowed", False)),
        "proposed_actions": [
            {
                "action_id": "patch004.noop.design",
                "action_type": "NOOP",
                "target_path": "docs/patch004_design_scaffold.md",
                "rationale": "Design scaffold only; no runtime execution.",
                "risk_level": "LOW",
                "requires_operator_review": True,
            }
        ],
        "safety": {
            "execution_triggered": bool(readiness_summary.get("execution_triggered", False)),
            "runtime_mutation": bool(readiness_summary.get("runtime_mutation", False)),
            "authority_leak_detected": bool(readiness_summary.get("authority_leak_detected", False)),
        },
    }
