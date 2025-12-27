from __future__ import annotations

import re
from typing import Any, Dict, List


SENT_SPLIT = re.compile(r"(?<=[\.\!\?])\s+")
WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    text = text.strip().lower()
    return WS.sub(" ", text)


def _sentences(text: str, max_sent: int = 5) -> List[str]:
    text = text.strip()
    if not text:
        return []
    parts = SENT_SPLIT.split(text)
    out: List[str] = []
    for part in parts:
        part = _norm(part)
        if len(part) < 20:
            continue
        out.append(part)
        if len(out) >= max_sent:
            break
    return out


def extract_claim_items_from_sources(
    sources: List[Dict[str, Any]],
    *,
    run_id: str,
    max_per_source: int = 5,
) -> List[Dict[str, Any]]:
    """
    v0.1 deterministic:
      - pull from title/snippet/summary/text in that order
      - split into up to max_per_source sentences
    """
    items: List[Dict[str, Any]] = []
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or "")
        domain = str(source.get("domain") or "")
        kind = str(source.get("type") or "web")

        text = ""
        for key in ("title", "snippet", "summary", "text"):
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                text = value.strip()
                break
        if not text:
            continue

        sentences = _sentences(text, max_sent=max_per_source)
        for j, sent in enumerate(sentences):
            items.append(
                {
                    "run_id": run_id,
                    "source_i": i,
                    "claim_i": j,
                    "domain": domain,
                    "url": url,
                    "type": kind,
                    "claim": sent,
                }
            )
    return items
