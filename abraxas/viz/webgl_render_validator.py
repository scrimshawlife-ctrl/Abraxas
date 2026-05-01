from __future__ import annotations

import math
from typing import Any, Dict, Iterable

from abraxas.viz.webgl_render_models import AUTHORITY


def validate_authority() -> None:
    if AUTHORITY["webgl_render_bundle_generation"] is not True:
        raise ValueError("webgl_render_bundle_generation must be true")
    for k, v in AUTHORITY.items():
        if k == "webgl_render_bundle_generation":
            continue
        if v is not False:
            raise ValueError(f"{k} must be false")


def validate_no_nan(values: Iterable[float]) -> None:
    for x in values:
        if isinstance(x, float) and math.isnan(x):
            raise ValueError("NaN value detected")


def validate_scene(scene_spec: Dict[str, Any]) -> None:
    if not isinstance(scene_spec, dict):
        raise TypeError("scene spec must be object")
