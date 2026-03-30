from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from abx.continuity.continuityScorecard import build_mission_continuity_scorecard
from abx.runtime_trade_ledger import load_runtime_trade_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class ContinuityRecord:
    run_id: str
    scenario_id: str
    previous_run_id: str | None
    persisted_surfaces: list[str]
    non_persisted_surfaces: list[str]


@dataclass(frozen=True)
class ContinuitySummaryArtifact:
    artifact_type: str
    artifact_id: str
    run_id: str
    scenario_id: str
    continuity_status: str
    chain: list[str]
    summary_hash: str


def build_continuity_record(payload: dict[str, Any]) -> ContinuityRecord:
    return ContinuityRecord(
        run_id=str(payload.get("run_id") or "RUN-CONT"),
        scenario_id=str(payload.get("scenario_id") or "SCN-CONT"),
        previous_run_id=(str(payload.get("previous_run_id")) if payload.get("previous_run_id") else None),
        persisted_surfaces=["runtime_trade_ledger", "closure_summary", "proof_chain"],
        non_persisted_surfaces=["raw_operator_stdout"],
    )


def build_continuity_summary(*, base_dir: Path, payload: dict[str, Any]) -> ContinuitySummaryArtifact:
    record = build_continuity_record(payload)
    chain = [record.run_id]
    if record.previous_run_id:
        chain.insert(0, record.previous_run_id)

    rows = load_runtime_trade_records(base_dir, record.run_id, record.scenario_id)
    status = "VALID" if rows else "PARTIAL"
    if record.previous_run_id and not rows:
        status = "BROKEN"

    hash_payload = {
        "run_id": record.run_id,
        "scenario_id": record.scenario_id,
        "previous_run_id": record.previous_run_id,
        "chain": chain,
        "status": status,
    }
    summary_hash = sha256_bytes(dumps_stable(hash_payload).encode("utf-8"))

    return ContinuitySummaryArtifact(
        artifact_type="ContinuitySummaryArtifact.v1",
        artifact_id=f"continuity-summary-{record.run_id}-{record.scenario_id}",
        run_id=record.run_id,
        scenario_id=record.scenario_id,
        continuity_status=status,
        chain=chain,
        summary_hash=summary_hash,
    )


__all__ = [
    "ContinuityRecord",
    "ContinuitySummaryArtifact",
    "build_continuity_record",
    "build_continuity_summary",
    "build_mission_continuity_scorecard",
]
