from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.observation_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_observation_ledger(
    execution_run: Mapping[str, Any],
    previous_ledger: Mapping[str, Any] | None = None,
) -> dict:
    execution_run_obj = deepcopy(dict(execution_run))
    previous_obj = deepcopy(dict(previous_ledger)) if previous_ledger is not None else {}

    executions = execution_run_obj.get("executions") if isinstance(execution_run_obj.get("executions"), list) else []
    prev_entries = previous_obj.get("entries") if isinstance(previous_obj.get("entries"), list) else []
    prev_by_obs = {
        str(e.get("observation_id")): e
        for e in prev_entries
        if isinstance(e, dict) and e.get("observation_id")
    }

    created: list[dict] = []
    existing = 0

    for ex in executions:
        if not isinstance(ex, dict):
            continue
        artifact = ex.get("applied_artifact") if isinstance(ex.get("applied_artifact"), dict) else {}
        scope = ex.get("execution_scope") if isinstance(ex.get("execution_scope"), dict) else {}
        lineage = ex.get("lineage") if isinstance(ex.get("lineage"), dict) else {}

        execution_status = str(ex.get("execution_status", ""))
        artifact_hash = artifact.get("artifact_hash")
        packet_id = ex.get("packet_id")

        replayable = execution_status == "completed"
        replay_key = _sha({"execution_id": ex.get("execution_id"), "artifact_hash": artifact_hash}) if artifact_hash else None
        rollback_key = _sha({"execution_id": ex.get("execution_id")}) if execution_status == "completed" else None

        entry = {
            "entry_version": "CanaryObservationLedgerEntry.v1",
            "observation_id": None,
            "execution_id": ex.get("execution_id"),
            "packet_id": packet_id,
            "source_key": str(ex.get("source_key", "")),
            "execution_status": execution_status,
            "artifact": {
                "artifact_hash": artifact_hash,
                "artifact_path": artifact.get("artifact_path"),
            },
            "sandbox": {
                "scope_id": str(scope.get("scope_id", "")),
                "sandbox_root": execution_run_obj.get("execution_scope", {}).get("sandbox_root"),
                "receipt_path": artifact.get("artifact_path"),
            },
            "execution": {
                "created_at": execution_run_obj.get("created_at", ""),
                "mode": "sandbox" if artifact.get("artifact_path") else "in_memory",
                "failure_reason": ex.get("reason"),
                "blocked_reason": ex.get("reason"),
            },
            "replay": {
                "replayable": replayable,
                "replay_key": replay_key,
            },
            "rollback": {
                "rollback_prepared": False,
                "rollback_key": rollback_key,
            },
            "lineage": {
                "execution_hash": _sha(ex),
                "packet_hash": _sha({"packet_id": packet_id}) if packet_id is not None else None,
            },
            "authority": dict(AUTHORITY_FLAGS),
        }

        obs_hash_payload = {
            "execution_id": entry["execution_id"],
            "packet_id": entry["packet_id"],
            "source_key": entry["source_key"],
            "execution_status": entry["execution_status"],
            "artifact": entry["artifact"],
            "sandbox": entry["sandbox"],
            "execution": {
                "mode": entry["execution"]["mode"],
                "failure_reason": entry["execution"]["failure_reason"],
                "blocked_reason": entry["execution"]["blocked_reason"],
            },
            "replay": entry["replay"],
            "rollback": entry["rollback"],
            "lineage": entry["lineage"],
            "authority": entry["authority"],
        }
        entry["observation_id"] = _sha(obs_hash_payload)

        if entry["observation_id"] in prev_by_obs:
            existing += 1
            continue
        created.append(entry)

    merged_entries = list(prev_by_obs.values()) + created
    merged_entries = sorted(merged_entries, key=lambda e: (str(e.get("source_key", "")), str(e.get("observation_id", ""))))

    return {
        "artifact": "CANARY-OBSERVATION-LEDGER-001",
        "schema_version": "CanaryObservationLedgerRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": {
            "executions_total": len(executions),
            "entries_created": len(created),
            "entries_existing": existing,
            "entries_total": len(merged_entries),
        },
        "entries": merged_entries,
    }
