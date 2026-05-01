from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.svg_models import AUTHORITY_FLAGS, CANVAS_HEIGHT, CANVAS_WIDTH, extract_counts, extract_view_id, manifest_payload
from abraxas.viz.svg_renderer import render_svg
from abraxas.viz.svg_validator import validate_render_authority, validate_view_packet


@dataclass(frozen=True)
class RenderOutputs:
    svg: str
    manifest: Dict[str, Any]


def build_outputs(view_packet: Dict[str, Any], svg_path: str) -> RenderOutputs:
    validate_render_authority()
    validate_view_packet(view_packet)

    view_packet_hash = sha256_hex(canonical_json(view_packet))
    svg = render_svg(view_packet, view_packet_hash)
    svg_hash = sha256(svg.encode("utf-8")).hexdigest()

    counts = extract_counts(view_packet)
    view_id = extract_view_id(view_packet)
    render_material = {
        "view_id": view_id,
        "svg_hash": svg_hash,
        "view_packet_hash": view_packet_hash,
        "dimensions": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT},
        "counts": counts.to_dict(),
        "authority": dict(AUTHORITY_FLAGS),
    }
    render_id = sha256_hex(canonical_json(render_material))
    manifest = manifest_payload(
        render_id=render_id,
        view_id=view_id,
        svg_hash=svg_hash,
        view_packet_hash=view_packet_hash,
        counts=counts,
        svg_path=svg_path,
    )
    return RenderOutputs(svg=svg, manifest=manifest)


def run_renderer(view_packet_path: Path, svg_out: Path, manifest_out: Path) -> RenderOutputs:
    view_packet = json.loads(view_packet_path.read_text(encoding="utf-8"))
    outputs = build_outputs(view_packet, str(svg_out))

    svg_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    svg_out.write_text(outputs.svg, encoding="utf-8")
    manifest_out.write_text(canonical_json(outputs.manifest), encoding="utf-8")
    return outputs
