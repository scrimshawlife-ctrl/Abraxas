from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class AdapterTransformRecord:
    adapter_id: str
    source_type: str
    target_type: str
    lossy: bool
    notes: str = ""


@dataclass(frozen=True)
class ResonanceFrame:
    frame_type: str
    frame_id: str
    run_id: str
    scenario_id: str
    phase: str
    lane: str
    scheduler_context: dict[str, Any]
    lineage: dict[str, Any]
    status: dict[str, Any]
    evidence: dict[str, Any]
    payload: dict[str, Any]
    continuity: dict[str, Any]
    adapter_records: list[AdapterTransformRecord] = field(default_factory=list)

    def stable_hash(self) -> str:
        payload = {
            "frame_id": self.frame_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "phase": self.phase,
            "lane": self.lane,
            "scheduler_context": self.scheduler_context,
            "lineage": self.lineage,
            "status": self.status,
            "evidence": self.evidence,
            "payload": self.payload,
            "continuity": self.continuity,
            "adapter_records": [r.__dict__ for r in self.adapter_records],
        }
        return sha256_bytes(dumps_stable(payload).encode("utf-8"))


@dataclass(frozen=True)
class FrameProjection:
    projection_type: str
    projection_id: str
    run_id: str
    scenario_id: str
    frame_hash: str
    summary: dict[str, Any]


def project_frame(frame: ResonanceFrame) -> FrameProjection:
    return FrameProjection(
        projection_type="FrameProjection.v1",
        projection_id=f"frame-projection-{frame.run_id}-{frame.scenario_id}",
        run_id=frame.run_id,
        scenario_id=frame.scenario_id,
        frame_hash=frame.stable_hash(),
        summary={
            "phase": frame.phase,
            "lane": frame.lane,
            "proof_status": frame.status.get("proof_chain_status"),
            "validation_status": frame.status.get("validation_status"),
            "closure_status": frame.status.get("closure_status"),
            "portfolio": frame.payload.get("portfolio"),
            "scheduler_policy": frame.scheduler_context.get("policy_id"),
        },
    )
