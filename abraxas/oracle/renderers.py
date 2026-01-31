from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from aal_core.aalmanac.oracle_attachment import summarize_rejections
from aal_core.aalmanac.storage.entries import load_entries
from aal_core.neon_genie.pipeline import load_latest_signal
from abraxas.oracle.render_aalmanac import render_aalmanac_block
from abraxas.oracle.render_neon_genie import render_neon_genie_block


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
    entries = load_entries()
    rejections = summarize_rejections()
    if entries:
        lines.extend(["", render_aalmanac_block(entries, rejections=rejections)])
    neon_signal = load_latest_signal()
    neon_block = render_neon_genie_block(neon_signal)
    if neon_block:
        lines.extend(["", neon_block])
    return RenderedOutput(markdown="\n".join(lines))
