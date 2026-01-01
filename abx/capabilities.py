from __future__ import annotations

import os
from typing import Dict


def detect_capabilities() -> Dict[str, bool]:
    """
    Deterministic capability detection with tiered online sourcing.
    - online_allowed: coarse switch to force offline-only runs
    - decodo_available: Decodo API key configured (tier 1)
    - direct_http_available: Can fetch known URLs directly (tier 2)
    - search_lite_available: DuckDuckGo HTML scraping (tier 3, brittle)
    - rss_available: RSS feed aggregation (tier 4)
    """
    online_allowed = os.getenv("ABX_ONLINE_ALLOWED", "1").strip() not in ("0", "false", "False")
    decodo_key = os.getenv("DECODO_API_KEY", "").strip()
    decodo_available = bool(decodo_key) and online_allowed

    # "Direct HTTP" is available whenever online is allowed.
    direct_http_available = bool(online_allowed)

    # Search-lite: optional; enabled explicitly because it can be brittle.
    # Example: ABX_SEARCH_LITE=1
    search_lite_available = online_allowed and os.getenv("ABX_SEARCH_LITE", "0").strip() in ("1", "true", "True")

    # RSS: optional; enabled if ABX_RSS_FEEDS_PATH exists (json file containing feeds)
    rss_feeds_path = os.getenv("ABX_RSS_FEEDS_PATH", "").strip()
    rss_available = online_allowed and bool(rss_feeds_path) and os.path.exists(rss_feeds_path)

    return {
        "online_allowed": bool(online_allowed),
        "decodo_available": bool(decodo_available),
        "direct_http_available": bool(direct_http_available),
        "search_lite_available": bool(search_lite_available),
        "rss_available": bool(rss_available),
    }
