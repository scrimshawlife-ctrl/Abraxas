from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Tuple

from .models import (
    AbraxasSignalPacket,
    DecisionContext,
    RiskProfile,
    RunState,
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class FamiliarAdapter:
    """
    Thin adapter that will later call the real ABX-Familiar engine.
    For now, it enforces the lifecycle gates and creates a minimal DecisionContext.
    """

    def ingest(self, packet: AbraxasSignalPacket) -> Tuple[RunState, str]:
        run_id = new_id("run")
        context_id = new_id("ctx")

        requires_ack = (
            packet.invariance_status == "fail"
            or packet.provenance_status in ("partial", "missing")
            or len(packet.drift_flags) > 0
        )

        if packet.lane == "shadow":
            mode = "observe_only"
        elif requires_ack:
            mode = "deliberate"
        else:
            mode = "present_options"

        allowed_lanes = ["shadow"] if packet.lane == "shadow" else ["canon", "shadow"]

        ctx = DecisionContext(
            context_id=context_id,
            source_signal_id=packet.signal_id,
            created_at_utc=now_utc(),
            stable_elements=[],
            unstable_elements=[],
            unknowns=[
                {"region_id": r.region_id, "reason_code": r.reason_code}
                for r in packet.not_computable_regions
            ],
            assumptions_inherited=[],
            execution_lanes_allowed=allowed_lanes,  # type: ignore[arg-type]
            risk_profile=RiskProfile(
                risk_of_action="medium",
                risk_of_inaction="medium",
                risk_notes="mvp: risk profile is structural until full policy wiring is present",
            ),
            requires_human_confirmation=requires_ack,
            recommended_interaction_mode=mode,  # type: ignore[arg-type]
            policy_basis={"mvp": True},
        )

        run = RunState(
            run_id=run_id,
            created_at_utc=now_utc(),
            phase=2,
            signal=packet,
            context=ctx,
            requires_human_confirmation=requires_ack,
            human_ack=None,
            deferral_active=False,
            quota_max_actions=None,
            actions_taken=0,
            pause_required=requires_ack,
            pause_reason="awaiting_ack" if requires_ack else None,
        )
        return run, context_id
