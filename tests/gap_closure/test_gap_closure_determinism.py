from __future__ import annotations

from abraxas.runes.gap_closure.project_run import run_projection_cycle


def test_gap_closure_determinism() -> None:
    cycle_a = run_projection_cycle(
        run_id="RUN-GAP-FIRST-0001",
        mode="sandbox",
        workspace_only=True,
        required_input={"input_state": "present"},
    )
    cycle_b = run_projection_cycle(
        run_id="RUN-GAP-FIRST-0001",
        mode="sandbox",
        workspace_only=True,
        required_input={"input_state": "present"},
    )
    assert cycle_a["input_hash"] == cycle_b["input_hash"]
