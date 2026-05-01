from __future__ import annotations

from typing import Any, Dict

from abraxas.viz.webgl_viewer_models import AUTHORITY


def validate_authority() -> None:
    if AUTHORITY["static_viewer_spec_generation"] is not True:
        raise ValueError("static_viewer_spec_generation must be true")
    for k, v in AUTHORITY.items():
        if k == "static_viewer_spec_generation":
            continue
        if v is not False:
            raise ValueError(f"{k} must be false")


def validate_viewer_spec(spec: Dict[str, Any], render_bundle: Dict[str, Any]) -> None:
    if spec["viewer"]["runtime_mode"] != "static_no_loop":
        raise ValueError("runtime_mode must be static_no_loop")
    if spec["viewer"]["supports_interaction"] is not False or spec["viewer"]["supports_animation"] is not False:
        raise ValueError("supports flags must be false")
    if any(v is not False for v in spec["interaction_policy"].values()):
        raise ValueError("interaction policy must be all false")

    buffers = render_bundle.get("buffers") or {}
    positions = list(buffers.get("positions") or [])
    colors = list(buffers.get("colors") or [])
    indices = list(buffers.get("indices") or [])

    d = spec["diagnostics"]
    if d["positions_length"] != len(positions) or d["colors_length"] != len(colors) or d["indices_length"] != len(indices):
        raise ValueError("diagnostics length mismatch")
