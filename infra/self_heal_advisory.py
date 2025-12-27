# Advisory-only self-heal (v0.1). NO side effects.

from __future__ import annotations

from typing import Any, Dict, List

from shared.evidence import sha256_obj


def generate_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    health = payload.get("health_state", {}) or {}
    policy = payload.get("policy", {}) or {}
    audit_report_sha256 = payload.get("audit_report_sha256")

    issues: List[str] = []
    plan: List[Dict[str, Any]] = []

    if health.get("daemon_alive") is False:
        issues.append("daemon_down")
        plan.append({"action": "systemd.restart", "service": "abraxas-daemon"})

    if health.get("disk_free_pct", 100) < policy.get("min_disk_free_pct", 5):
        issues.append("low_disk")
        plan.append(
            {
                "action": "ops.alert",
                "message": "Low disk space; consider cleanup.",
            }
        )

    advisory = {
        "issues": issues,
        "action_plan": plan,
        "evidence": {
            "audit_report_sha256": audit_report_sha256,
            "health_state_sha256": sha256_obj(health),
            "policy_sha256": sha256_obj(policy),
        },
        "audit_log": {
            "notes": (
                "Advisory plan only. Apply via actuator.apply "
                "(governance-gated)."
            )
        },
    }
    advisory["evidence"]["plan_sha256"] = sha256_obj(
        {
            "issues": issues,
            "action_plan": plan,
            "evidence": advisory["evidence"],
        }
    )

    return advisory
