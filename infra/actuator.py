# Actuator (v0.1). Executes state changes ONLY when kernel governance gate passes.

from __future__ import annotations

import subprocess
from typing import Any, Dict, List

from infra.health_probes import basic_health_state
from shared.policy import load_policy


def apply(payload: Dict[str, Any]) -> Dict[str, Any]:
    plan: List[Dict[str, Any]] = payload.get("action_plan", []) or []
    audit: List[Dict[str, Any]] = []
    applied_ok = 0
    dry_run = bool(payload.get("dry_run", False))

    policy_doc = load_policy()
    actuator_policy = policy_doc.get("actuator", {}) or {}
    allow_actions = set(actuator_policy.get("allow_actions", []) or [])
    allow_services = set(actuator_policy.get("allow_services", []) or [])

    services = policy_doc.get("services", {}) or {}
    svc_default = services.get("daemon_service", "abraxas-daemon")
    disk_path = services.get("disk_path", "/")

    for step in plan:
        action = step.get("action")
        if action not in allow_actions:
            audit.append(
                {
                    "step": step,
                    "status": "skipped",
                    "reason": "action_not_allowed_by_policy",
                }
            )
            continue

        if action.startswith("systemd."):
            service = step.get("service")
            if not service:
                audit.append(
                    {
                        "step": step,
                        "status": "skipped",
                        "reason": "missing_service",
                    }
                )
                continue
            if allow_services and service not in allow_services:
                audit.append(
                    {
                        "step": step,
                        "status": "skipped",
                        "reason": "service_not_allowed_by_policy",
                    }
                )
                continue

            cmd = ["systemctl", action.split(".")[1], service]
            try:
                if dry_run:
                    audit.append(
                        {"step": step, "status": "dry_run_ok", "cmd": cmd}
                    )
                else:
                    subprocess.check_call(cmd)
                    audit.append({"step": step, "status": "ok", "cmd": cmd})
                    applied_ok += 1
            except Exception as exc:
                audit.append(
                    {"step": step, "status": "error", "cmd": cmd, "error": str(exc)}
                )

        elif action == "ops.alert":
            audit.append(
                {"step": step, "status": "ok", "note": step.get("message")}
            )
            applied_ok += 1

    verification = basic_health_state(
        daemon_service=svc_default, disk_path=disk_path
    )

    return {
        "apply_receipt": {
            "dry_run": dry_run,
            "applied_steps_total": len(audit),
            "applied_steps_ok": applied_ok,
        },
        "verification": verification,
        "audit_log": audit,
    }
