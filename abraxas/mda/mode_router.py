from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal


Mode = Literal["oracle", "ritual", "analyst"]


@dataclass(frozen=True)
class RenderedMode:
    mode: Mode
    markdown: str


def _md_kv(k: str, v: Any) -> str:
    return f"- **{k}**: {v}"


def render_oracle_log(payload: Dict[str, Any]) -> str:
    env = payload.get("envelope", {})
    aggs = payload.get("domain_aggregates", {})
    fusion = payload.get("fusion_graph", {})

    lines: List[str] = []
    lines.append("# Oracle Log")
    lines.append("")
    lines.append("## Run Envelope")
    lines.append(_md_kv("env", env.get("env")))
    lines.append(_md_kv("run_at", env.get("run_at")))
    lines.append(_md_kv("seed", env.get("seed")))
    lines.append(_md_kv("input_hash", env.get("input_hash")))
    lines.append("")

    lines.append("## Domain Pressure Snapshot")
    for d, a in sorted(aggs.items(), key=lambda x: x[0]):
        s = (a or {}).get("scores", {})
        lines.append(f"### {d}")
        lines.append(_md_kv("status", (a or {}).get("status")))
        lines.append(_md_kv("impact", s.get("impact")))
        lines.append(_md_kv("velocity", s.get("velocity")))
        lines.append(_md_kv("uncertainty", s.get("uncertainty")))
        lines.append(_md_kv("polarity", s.get("polarity")))
        lines.append("")

    lines.append("## Fusion Graph Summary")
    lines.append(_md_kv("nodes", len((fusion or {}).get("nodes", {}) or {})))
    lines.append(_md_kv("edges", len((fusion or {}).get("edges", []) or [])))
    lines.append("")
    lines.append("> Note: Oracle Log is intentionally terse. It is a run record, not a story.")
    return "\n".join(lines) + "\n"


def render_ritual_map(payload: Dict[str, Any]) -> str:
    env = payload.get("envelope", {})
    dsps = payload.get("dsp", []) or []
    fusion = payload.get("fusion_graph", {}) or {}

    by_domain: Dict[str, Dict[str, int]] = {}
    for d in dsps:
        dom = d.get("domain", "unknown")
        sub = d.get("subdomain", "unknown")
        by_domain.setdefault(dom, {})
        by_domain[dom][sub] = by_domain[dom].get(sub, 0) + len(d.get("events", []) or [])

    lines: List[str] = []
    lines.append("# Ritual Map")
    lines.append("")
    lines.append("## Circle of Domains (Hierarchical)")
    lines.append(_md_kv("env", env.get("env")))
    lines.append(_md_kv("run_at", env.get("run_at")))
    lines.append("")

    for dom in sorted(by_domain.keys()):
        lines.append(f"### {dom}")
        for sub, evc in sorted(by_domain[dom].items(), key=lambda x: x[0]):
            lines.append(f"- **{sub}** → events: {evc}")
        lines.append("")

    lines.append("## Threads (Fusion Edges)")
    edges = fusion.get("edges", []) or []
    if not edges:
        lines.append("- *(none)*")
    else:
        for e in edges[:25]:
            lines.append(f"- `{e.get('edge_type')}` :: {e.get('src_id')} → {e.get('dst_id')}")
        if len(edges) > 25:
            lines.append(f"- … {len(edges) - 25} more")

    lines.append("")
    lines.append("> Ritual Map is a topology view: what’s connected, where density accumulates.")
    return "\n".join(lines) + "\n"


def render_analyst_console(payload: Dict[str, Any]) -> str:
    import json as _json

    env = payload.get("envelope", {})
    dsps = payload.get("dsp", []) or []
    fusion = payload.get("fusion_graph", {}) or {}

    lines: List[str] = []
    lines.append("# Analyst Console")
    lines.append("")
    lines.append("## Envelope")
    lines.append("```json")
    lines.append(_json.dumps(env, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")

    lines.append("## DSP Packs (Domain → Subdomain)")
    for d in dsps:
        scores = d.get("scores", {}) or {}
        lines.append(f"### {d.get('domain')}:{d.get('subdomain')}")
        lines.append(_md_kv("status", d.get("status")))
        lines.append(_md_kv("impact", scores.get("impact")))
        lines.append(_md_kv("velocity", scores.get("velocity")))
        lines.append(_md_kv("uncertainty", scores.get("uncertainty")))
        lines.append(_md_kv("polarity", scores.get("polarity")))
        lines.append(_md_kv("events", len(d.get("events", []) or [])))
        lines.append(_md_kv("evidence_refs", len(d.get("evidence_refs", []) or [])))
        lines.append("")

    lines.append("## Fusion Graph")
    lines.append(_md_kv("nodes", len((fusion.get("nodes", {}) or {}))))
    lines.append(_md_kv("edges", len((fusion.get("edges", []) or []))))
    lines.append("")
    lines.append("> Analyst Console is the machine view: counts, bounds, and contracts.")
    return "\n".join(lines) + "\n"


def render_mode(payload: Dict[str, Any], mode: Mode) -> RenderedMode:
    if mode == "oracle":
        return RenderedMode(mode=mode, markdown=render_oracle_log(payload))
    if mode == "ritual":
        return RenderedMode(mode=mode, markdown=render_ritual_map(payload))
    if mode == "analyst":
        return RenderedMode(mode=mode, markdown=render_analyst_console(payload))
    raise ValueError(f"Unknown mode: {mode}")

