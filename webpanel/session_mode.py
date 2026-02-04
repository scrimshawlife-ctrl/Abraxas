from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional


class SessionGateError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _hash_session_id(run_id: str, started_utc: str) -> str:
    payload = f"{run_id}|{started_utc}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def start_session(
    *,
    run: Any,
    max_steps: int,
    started_utc: str,
    ledger,
    event_id: str,
) -> None:
    max_steps = max(1, min(5, int(max_steps)))
    session_id = _hash_session_id(run.run_id, started_utc)
    run.session_active = True
    run.session_id = session_id
    run.session_max_steps = max_steps
    run.session_steps_used = 0
    run.session_started_utc = started_utc
    ledger.append(
        run.run_id,
        event_id,
        "session_start",
        started_utc,
        {"session_id": session_id, "max_steps": max_steps, "started_utc": started_utc},
    )


def end_session(
    *,
    run: Any,
    ended_utc: str,
    ledger,
    event_id: str,
    reason: str,
) -> None:
    session_id = getattr(run, "session_id", None)
    run.session_active = False
    ledger.append(
        run.run_id,
        event_id,
        "session_end",
        ended_utc,
        {
            "session_id": session_id,
            "used": int(getattr(run, "session_steps_used", 0)),
            "ended_utc": ended_utc,
            "reason": reason,
        },
    )


def enforce_session(run: Any) -> None:
    max_steps = int(getattr(run, "session_max_steps", 0) or 0)
    used = int(getattr(run, "session_steps_used", 0) or 0)
    if max_steps > 0 and used >= max_steps:
        raise SessionGateError("session_exhausted")
    if not bool(getattr(run, "session_active", False)):
        raise SessionGateError("session_required")


def consume_session_step(
    *,
    run: Any,
    ledger,
    event_id: str,
    end_event_id: str,
    timestamp_utc: str,
    route: str,
    step_index: int,
) -> None:
    run.session_steps_used = int(getattr(run, "session_steps_used", 0) or 0) + 1
    max_steps = int(getattr(run, "session_max_steps", 0) or 0)
    used = int(run.session_steps_used)
    remaining = max(0, max_steps - used)
    ledger.append(
        run.run_id,
        event_id,
        "session_step",
        timestamp_utc,
        {
            "session_id": getattr(run, "session_id", None),
            "step_index": step_index,
            "used": used,
            "remaining": remaining,
            "timestamp_utc": timestamp_utc,
            "route": route,
        },
    )
    if max_steps > 0 and used >= max_steps:
        end_session(
            run=run,
            ended_utc=timestamp_utc,
            ledger=ledger,
            event_id=end_event_id,
            reason="exhausted",
        )
