"""Manifest artifact schema for manifest-first acquisition."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


ManifestKind = str


class ManifestProvenance(BaseModel):
    retrieval_method: str
    decodo_used: bool
    reason_code: Optional[str] = None
    raw_hash: str
    parse_hash: str
    cache_path: str


class ManifestArtifact(BaseModel):
    manifest_id: str
    source_id: str
    retrieved_at_utc: str
    kind: ManifestKind
    urls: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: ManifestProvenance

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "source_id": self.source_id,
            "retrieved_at_utc": self.retrieved_at_utc,
            "kind": self.kind,
            "urls": list(self.urls),
            "metadata": _sort_obj(self.metadata),
            "provenance": _sort_obj(self.provenance.model_dump()),
        }

    def manifest_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))

    @classmethod
    def build(
        cls,
        *,
        source_id: str,
        retrieved_at_utc: str,
        kind: ManifestKind,
        urls: List[str],
        metadata: Dict[str, Any],
        provenance: ManifestProvenance,
    ) -> "ManifestArtifact":
        payload = {
            "source_id": source_id,
            "retrieved_at_utc": retrieved_at_utc,
            "kind": kind,
            "urls": urls,
            "metadata": _sort_obj(metadata),
            "provenance": _sort_obj(provenance.model_dump()),
        }
        manifest_id = sha256_hex(canonical_json(payload))
        return cls(
            manifest_id=manifest_id,
            source_id=source_id,
            retrieved_at_utc=retrieved_at_utc,
            kind=kind,
            urls=urls,
            metadata=metadata,
            provenance=provenance,
        )


def _sort_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _sort_obj(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_sort_obj(item) for item in obj]
    return obj
