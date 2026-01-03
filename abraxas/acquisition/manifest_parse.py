"""Deterministic manifest parsers."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Iterable, List
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree


URL_RE = re.compile(r"https?://[^\s\"'>]+", re.IGNORECASE)


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    parts = urlsplit(url)
    scheme = parts.scheme.lower() if parts.scheme else parts.scheme
    netloc = parts.netloc.lower() if parts.netloc else parts.netloc
    normalized = urlunsplit((scheme, netloc, parts.path, parts.query, ""))
    return normalized


def _normalize_dedup_sort(urls: Iterable[str]) -> List[str]:
    normalized = [normalize_url(u) for u in urls]
    filtered = [u for u in normalized if u]
    return sorted(set(filtered))


def parse_sitemap_xml(raw: str) -> List[str]:
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return []
    urls = []
    for loc in root.iter():
        if loc.tag.lower().endswith("loc") and loc.text:
            urls.append(loc.text.strip())
    return _normalize_dedup_sort(urls)


def parse_rss(raw: str) -> List[str]:
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return []
    urls = []
    for link in root.iter():
        if link.tag.lower().endswith("link") and link.text:
            urls.append(link.text.strip())
        if link.tag.lower().endswith("link") and "href" in link.attrib:
            urls.append(link.attrib.get("href", "").strip())
    return _normalize_dedup_sort(urls)


class _IndexHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value:
                self.links.append(value)


def parse_index_html(raw: str) -> List[str]:
    parser = _IndexHTMLParser()
    try:
        parser.feed(raw)
    except Exception:
        return []
    return _normalize_dedup_sort(parser.links)


def parse_json_listing(raw: str) -> List[str]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    urls = []
    for value in _walk_json(payload):
        if isinstance(value, str) and URL_RE.search(value):
            urls.append(value)
    return _normalize_dedup_sort(urls)


def _walk_json(payload):
    if isinstance(payload, dict):
        for value in payload.values():
            yield from _walk_json(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from _walk_json(value)
    else:
        yield payload
