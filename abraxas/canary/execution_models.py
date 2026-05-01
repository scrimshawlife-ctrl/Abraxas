from __future__ import annotations

from dataclasses import dataclass

RUN_AUTHORITY = {
    "canary_activation": True,
    "baseline_mutation": False,
    "runtime_write": False,
    "scheduler_registration": False,
    "promotion": False,
    "production_execution": False,
}

SKIP_AUTHORITY = {
    "canary_activation": False,
    "baseline_mutation": False,
    "runtime_write": False,
    "scheduler_registration": False,
    "promotion": False,
    "production_execution": False,
}


@dataclass(frozen=True)
class CanaryActivationExecution:
    execution_id: str
    packet_id: str
    source_key: str
    overlay_id: str
    overlay_hash: str
    simulation_hash: str
    recommendation_id: str
    ledger_entry_hash: str | None
    execution_scope: dict
    applied_artifact: dict
    evidence: dict
    lineage: dict
    reason: str | None

    def to_dict(self) -> dict:
        return {
            "schema_version": "CanaryActivationExecution.v1",
            "execution_id": self.execution_id,
            "packet_id": self.packet_id,
            "source_key": self.source_key,
            "overlay_id": self.overlay_id,
            "overlay_hash": self.overlay_hash,
            "simulation_hash": self.simulation_hash,
            "recommendation_id": self.recommendation_id,
            "ledger_entry_hash": self.ledger_entry_hash,
            "execution_status": "canary_applied",
            "execution_scope": self.execution_scope,
            "authority": dict(RUN_AUTHORITY),
            "applied_artifact": self.applied_artifact,
            "evidence": self.evidence,
            "lineage": self.lineage,
            "reason": self.reason,
        }


def build_skipped(packet: dict | None, reason: str) -> dict:
    packet = packet or {}
    return {
        "schema_version": "CanaryActivationSkipped.v1",
        "packet_id": packet.get("packet_id"),
        "source_key": packet.get("source_key"),
        "overlay_id": packet.get("overlay_id"),
        "reason": reason,
        "authority": dict(SKIP_AUTHORITY),
    }
