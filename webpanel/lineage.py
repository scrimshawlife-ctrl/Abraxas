from __future__ import annotations

from typing import List, Set

from webpanel.models import RunState


def get_lineage(run_id: str, store, max_hops: int = 10) -> List[RunState]:
    lineage: List[RunState] = []
    visited: Set[str] = set()
    current_id = run_id
    hops = 0
    while current_id and hops < max_hops:
        if current_id in visited:
            break
        visited.add(current_id)
        run = store.get(current_id)
        if run is None:
            break
        lineage.append(run)
        current_id = run.prev_run_id or ""
        hops += 1
    return lineage
