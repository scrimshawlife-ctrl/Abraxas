"""Test-support: put a run into an active session.

The panel gates session-dependent steps behind ``session_mode.enforce_session``, which
raises ``session_required`` when ``run.session_active`` is false. The webpanel tests in
this package exercise those steps but predate the gate, so they never activated a
session -- they could not run at all (the app itself failed to build), and once it built
they failed with ``session_required``.

This mirrors the pattern already used by tests/test_session_mode_v0.py, which calls
``start_session`` directly. Kept in one place so the twelve call sites cannot drift
apart, and named with a leading underscore so pytest does not try to collect it.
"""

from __future__ import annotations

from typing import Any, Optional

TEST_SESSION_STARTED_UTC = "2026-02-03T00:00:00+00:00"


def start_test_session(run: Any, *, max_steps: int = 5, ledger: Optional[Any] = None, event_id: str = "ev_test_session") -> None:
    """Activate a session on ``run`` so session-gated steps are reachable.

    Only sets the session state -- it does not consume steps, so a test that exercises
    quota behaviour still observes the full budget.
    """
    from webpanel.ledger import LedgerChain
    from webpanel.session_mode import start_session

    start_session(
        run=run,
        max_steps=max_steps,
        started_utc=TEST_SESSION_STARTED_UTC,
        ledger=ledger if ledger is not None else LedgerChain(),
        event_id=event_id,
    )


def start_test_session_http(client: Any, run_id: str, *, max_steps: int = 5) -> None:
    """Open a session over HTTP, the way a real operator does.

    The panel exposes POST /ui/runs/{run_id}/session/start, guarded by require_token.
    Tests that drive the panel through TestClient must use it, because the gate is
    enforced in the route layer -- activating the session on the RunState object
    directly does not reach that path.

    This route had no test coverage at all before this: the session gate was added and
    every caller of a gated step predated it, so nothing exercised the sanctioned way
    to open a session.
    """
    resp = client.post(f"/ui/runs/{run_id}/session/start", data={"session_max_steps": str(max_steps)})
    if resp.status_code not in (200, 303):
        raise AssertionError(
            f"session start failed: {resp.status_code} {resp.text[:200]}"
        )
