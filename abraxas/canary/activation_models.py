from __future__ import annotations

from dataclasses import dataclass

AUTHORITY_FLAGS = {
    "activation_packet_generation": True,
    "overlay_activation": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}


@dataclass(frozen=True)
class ActivationPacket:
    packet_id: str
    overlay_id: str
    entry_id: str | None
    proposal_id: str | None
    source_key: str
    recommendation_status: str
    summary: dict
    evidence: dict
    lineage: dict

    def to_dict(self) -> dict:
        return {
            "packet_version": "CanaryActivationPacket.v1",
            "packet_id": self.packet_id,
            "overlay_id": self.overlay_id,
            "entry_id": self.entry_id,
            "proposal_id": self.proposal_id,
            "source_key": self.source_key,
            "recommendation_status": self.recommendation_status,
            "packet_status": "pending_review",
            "summary": self.summary,
            "evidence": self.evidence,
            "lineage": self.lineage,
            "review": {
                "reviewer_notes": [],
                "approval_status": "unreviewed",
                "decision_reason": None,
            },
            "authority": dict(AUTHORITY_FLAGS),
        }
