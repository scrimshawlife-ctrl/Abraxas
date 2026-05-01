from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from abraxas.canary.execution_models import CanaryActivationExecution, RUN_AUTHORITY, build_skipped
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _has_forbidden_authority(authority: dict[str, Any]) -> str | None:
    checks = ["overlay_activation", "promotion", "production_execution", "runtime_write", "baseline_mutation"]
    for key in checks:
        if authority.get(key) is True:
            return key
    return None


def build_canary_activation_execution_run(
    activation_packet_run: Mapping[str, Any],
    *,
    created_at: str,
    scope_id: str,
    sandbox_root: str | None = None,
) -> dict:
    payload = deepcopy(dict(activation_packet_run))
    errors: list[str] = []
    packets = payload.get("packets") if isinstance(payload.get("packets"), list) else []

    if payload.get("schema_version") != "CanaryActivationPacketRun.v1":
        errors.append("invalid_packet_run")

    packet_run_hash = _sha(payload)

    executions: list[dict] = []
    skipped: list[dict] = []
    sandbox_root_path = Path(sandbox_root).resolve() if sandbox_root else None

    for packet in sorted((p for p in packets if isinstance(p, dict)), key=lambda p: (str(p.get("source_key", "")), str(p.get("packet_id", "")))):
        required = ["packet_id", "source_key", "overlay_id", "overlay_hash", "simulation_hash", "recommendation_id", "authority", "lineage"]
        if any(packet.get(r) is None for r in required):
            skipped.append(build_skipped(packet, "invalid_packet"))
            continue

        lineage = packet.get("lineage") if isinstance(packet.get("lineage"), dict) else {}
        if lineage.get("recommendation_id") is None or lineage.get("simulation_hash") is None:
            skipped.append(build_skipped(packet, "missing_required_lineage"))
            continue

        authority = packet.get("authority") if isinstance(packet.get("authority"), dict) else {}
        violation = _has_forbidden_authority(authority)
        if violation:
            skipped.append(build_skipped(packet, f"authority_boundary_violation:{violation}"))
            continue

        if packet.get("recommendation_status") != "recommend_approve_for_activation_review":
            skipped.append(build_skipped(packet, "not_approved_for_execution"))
            continue

        execution_scope = {
            "environment": "canary",
            "scope_id": scope_id,
            "sandbox_path": None,
        }
        receipt_base = {
            "schema_version": "CanaryOverlayActivationReceipt.v1",
            "packet_id": packet["packet_id"],
            "overlay_id": packet["overlay_id"],
            "source_key": packet["source_key"],
            "scope_id": scope_id,
            "created_at": created_at,
            "activation_packet_run_hash": packet_run_hash,
            "summary": packet.get("summary"),
            "evidence": packet.get("evidence"),
            "lineage": lineage,
        }
        artifact_hash = _sha(receipt_base)

        execution_id_payload = {
            "schema_version": "CanaryActivationExecution.v1",
            "packet_id": packet["packet_id"],
            "source_key": packet["source_key"],
            "overlay_id": packet["overlay_id"],
            "overlay_hash": packet["overlay_hash"],
            "simulation_hash": packet["simulation_hash"],
            "recommendation_id": packet["recommendation_id"],
            "ledger_entry_hash": lineage.get("ledger_entry_hash"),
            "created_at": created_at,
            "scope_id": scope_id,
            "activation_packet_run_hash": packet_run_hash,
            "artifact_hash": artifact_hash,
        }
        execution_id = _sha(execution_id_payload)

        artifact_path = None
        if sandbox_root_path is not None:
            try:
                receipt_dir = sandbox_root_path / "canary_activation_receipts"
                receipt_dir.mkdir(parents=True, exist_ok=True)
                receipt_path = receipt_dir / f"{execution_id}.json"
                receipt_path.write_text(canonical_json(receipt_base) + "\n", encoding="utf-8")
                artifact_path = str(receipt_path)
                execution_scope["sandbox_path"] = str(receipt_dir)
                artifact_hash = sha256(receipt_path.read_bytes()).hexdigest()
            except Exception as exc:
                skipped.append(build_skipped(packet, f"sandbox_apply_failed:{exc.__class__.__name__}"))
                continue

        executions.append(
            CanaryActivationExecution(
                execution_id=execution_id,
                packet_id=packet["packet_id"],
                source_key=packet["source_key"],
                overlay_id=packet["overlay_id"],
                overlay_hash=packet["overlay_hash"],
                simulation_hash=packet["simulation_hash"],
                recommendation_id=packet["recommendation_id"],
                ledger_entry_hash=lineage.get("ledger_entry_hash"),
                execution_scope=execution_scope,
                applied_artifact={
                    "artifact_type": "canary_overlay_activation_receipt",
                    "artifact_hash": artifact_hash,
                    "artifact_path": artifact_path,
                },
                evidence={"summary": packet.get("summary"), "evidence": packet.get("evidence")},
                lineage={
                    "activation_packet_run_hash": packet_run_hash,
                    "packet_id": packet["packet_id"],
                    "simulation_hash": packet["simulation_hash"],
                    "recommendation_id": packet["recommendation_id"],
                    "ledger_entry_hash": lineage.get("ledger_entry_hash"),
                },
                reason=None,
            ).to_dict()
        )

    executions = sorted(executions, key=lambda x: (x["source_key"], x["execution_id"]))
    skipped = sorted(skipped, key=lambda x: (str(x.get("source_key") or ""), str(x.get("overlay_id") or ""), str(x.get("packet_id") or ""), x["reason"]))

    counts = {
        "input_packets": len(packets),
        "executions": len(executions),
        "skipped": len(skipped),
        "canary_applied": len(executions),
        "blocked": 0,
        "not_computable": 0,
    }
    run_wo_id = {
        "schema_version": "CanaryActivationExecutionRun.v1",
        "created_at": created_at,
        "execution_scope": {"environment": "canary", "scope_id": scope_id, "sandbox_root": str(sandbox_root_path) if sandbox_root_path else None},
        "authority": dict(RUN_AUTHORITY),
        "input": {"activation_packet_run_hash": packet_run_hash},
        "counts": counts,
        "executions": executions,
        "skipped": skipped,
        "validation": {"valid": len(errors) == 0, "errors": errors},
    }
    run_id = _sha(run_wo_id)
    run_wo_id["run_id"] = run_id
    return run_wo_id
