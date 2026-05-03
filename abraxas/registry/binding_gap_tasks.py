from __future__ import annotations

from typing import Any
import hashlib
import json

from .binding_gap_plan import run_binding_gap_plan


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _priority_for_category(category: str) -> int:
    order = {
        "modules": 1,
        "scripts": 2,
        "schemas": 3,
        "artifacts": 4,
        "tests": 5,
    }
    return order.get(category, 99)


def run_binding_gap_tasks() -> dict[str, Any]:
    plan = run_binding_gap_plan()
    tasks: list[dict[str, Any]] = []

    for subsystem in plan["plan"]:
        subsystem_id = subsystem["subsystem_id"]
        for action in subsystem["actions"]:
            category = action["category"]
            paths = action.get("expected_paths", [])
            for path in paths:
                tasks.append(
                    {
                        "subsystem_id": subsystem_id,
                        "category": category,
                        "target_path": path,
                        "priority": _priority_for_category(category),
                        "action": "CREATE_OR_FIX",
                        "verify_command": f"test -e {path} || echo MISSING:{path}",
                    }
                )

    tasks_sorted = sorted(
        tasks,
        key=lambda item: (item["priority"], item["subsystem_id"], item["target_path"]),
    )
    payload = {
        "schema_version": "BindingGapTasks.v1",
        "task_count": len(tasks_sorted),
        "tasks": tasks_sorted,
    }
    payload_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "canonical_hash": payload_hash,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
