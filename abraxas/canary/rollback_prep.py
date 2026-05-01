from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.rollback_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_rollback_prep(observation_run: Mapping[str, Any]) -> dict:
    data = deepcopy(dict(observation_run))
    entries = data.get("entries") if isinstance(data.get("entries"), list) else []

    rollbacks: list[dict] = []
    prepared = 0
    not_computable = 0

    for obs in entries:
        if not isinstance(obs, dict):
            continue
        execution = obs.get("execution") if isinstance(obs.get("execution"), dict) else {}
        artifact = obs.get("artifact") if isinstance(obs.get("artifact"), dict) else {}
        replay = obs.get("replay") if isinstance(obs.get("replay"), dict) else {}
        rollback = obs.get("rollback") if isinstance(obs.get("rollback"), dict) else {}
        lineage = obs.get("lineage") if isinstance(obs.get("lineage"), dict) else {}

        reason = None
        status = "prepared"
        replayable = bool(replay.get("replayable"))
        rollback_key = rollback.get("rollback_key")

        if obs.get("execution_status") != "completed":
            status = "not_computable"
            reason = "execution_not_completed"
        elif replayable is not True:
            status = "not_computable"
            reason = "not_replayable"
        elif rollback_key is None:
            status = "not_computable"
            reason = "missing_rollback_key"

        if status == "prepared":
            prepared += 1
            safety = {"replayable": replayable, "rollback_prepared": True, "reason": None}
        else:
            not_computable += 1
            safety = {"replayable": replayable, "rollback_prepared": False, "reason": reason}

        rollback_plan = {
            "mode": "deterministic_replay",
            "requires_artifact": artifact.get("artifact_hash") is not None,
            "artifact_hash": artifact.get("artifact_hash"),
            "artifact_path": artifact.get("artifact_path"),
        }
        lineage_obj = {
            "observation_hash": _sha(obs),
            "execution_hash": lineage.get("execution_hash"),
        }

        rollback_id = _sha(
            {
                "observation_id": obs.get("observation_id"),
                "execution_id": obs.get("execution_id"),
                "source_key": obs.get("source_key"),
                "rollback_key": rollback_key,
                "rollback_plan": rollback_plan,
                "safety": safety,
                "lineage": lineage_obj,
                "authority": dict(AUTHORITY_FLAGS),
            }
        )

        rollbacks.append(
            {
                "rollback_version": "CanaryRollbackPrep.v1",
                "rollback_id": rollback_id,
                "observation_id": obs.get("observation_id"),
                "execution_id": obs.get("execution_id"),
                "source_key": str(obs.get("source_key", "")),
                "rollback_key": rollback_key,
                "status": status,
                "rollback_plan": rollback_plan,
                "safety": safety,
                "lineage": lineage_obj,
                "authority": dict(AUTHORITY_FLAGS),
            }
        )

    rollbacks = sorted(rollbacks, key=lambda r: (r["source_key"], r["rollback_id"]))

    return {
        "artifact": "CANARY-ROLLBACK-PREP-001",
        "schema_version": "CanaryRollbackPrepRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": {
            "observations_total": len(entries),
            "prepared": prepared,
            "not_computable": not_computable,
        },
        "rollbacks": rollbacks,
    }
