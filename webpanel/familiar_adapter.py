from __future__ import annotations

from typing import Tuple

from .core_bridge import core_ingest
from .models import AbraxasSignalPacket, RunState


class FamiliarAdapter:
    """
    Thin adapter that will later call the real ABX-Familiar engine.
    For now, it enforces the lifecycle gates and creates a minimal DecisionContext.
    """

    def ingest(self, packet: AbraxasSignalPacket) -> Tuple[RunState, str]:
        payload = packet.model_dump()
        result = core_ingest(payload)
        run = RunState.model_validate(result)
        return run, run.context.context_id
