"""Linguistic packet schema for text ingestion."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.linguistics.normalize import stable_lang


class TextItem(BaseModel):
    item_id: str
    ts_utc: str
    text: str
    lang: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_hash: str


class LinguisticPacket(BaseModel):
    source_id: str
    observed_at_utc: str
    window_start_utc: Optional[str]
    window_end_utc: Optional[str]
    items: List[TextItem] = Field(default_factory=list)

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload["items"] = [item.model_dump() for item in self.items]
        return payload

    def packet_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))


def build_text_item(ts_utc: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> TextItem:
    metadata = metadata or {}
    raw_hash = sha256_hex(text)
    lang = metadata.get("lang") or stable_lang(text)
    item_id = sha256_hex(canonical_json({"ts_utc": ts_utc, "text": text, "meta": metadata}))
    return TextItem(
        item_id=item_id,
        ts_utc=ts_utc,
        text=text,
        lang=lang,
        metadata=metadata,
        raw_hash=raw_hash,
    )
