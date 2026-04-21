from __future__ import annotations

from typing import Any, Dict


def normalize_online_capability(
    capability: Dict[str, Any] | None,
    *,
    default_online_allowed: bool,
    default_decodo_available: bool,
) -> Dict[str, bool]:
    raw = capability if isinstance(capability, dict) else {}
    online_allowed = bool(raw.get("online_allowed", default_online_allowed))
    decodo_available = bool(raw.get("decodo_available", default_decodo_available))
    if not online_allowed:
        decodo_available = False
    return {
        "online_allowed": online_allowed,
        "decodo_available": decodo_available,
    }
