from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from abraxas.canary.rollback_execution_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _forbidden_authority(authority: dict[str, Any]) -> str | None:
    for field in ["production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler"]:
        if authority.get(field) is True:
            return field
    return None


def _receipt(execution_id: str, packet: dict, effect: str) -> dict:
    return {
        "receipt_version": "CanaryRollbackReceipt.v1",
        "execution_id": execution_id,
        "packet_id": packet.get("packet_id"),
        "rollback_id": packet.get("rollback_id"),
        "source_key": packet.get("source_key"),
        "effect": effect,
    }


def build_rollback_execution_run(
    rollback_packet_run: Mapping[str, Any],
    *,
    created_at: str,
    scope_id: str,
    sandbox_root: str | None = None,
) -> dict:
    data = deepcopy(dict(rollback_packet_run))
    packets = data.get("packets") if isinstance(data.get("packets"), list) else []

    sandbox = Path(sandbox_root).resolve() if sandbox_root else None
    receipt_root = sandbox / "canary_rollback_receipts" if sandbox else None

    executions: list[dict] = []

    for packet in sorted((p for p in packets if isinstance(p, dict)), key=lambda p: (str(p.get("source_key", "")), str(p.get("packet_id", "")))):
        mode = "sandbox" if sandbox else "in_memory"
        rollback_result = {
            "rollback_plan_mode": (packet.get("rollback_plan") if isinstance(packet.get("rollback_plan"), dict) else {}).get("mode"),
            "requires_artifact": bool((packet.get("rollback_plan") if isinstance(packet.get("rollback_plan"), dict) else {}).get("requires_artifact", False)),
            "artifact_hash": (packet.get("rollback_plan") if isinstance(packet.get("rollback_plan"), dict) else {}).get("artifact_hash"),
            "artifact_path": (packet.get("rollback_plan") if isinstance(packet.get("rollback_plan"), dict) else {}).get("artifact_path"),
            "effect": "none",
        }
        lineage_core = {
            "rollback_packet_hash": _sha(packet),
            "rollback_id": packet.get("rollback_id"),
            "observation_id": packet.get("observation_id"),
        }

        execution_source_id = packet.get("execution_id")
        execution_id_payload = {
            "packet_id": packet.get("packet_id"),
            "rollback_id": packet.get("rollback_id"),
            "observation_id": packet.get("observation_id"),
            "execution_source_id": execution_source_id,
            "source_key": packet.get("source_key"),
            "mode": mode,
            "scope_id": scope_id,
            "rollback_result": {k: v for k, v in rollback_result.items() if k != "artifact_path"},
            "lineage": lineage_core,
            "authority": dict(AUTHORITY_FLAGS),
        }
        execution_id = _sha(execution_id_payload)

        status = "completed"
        failure_reason = None
        artifact_hash = None
        artifact_path = None
        receipt_path = None

        if packet.get("packet_status") != "pending_review":
            status = "skipped"
            failure_reason = f"packet_not_pending_review:{packet.get('packet_status')}"
        elif packet.get("recommendation_status") != "recommend_approve_for_rollback_review":
            status = "skipped"
            failure_reason = f"not_approved_for_rollback_review:{packet.get('recommendation_status')}"
        else:
            pauth = packet.get("authority") if isinstance(packet.get("authority"), dict) else {}
            forbidden = _forbidden_authority(pauth)
            if forbidden is not None:
                status = "blocked"
                failure_reason = f"forbidden_authority_signal:{forbidden}"

        if status == "completed":
            if sandbox:
                try:
                    assert receipt_root is not None
                    receipt_root.mkdir(parents=True, exist_ok=True)
                    target = (receipt_root / f"{execution_id}.json").resolve()
                    if receipt_root.resolve() not in target.parents:
                        status = "blocked"
                        failure_reason = "sandbox_path_escape"
                    else:
                        receipt_payload = _receipt(execution_id, packet, "sandbox_receipt_written")
                        target.write_text(canonical_json(receipt_payload) + "\n", encoding="utf-8")
                        artifact_hash = _sha(receipt_payload)
                        artifact_path = str(target)
                        receipt_path = str(target)
                        rollback_result["effect"] = "sandbox_receipt_written"
                except Exception:
                    status = "failed"
                    failure_reason = "sandbox_write_failed"
            else:
                receipt_payload = _receipt(execution_id, packet, "in_memory_receipt")
                artifact_hash = _sha(receipt_payload)
                rollback_result["effect"] = "in_memory_receipt"

        execution = {
            "execution_version": "CanaryRollbackExecution.v1",
            "execution_id": execution_id,
            "packet_id": packet.get("packet_id"),
            "rollback_id": packet.get("rollback_id"),
            "observation_id": packet.get("observation_id"),
            "execution_source_id": execution_source_id,
            "source_key": str(packet.get("source_key", "")),
            "execution_status": status,
            "mode": mode,
            "scope": {
                "scope_id": scope_id,
                "sandbox_root": str(sandbox) if sandbox else None,
                "receipt_path": receipt_path,
            },
            "artifact": {
                "artifact_hash": artifact_hash,
                "artifact_path": artifact_path,
            },
            "rollback_result": {
                **rollback_result,
                "artifact_hash": rollback_result.get("artifact_hash"),
                "artifact_path": rollback_result.get("artifact_path"),
            },
            "failure": {"reason": failure_reason},
            "lineage": {
                **lineage_core,
                "execution_hash": None,
            },
            "authority": dict(AUTHORITY_FLAGS),
        }
        execution["lineage"]["execution_hash"] = _sha({k: v for k, v in execution.items() if k != "lineage"} | {"lineage": {**lineage_core, "execution_hash": None}})
        executions.append(execution)

    executions = sorted(executions, key=lambda e: (e["source_key"], e["execution_id"]))
    counts = {
        "packets_total": len(packets),
        "completed": sum(1 for e in executions if e["execution_status"] == "completed"),
        "skipped": sum(1 for e in executions if e["execution_status"] == "skipped"),
        "blocked": sum(1 for e in executions if e["execution_status"] == "blocked"),
        "failed": sum(1 for e in executions if e["execution_status"] == "failed"),
    }

    return {
        "artifact": "CANARY-ROLLBACK-EXECUTOR-001",
        "schema_version": "CanaryRollbackExecutionRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "controls": {
            "created_at": created_at,
            "scope_id": scope_id,
            "sandbox_root": str(sandbox) if sandbox else None,
        },
        "counts": counts,
        "executions": executions,
    }
