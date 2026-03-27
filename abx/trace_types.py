from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExecutionTraceEvent(BaseModel):
    rune_id: str
    capability: str
    status: str
    input_hash: str
    output_hash: str | None = None
    order: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionTrace(BaseModel):
    run_id: str
    events: list[ExecutionTraceEvent] = Field(default_factory=list)

    def deterministic_view(self) -> list[ExecutionTraceEvent]:
        return sorted(self.events, key=lambda e: (int(e.order), str(e.rune_id)))
