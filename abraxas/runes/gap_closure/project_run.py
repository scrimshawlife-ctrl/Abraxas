from __future__ import annotations

from typing import Any

from .runtime import build_gap_closure_cycle


def run_projection_cycle(
    *,
    run_id: str,
    mode: str,
    workspace_only: bool,
    required_input: dict[str, Any] | None,
) -> dict[str, Any]:
    return build_gap_closure_cycle(
        run_id=run_id,
        mode=mode,
        workspace_only=workspace_only,
        required_input=required_input,
    )
