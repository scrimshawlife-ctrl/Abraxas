from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .runplan import RunPlan


Tier = Literal["psychonaut", "academic", "enterprise"]
Lane = Literal["canon", "shadow", "sandbox"]
ProvStatus = Literal["complete", "partial", "missing"]
InvStatus = Literal["pass", "fail", "not_evaluated"]
RentStatus = Literal["paid", "unpaid", "not_applicable"]

InteractionMode = Literal[
    "clarify", "deliberate", "present_options", "observe_only", "execute", "defer"
]

AckMode = Literal["explicit_yes", "signed_token", "ui_confirm"]

PauseReason = Literal[
    "quota_exhausted",
    "early_pause_triggered",
    "human_revoked",
    "completed",
    "awaiting_ack",
    "packet_rejected",
    "invariance_failed",
    "drift_escalated",
]


class NotComputableRegion(BaseModel):
    region_id: str
    reason_code: str
    notes: Optional[str] = None


class AbraxasSignalPacket(BaseModel):
    signal_id: str
    timestamp_utc: str
    tier: Tier
    lane: Lane
    payload: Dict[str, Any]
    confidence: Dict[str, Any]
    provenance_status: ProvStatus
    invariance_status: InvStatus
    drift_flags: List[str] = Field(default_factory=list)
    rent_status: RentStatus
    not_computable_regions: List[NotComputableRegion] = Field(default_factory=list)


class RiskProfile(BaseModel):
    risk_of_action: Literal["low", "medium", "high"]
    risk_of_inaction: Literal["low", "medium", "high"]
    risk_notes: str


class DecisionContext(BaseModel):
    context_id: str
    source_signal_id: str
    created_at_utc: str
    stable_elements: List[Any] = Field(default_factory=list)
    unstable_elements: List[Any] = Field(default_factory=list)
    unknowns: List[Any] = Field(default_factory=list)
    assumptions_inherited: List[Any] = Field(default_factory=list)
    execution_lanes_allowed: List[Literal["canon", "shadow"]] = Field(default_factory=list)
    risk_profile: RiskProfile
    requires_human_confirmation: bool
    recommended_interaction_mode: InteractionMode
    policy_basis: Dict[str, Any] = Field(default_factory=dict)


class HumanAck(BaseModel):
    ack_mode: AckMode
    ack_id: str
    ack_timestamp_utc: str


class DeferralStart(BaseModel):
    quota_max_actions: Literal[2, 3]


class RunSummary(BaseModel):
    run_id: str
    signal_id: str
    tier: Tier
    lane: Lane
    phase: int
    pause_required: bool
    pause_reason: Optional[PauseReason] = None
    created_at_utc: str


class RunState(BaseModel):
    run_id: str
    created_at_utc: str
    phase: int

    signal: AbraxasSignalPacket
    context: DecisionContext

    requires_human_confirmation: bool
    human_ack: Optional[HumanAck] = None

    deferral_active: bool = False
    quota_max_actions: Optional[int] = None
    actions_taken: int = 0

    pause_required: bool = False
    pause_reason: Optional[PauseReason] = None
    runplan: Optional[RunPlan] = None
    current_step_index: int = 0
    last_step_result: Optional[Dict[str, Any]] = None
    step_results: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def actions_remaining(self) -> Optional[int]:
        if not self.deferral_active or self.quota_max_actions is None:
            return None
        return max(0, self.quota_max_actions - self.actions_taken)
