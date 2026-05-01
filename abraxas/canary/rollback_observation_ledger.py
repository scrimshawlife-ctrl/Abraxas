from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.rollback_observation_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_rollback_observation_ledger(
    execution_run: Mapping[str, Any],
    prior_ledger: Mapping[str, Any] | None = None,
) -> dict:
    ex_data = deepcopy(dict(execution_run))
    prior_data = deepcopy(dict(prior_ledger)) if prior_ledger is not None else {}

    executions = ex_data.get("executions") if isinstance(ex_data.get("executions"), list) else []
    prior_obs = prior_data.get("observations") if isinstance(prior_data.get("observations"), list) else []
    prior_by_id = {str(o.get("observation_id")): o for o in prior_obs if isinstance(o, dict) and o.get("observation_id")}

    created: list[dict] = []
    existing = 0

    for ex in executions:
        if not isinstance(ex, dict):
            continue
        artifact = ex.get("artifact") if isinstance(ex.get("artifact"), dict) else {}
        scope = ex.get("scope") if isinstance(ex.get("scope"), dict) else {}

        obs_hash_payload = {
            "execution_id": ex.get("execution_id"),
            "packet_id": ex.get("packet_id"),
            "rollback_id": ex.get("rollback_id"),
            "source_key": ex.get("source_key"),
            "execution_status": ex.get("execution_status"),
            "mode": ex.get("mode"),
            "artifact_hash": artifact.get("artifact_hash"),
            "scope_id": scope.get("scope_id"),
        }
        observation_id = _sha(obs_hash_payload)

        entry = {
            "observation_version": "CanaryRollbackObservationLedgerEntry.v1",
            "observation_id": observation_id,
            "execution_id": ex.get("execution_id"),
            "packet_id": ex.get("packet_id"),
            "rollback_id": ex.get("rollback_id"),
            "observation_source_id": ex.get("execution_source_id"),
            "source_key": str(ex.get("source_key", "")),
            "execution_status": ex.get("execution_status"),
            "mode": ex.get("mode"),
            "artifact": {
                "artifact_hash": artifact.get("artifact_hash"),
                "artifact_path": artifact.get("artifact_path"),
            },
            "scope": {
                "scope_id": scope.get("scope_id"),
                "sandbox_root": scope.get("sandbox_root"),
            },
            "replay": {
                "replayable": ex.get("execution_status") == "completed",
                "replay_key": artifact.get("artifact_hash") if artifact.get("artifact_hash") is not None else None,
            },
            "rollback": {
                "rollback_prepared": False,
                "rollback_key": artifact.get("artifact_hash") if ex.get("execution_status") == "completed" else None,
            },
            "audit": {
                "execution_hash": (ex.get("lineage") if isinstance(ex.get("lineage"), dict) else {}).get("execution_hash") or _sha(ex),
                "packet_hash": (ex.get("lineage") if isinstance(ex.get("lineage"), dict) else {}).get("rollback_packet_hash"),
            },
            "lineage": {
                "execution_id": ex.get("execution_id"),
                "packet_id": ex.get("packet_id"),
                "rollback_id": ex.get("rollback_id"),
            },
            "authority": dict(AUTHORITY_FLAGS),
        }

        if observation_id in prior_by_id:
            existing += 1
            continue
        created.append(entry)

    observations = list(prior_by_id.values()) + created
    observations = sorted(observations, key=lambda o: (str(o.get("source_key", "")), str(o.get("observation_id", ""))))

    return {
        "artifact": "CANARY-ROLLBACK-OBSERVATION-LEDGER-001",
        "schema_version": "CanaryRollbackObservationLedgerRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": {
            "executions_total": len(executions),
            "observations_created": len(created),
            "observations_existing": existing,
            "observations_total": len(observations),
        },
        "observations": observations,
    }
