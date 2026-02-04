from __future__ import annotations

from typing import Dict, List, Optional

from .models import RunState, RunSummary


class InMemoryStore:
    def __init__(self) -> None:
        self._runs: Dict[str, RunState] = {}

    def put(self, run: RunState) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: str) -> Optional[RunState]:
        return self._runs.get(run_id)

    def list(self, limit: int = 50) -> List[RunSummary]:
        runs = list(self._runs.values())
        runs.sort(key=lambda r: r.created_at_utc, reverse=True)
        out: List[RunSummary] = []
        for r in runs[:limit]:
            out.append(
                RunSummary(
                    run_id=r.run_id,
                    signal_id=r.signal.signal_id,
                    tier=r.signal.tier,
                    lane=r.signal.lane,
                    phase=r.phase,
                    pause_required=r.pause_required,
                    pause_reason=r.pause_reason,
                    created_at_utc=r.created_at_utc,
                )
            )
        return out
