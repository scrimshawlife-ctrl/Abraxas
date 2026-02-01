from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RenderedMode:
    markdown: str


def render_mode(out: Dict[str, Any], *, mode: str) -> RenderedMode:
    """
    Deterministic markdown projection of MDA output.
    """
    env = (out.get("envelope") or {}).get("env", "")
    run_at = (out.get("envelope") or {}).get("run_at_iso", "")
    input_hash = (out.get("envelope") or {}).get("input_hash", "")
    dsp = out.get("dsp") or []

    lines = [
        f"# MDA ({mode})",
        "",
        f"- env: {env}",
        f"- run_at: {run_at}",
        f"- input_hash: {input_hash}",
        f"- dsp_count: {len(dsp)}",
        "",
    ]
    for item in dsp:
        lines.append(f"- {item.get('domain')}:{item.get('subdomain')} status={item.get('status')}")
    lines.append("")
    return RenderedMode(markdown="\n".join(lines))

