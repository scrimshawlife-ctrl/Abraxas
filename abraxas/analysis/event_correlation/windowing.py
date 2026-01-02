from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _created_at(env: Dict[str, Any]) -> Optional[str]:
    v = env.get("created_at") or env.get("createdAt") or env.get("created_at_utc") or env.get("createdAtUtc")
    return v if isinstance(v, str) and len(v) >= 10 else None


@dataclass(frozen=True)
class WindowInfo:
    start_created_at: Optional[str]
    end_created_at: Optional[str]
    artifact_count: int


def compute_window(envelopes: List[Dict[str, Any]]) -> WindowInfo:
    ts = [t for t in (_created_at(e) for e in envelopes) if t is not None]
    ts_sorted = sorted(ts)
    if not ts_sorted:
        return WindowInfo(start_created_at=None, end_created_at=None, artifact_count=len(envelopes))
    return WindowInfo(
        start_created_at=ts_sorted[0],
        end_created_at=ts_sorted[-1],
        artifact_count=len(envelopes),
    )


def stable_sort_envelopes(envelopes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Deterministic ordering: created_at then artifact_id then canonical fallback
    def key(env: Dict[str, Any]) -> Tuple[str, str]:
        created = _created_at(env) or ""
        aid = str(env.get("artifact_id") or env.get("id") or env.get("artifactId") or env.get("run_id") or "")
        return (created, aid)

    return sorted(envelopes, key=key)

