from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from abraxas.osh.normalize import normalize_artifact_to_ingest_packet
from abraxas.osh.types import RawFetchArtifact


@dataclass(frozen=True)
class SourceRow:
    url: str
    domain: str
    type: str
    title: str
    snippet: str
    summary: str
    text: str
    artifact_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "domain": self.domain,
            "type": self.type,
            "title": self.title,
            "snippet": self.snippet,
            "summary": self.summary,
            "text": self.text,
            "artifact_id": self.artifact_id,
        }


def _read_jsonl(path: str, max_lines: int = 500000) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _domain_from_url(url: str) -> str:
    if "//" in url:
        url = url.split("//", 1)[1]
    return url.split("/", 1)[0].lower()


def load_sources_from_osh(osh_ledger_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _read_jsonl(osh_ledger_path)
    sources: List[Dict[str, Any]] = []
    stats = {"total": 0, "ok": 0, "missing_body": 0}
    for row in rows:
        stats["total"] += 1
        if row.get("status") != "ok":
            continue
        artifact = row.get("artifact")
        if not isinstance(artifact, dict):
            continue
        stats["ok"] += 1
        try:
            art = RawFetchArtifact(**artifact)
        except TypeError:
            continue
        if not art.body_path or not os.path.exists(art.body_path):
            stats["missing_body"] += 1
            continue
        packet = normalize_artifact_to_ingest_packet(art)
        text = str(packet.get("text") or "")
        meta = packet.get("meta") if isinstance(packet.get("meta"), dict) else {}
        title = str(meta.get("title") or "")
        snippet = str(meta.get("snippet") or "")
        summary = str(meta.get("summary") or "")
        url = str(packet.get("url") or art.url or "")
        sources.append(
            SourceRow(
                url=url,
                domain=_domain_from_url(url),
                type="osh",
                title=title,
                snippet=snippet,
                summary=summary,
                text=text,
                artifact_id=art.artifact_id,
            ).to_dict()
        )
    return sources, stats
