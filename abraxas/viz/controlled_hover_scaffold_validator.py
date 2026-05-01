from __future__ import annotations

from typing import Any, Dict

from abraxas.viz.controlled_hover_scaffold_models import AUTHORITY


def validate(scaffold: Dict[str, Any]) -> None:
    if scaffold["authority"] != AUTHORITY:
        raise ValueError("authority mismatch")
    if scaffold["status"]["value"] not in {"blocked", "review_ready", "not_computable"}:
        raise ValueError("invalid status")
    if scaffold["status"]["value"] == "review_ready" and scaffold["status"]["blockers"]:
        raise ValueError("review_ready requires empty blockers")
    if scaffold["authority"]["runtime_enabled"] is not False:
        raise ValueError("runtime must remain disabled")
