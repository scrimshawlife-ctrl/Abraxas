from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from .binding_gap_tasks import run_binding_gap_tasks


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_exists(path: str) -> bool:
    return Path(path).exists()


def run_binding_gap_executor() -> dict[str, Any]:
    tasks_data = run_binding_gap_tasks()
    execution: list[dict[str, Any]] = []

    for task in tasks_data["tasks"]:
        path = task["target_path"]
        exists = _path_exists(path)
        execution.append(
            {
                "subsystem_id": task["subsystem_id"],
                "category": task["category"],
                "target_path": path,
                "priority": task["priority"],
                "exists": exists,
                "status": "READY" if not exists else "ALREADY_PRESENT",
            }
        )

    grouped: dict[int, list[dict[str, Any]]] = {}
    for item in execution:
        grouped.setdefault(item["priority"], []).append(item)

    payload = {
        "schema_version": "BindingGapExecutionReport.v1",
        "total_tasks": len(execution),
        "by_priority": {str(priority): items for priority, items in sorted(grouped.items())},
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
