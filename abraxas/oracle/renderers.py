from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RenderedOutput:
    markdown: str


def render_from_signal_v2(signal: Dict[str, Any], *, mode: str) -> RenderedOutput:
    """
    Minimal renderer for oracle batch packaging.
    """
    osv2 = signal.get("oracle_signal_v2") or {}
    meta = osv2.get("meta") or {}
    lines = [
        "# Oracle Output",
        "",
        f"- Mode: {mode}",
        f"- Slice Hash: {meta.get('slice_hash', '')}",
    ]
    return RenderedOutput(markdown="\n".join(lines))
