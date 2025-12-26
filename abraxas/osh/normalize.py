from __future__ import annotations

import json
import re
from typing import Any, Dict

from .types import RawFetchArtifact


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(html: str) -> str:
    return _TAG_RE.sub(" ", html).strip()


def normalize_artifact_to_ingest_packet(art: RawFetchArtifact) -> Dict[str, Any]:
    """
    Minimal v0.1 normalizer:
    - reads raw bytes
    - attempts UTF-8 decode
    - strips HTML tags if looks like HTML
    - returns a deterministic ingest packet structure
    """
    with open(art.body_path, "rb") as f:
        body = f.read()
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:
        text = ""

    content_type = (art.content_type or "").lower()
    if "html" in content_type or "<html" in text.lower():
        text = _strip_html(text)

    packet = {
        "packet_version": "0.1",
        "run_id": art.run_id,
        "artifact_id": art.artifact_id,
        "fetched_ts": art.fetched_ts,
        "url": art.url,
        "content_type": art.content_type,
        "body_sha256": art.body_sha256,
        "trust_class": "online_untrusted",
        "quarantine_default": True,
        "text": text,
        "meta": art.meta,
        "provenance": art.provenance,
    }
    json.dumps(packet, sort_keys=True, ensure_ascii=False)
    return packet
