from __future__ import annotations

import os
from typing import Dict


def detect_capabilities() -> Dict[str, bool]:
    """
    Deterministic capability detection.
    - decodo_available: configured via env vars or config file presence
    - online_allowed: coarse switch so you can force offline-only runs
    """
    online_allowed = os.getenv("ABX_ONLINE_ALLOWED", "1").strip() not in ("0", "false", "False")
    decodo_key = os.getenv("DECODO_API_KEY", "").strip()
    decodo_available = bool(decodo_key) and online_allowed
    return {
        "online_allowed": bool(online_allowed),
        "decodo_available": bool(decodo_available),
    }
