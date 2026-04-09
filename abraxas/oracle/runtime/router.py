from __future__ import annotations

from typing import Mapping


def route_signal_item_v0(item: Mapping[str, object]) -> dict[str, str]:
    score = float(item.get("score", 0.0))
    confidence = float(item.get("confidence", 0.0))
    if score >= 0.8 and confidence >= 0.6:
        tier = "hot"
    elif score >= 0.5:
        tier = "active"
    else:
        tier = "watch"
    route = f"{item.get('domain','unknown')}.{item.get('subdomain','unknown')}.{tier}"
    return {"tier": tier, "route": route}
