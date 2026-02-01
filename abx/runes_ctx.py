"""ABX helpers for constructing RuneInvocationContext.

ABX is allowed to import `abraxas.runes.*` to communicate across subsystem
boundaries via capability contracts.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache

from abraxas.runes.ctx import RuneInvocationContext


@lru_cache(maxsize=1)
def _git_hash() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, timeout=2)
            .decode("utf-8")
            .strip()
        )
    except Exception:
        return "unknown"


def build_rune_ctx(*, run_id: str, subsystem_id: str) -> RuneInvocationContext:
    return RuneInvocationContext(run_id=run_id, subsystem_id=subsystem_id, git_hash=_git_hash())


__all__ = ["build_rune_ctx"]

