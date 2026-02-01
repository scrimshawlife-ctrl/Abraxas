from __future__ import annotations

from typing import Any, Dict


def assert_mode_lock(v2_block: Dict[str, Any]) -> None:
    """
    Hard invariant:
      oracle_signal.v2.mode must equal oracle_signal.v2.mode_decision.mode

    If this fails, the pipeline has allowed an illegal divergence.
    """
    mode = v2_block.get("mode")
    md = v2_block.get("mode_decision") or {}
    decided = md.get("mode")
    if mode != decided:
        raise ValueError(f"v2 mode lock violated: mode={mode!r} decision.mode={decided!r}")
