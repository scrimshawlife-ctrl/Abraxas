from __future__ import annotations

from abraxas.runes.gap_closure.project_run import run_projection_cycle


def test_live_run_projection_boundary() -> None:
    cycle = run_projection_cycle(
        run_id="RUN-GAP-FIRST-0001",
        mode="sandbox",
        workspace_only=True,
        required_input={"input_state": "present"},
    )
    assert cycle["projection"]["authority_boundary"] == "projection cannot alter canon status"
