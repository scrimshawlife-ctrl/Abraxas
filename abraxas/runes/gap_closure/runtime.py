from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abraxas.core.canonical import canonical_json, sha256_hex

REQUIRED_ARTIFACTS = (
    "gap_closure_run.json",
    "live_run_projection.json",
    "closure_validation_report.json",
)


def write_canonical_json(path: Path, payload: dict[str, Any]) -> str:
    serialized = canonical_json(payload) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")
    return sha256_hex(serialized)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_record(
    *,
    run_id: str,
    artifact_path: str,
    artifact_hash: str,
    provenance: dict[str, Any],
    input_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": "gap_closure_artifact.v1",
        "run_id": run_id,
        "artifact_path": artifact_path,
        "artifact_hash": artifact_hash,
        "provenance": provenance,
        "input_hash": input_hash,
    }


def _build_projection(run_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "live_run_projection.v1",
        "run_id": run_record["run_id"],
        "status": run_record["status"],
        "input_hash": run_record["input_hash"],
        "authority_boundary": "projection cannot alter canon status",
        "projection_notice": "projection cannot alter canon status",
        "provenance": run_record["provenance"],
    }


def _build_bridge(run_record: dict[str, Any]) -> dict[str, Any]:
    bridge_basis = {
        "run_id": run_record["run_id"],
        "input_hash": run_record["input_hash"],
        "oracle_status": "DERIVED_ONLY",
        "gap_status": run_record["status"],
    }
    return {
        "schema_version": "oracle_gap_bridge.v1",
        "bridge_id": sha256_hex(canonical_json(bridge_basis))[:16],
        **bridge_basis,
    }


def build_gap_closure_cycle(
    *,
    run_id: str,
    mode: str,
    workspace_only: bool,
    required_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    input_payload = {
        "mode": mode,
        "required_input": required_input,
        "run_id": run_id,
        "workspace_only": workspace_only,
    }
    input_hash = sha256_hex(canonical_json(input_payload))
    status = "COMPLETE" if required_input is not None else "NOT_COMPUTABLE"
    provenance = {
        "lane": "forecast-active",
        "mode": mode,
        "workspace_only": workspace_only,
    }
    run_record = {
        "schema_version": "gap_closure_run.v1",
        "run_id": run_id,
        "input_hash": input_hash,
        "provenance": provenance,
        "status": status,
    }
    projection = _build_projection(run_record)
    bridge = _build_bridge(run_record)
    return {
        "input_hash": input_hash,
        "run_record": run_record,
        "projection": projection,
        "bridge": bridge,
        "status": status,
    }


def build_artifact_index(
    *,
    run_id: str,
    provenance: dict[str, Any],
    input_hash: str,
    run_artifact: tuple[str, str],
    projection_artifact: tuple[str, str],
    validation_artifact: tuple[str, str],
) -> list[dict[str, Any]]:
    artifacts = [run_artifact, projection_artifact, validation_artifact]
    return [
        _artifact_record(
            run_id=run_id,
            artifact_path=path,
            artifact_hash=artifact_hash,
            provenance=provenance,
            input_hash=input_hash,
        )
        for path, artifact_hash in artifacts
    ]
