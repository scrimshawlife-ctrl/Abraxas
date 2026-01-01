from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clamp(n: int, a: int, b: int) -> int:
    return max(a, min(b, n))


def _http_get(url: str, timeout: int = 12, headers: Optional[Dict[str, str]] = None) -> str:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "abx/online_sourcing (direct_http)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def direct_http_fetch(urls: List[str], max_urls: int = 12) -> Dict[str, Any]:
    out = []
    for u in urls[:_clamp(max_urls, 1, 50)]:
        uu = (u or "").strip()
        if not uu:
            continue
        out.append({"url": uu, "provider": "direct_http", "ts": _utc_now_iso(), "notes": "URL provided directly; fetch optional downstream."})
    return {"provider": "direct_http", "results": out}


def search_lite_duckduckgo(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Minimal HTML scrape of DuckDuckGo's html endpoint.
    Brittle by nature; disabled unless ABX_SEARCH_LITE=1.
    Returns URLs only.
    """
    q = (query or "").strip()
    if not q:
        return {"provider": "search_lite", "results": [], "error": "empty_query"}
    params = {"q": q}
    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode(params)
    html = _http_get(url, timeout=12, headers={"User-Agent": "abx/online_sourcing (search_lite)"})

    # Extract result links: look for 'result__a' anchors and hrefs
    links = re.findall(r'class="result__a"\s+href="([^"]+)"', html)
    out = []
    for href in links[:_clamp(max_results, 1, 30)]:
        u = href.strip()
        if u:
            out.append({"url": u, "provider": "search_lite", "ts": _utc_now_iso(), "notes": "Search-lite candidate URL."})
    return {"provider": "search_lite", "results": out, "query": q}


def rss_from_feeds(term: str, feeds_path: str, max_results: int = 12) -> Dict[str, Any]:
    """
    RSS feed list is a JSON file: {"feeds":[{"url":"...","tags":["tech","ai"]}, ...]}
    This function only returns feed URLs to fetch downstream (parsing RSS properly can be added later).
    """
    tp = (term or "").strip().lower()
    if not feeds_path or not os.path.exists(feeds_path):
        return {"provider": "rss", "results": [], "error": "feeds_path_missing"}
    try:
        with open(feeds_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return {"provider": "rss", "results": [], "error": "feeds_path_unreadable"}

    feeds = obj.get("feeds") if isinstance(obj, dict) else None
    if not isinstance(feeds, list):
        return {"provider": "rss", "results": [], "error": "feeds_invalid"}

    # naive: return all feeds; downstream resolver can filter by tag/domain later
    out = []
    for fd in feeds:
        if not isinstance(fd, dict):
            continue
        u = str(fd.get("url") or "").strip()
        if u:
            out.append({"url": u, "provider": "rss", "ts": _utc_now_iso(), "notes": "RSS feed URL (downstream parser required)."})
        if len(out) >= _clamp(max_results, 1, 50):
            break
    return {"provider": "rss", "results": out}


def route_online_sources(
    *,
    term: str,
    query: str,
    known_urls: List[str],
    caps: Dict[str, bool],
) -> Dict[str, Any]:
    """
    Deterministic provider fallback:
    - if Decodo available: return a 'decodo' request stub (WO-78 will execute)
    - else: direct_http for known URLs
    - else: search_lite (if enabled)
    - else: rss (if enabled)
    """
    if caps.get("decodo_available", False):
        return {
            "provider": "decodo",
            "request": {
                "term": term,
                "query": query,
                "notes": "Decodo stub; executed in WO-78 operator.",
            },
            "results": [],
        }

    # Non-Decodo online fallback chain
    if caps.get("direct_http_available", False) and known_urls:
        return direct_http_fetch(known_urls)

    if caps.get("search_lite_available", False):
        return search_lite_duckduckgo(query=query, max_results=10)

    if caps.get("rss_available", False):
        feeds_path = os.getenv("ABX_RSS_FEEDS_PATH", "").strip()
        return rss_from_feeds(term=term, feeds_path=feeds_path, max_results=12)

    return {"provider": "none", "results": [], "error": "no_online_provider_available"}
