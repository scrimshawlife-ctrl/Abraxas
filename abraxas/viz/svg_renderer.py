from __future__ import annotations

import html
from typing import Any, Dict, List, Tuple

from abraxas.viz.svg_models import CANVAS_HEIGHT, CANVAS_WIDTH

NODE_COLORS = {
    "cyan": "#22d3ee",
    "amber": "#f59e0b",
    "violet": "#8b5cf6",
    "blue": "#3b82f6",
    "green": "#22c55e",
    "purple": "#a855f7",
    "orange": "#f97316",
}
DEFAULT_NODE_COLOR = "#94a3b8"
ALERT_COLORS = {"critical": "#ef4444", "warning": "#f59e0b", "info": "#22d3ee"}
ACTION_COLORS = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22d3ee"}


def _node_xy(position: List[float]) -> Tuple[float, float]:
    px = float(position[0]) if len(position) > 0 else 0.0
    py = float(position[1]) if len(position) > 1 else 0.0
    x = (CANVAS_WIDTH / 2) + (px * 260)
    y = (CANVAS_HEIGHT / 2) - (py * 220)
    return x, y


def render_svg(view_packet: Dict[str, Any], view_packet_hash: str) -> str:
    nodes = list(view_packet.get("nodes") or [])
    node_by_id = {str(n.get("node_id")): n for n in nodes}
    edges = list(view_packet.get("edges") or [])
    alerts = list(view_packet.get("alerts") or [])
    actions = list(view_packet.get("actions") or [])

    lines: List[str] = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">')
    lines.append('<rect x="0" y="0" width="1200" height="800" fill="#020617"/>')

    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        edge_type = str(edge.get("edge_type", ""))
        sx, sy = _node_xy(list((node_by_id.get(source) or {}).get("position") or [0, 0]))
        tx, ty = _node_xy(list((node_by_id.get(target) or {}).get("position") or [0, 0]))
        lines.append(
            f'<line id="edge-{html.escape(source)}-{html.escape(target)}-{html.escape(edge_type)}" '
            f'x1="{sx:.2f}" y1="{sy:.2f}" x2="{tx:.2f}" y2="{ty:.2f}" stroke="#334155" stroke-width="2"/>'
        )

    for node in nodes:
        node_id = str(node.get("node_id", ""))
        state = str(node.get("state", "unknown"))
        color = NODE_COLORS.get(str(node.get("color", "")).lower(), DEFAULT_NODE_COLOR)
        x, y = _node_xy(list(node.get("position") or [0, 0]))
        lines.append(f'<g id="node-{html.escape(node_id)}">')
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="28" fill="{color}"/>')
        lines.append(
            f'<text x="{x:.2f}" y="{(y - 34):.2f}" fill="#e2e8f0" font-size="14" text-anchor="middle">{html.escape(node_id)}</text>'
        )
        lines.append(
            f'<text x="{x:.2f}" y="{(y + 5):.2f}" fill="#0f172a" font-size="12" text-anchor="middle">{html.escape(state)}</text>'
        )
        lines.append('</g>')

    lines.append('<g id="alerts-panel">')
    lines.append('<rect x="850" y="20" width="330" height="470" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>')
    for i, alert in enumerate(alerts):
        y = 50 + (i * 30)
        severity = str(alert.get("severity", "info")).lower()
        badge = ALERT_COLORS.get(severity, "#22d3ee")
        message = str(alert.get("message", ""))
        lines.append(f'<rect x="865" y="{y - 14}" width="10" height="10" fill="{badge}"/>')
        lines.append(f'<text x="882" y="{y - 5}" fill="#e2e8f0" font-size="12">{html.escape(message)}</text>')
    lines.append('</g>')

    lines.append('<g id="actions-panel">')
    lines.append('<rect x="20" y="620" width="1160" height="160" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>')
    for i, action in enumerate(actions):
        y = 650 + (i * 26)
        priority = str(action.get("priority", "low")).lower()
        badge = ACTION_COLORS.get(priority, "#22d3ee")
        label = str(action.get("label") or action.get("action") or "")
        lines.append(f'<rect x="40" y="{y - 12}" width="10" height="10" fill="{badge}"/>')
        lines.append(f'<text x="58" y="{y - 3}" fill="#e2e8f0" font-size="12">{html.escape(label)}</text>')
    lines.append('</g>')

    lines.append('<g id="provenance">')
    lines.append(
        f'<text x="20" y="598" fill="#94a3b8" font-size="11">view_packet_hash: {html.escape(view_packet_hash[:12])}</text>'
    )
    lines.append('</g>')
    lines.append('</svg>')
    return "\n".join(lines) + "\n"
