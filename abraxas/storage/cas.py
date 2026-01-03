"""Content-addressable storage (CAS) for deterministic acquisition artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.canonical import canonical_json, sha256_hex


@dataclass(frozen=True)
class CASRef:
    content_hash: str
    path: str
    bytes: int
    subdir: str
    suffix: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_hash": self.content_hash,
            "path": self.path,
            "bytes": self.bytes,
            "subdir": self.subdir,
            "suffix": self.suffix,
        }


@dataclass(frozen=True)
class CASIndexEntry:
    url: str
    content_hash: str
    path: str
    subdir: str
    suffix: str
    recorded_at_utc: Optional[str] = None
    meta: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "content_hash": self.content_hash,
            "path": self.path,
            "subdir": self.subdir,
            "suffix": self.suffix,
            "recorded_at_utc": self.recorded_at_utc,
            "meta": self.meta or {},
        }


class CASStore:
    def __init__(self, base_dir: str | Path = "data/cas", index_path: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.index_path = Path(index_path) if index_path else self.base_dir / "index.jsonl"

    def _path_for_hash(self, content_hash: str, *, subdir: str, suffix: str) -> Path:
        return self.base_dir / subdir / content_hash[:2] / f"{content_hash}{suffix}"

    def store_bytes(
        self,
        data: bytes,
        *,
        subdir: str = "raw",
        suffix: str = ".bin",
        url: str | None = None,
        recorded_at_utc: str | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> CASRef:
        content_hash = sha256_hex(data)
        path = self._path_for_hash(content_hash, subdir=subdir, suffix=suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(data)

        ref = CASRef(
            content_hash=content_hash,
            path=str(path),
            bytes=len(data),
            subdir=subdir,
            suffix=suffix,
        )
        if url:
            self._append_index(
                CASIndexEntry(
                    url=url,
                    content_hash=content_hash,
                    path=str(path),
                    subdir=subdir,
                    suffix=suffix,
                    recorded_at_utc=recorded_at_utc,
                    meta=meta,
                )
            )
        return ref

    def store_text(
        self,
        text: str,
        *,
        subdir: str = "text",
        suffix: str = ".txt",
        url: str | None = None,
        recorded_at_utc: str | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> CASRef:
        return self.store_bytes(
            text.encode("utf-8"),
            subdir=subdir,
            suffix=suffix,
            url=url,
            recorded_at_utc=recorded_at_utc,
            meta=meta,
        )

    def store_json(
        self,
        payload: Dict[str, Any],
        *,
        subdir: str = "json",
        suffix: str = ".json",
        url: str | None = None,
        recorded_at_utc: str | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> CASRef:
        text = canonical_json(payload)
        return self.store_text(
            text,
            subdir=subdir,
            suffix=suffix,
            url=url,
            recorded_at_utc=recorded_at_utc,
            meta=meta,
        )

    def read_bytes(self, content_hash: str, *, subdir: str = "raw", suffix: str = ".bin") -> bytes:
        path = self._path_for_hash(content_hash, subdir=subdir, suffix=suffix)
        return path.read_bytes()

    def lookup_url(self, url: str) -> CASIndexEntry | None:
        if not self.index_path.exists():
            return None
        latest: CASIndexEntry | None = None
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json_loads(line)
            except ValueError:
                continue
            if payload.get("url") != url:
                continue
            latest = CASIndexEntry(
                url=payload.get("url", url),
                content_hash=payload.get("content_hash", ""),
                path=payload.get("path", ""),
                subdir=payload.get("subdir", "raw"),
                suffix=payload.get("suffix", ".bin"),
                recorded_at_utc=payload.get("recorded_at_utc"),
                meta=payload.get("meta") or {},
            )
        return latest

    def _append_index(self, entry: CASIndexEntry) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = canonical_json(entry.to_dict())
        with self.index_path.open("a", encoding="utf-8") as f:
            f.write(payload + "\n")


def json_loads(text: str) -> Dict[str, Any]:
    import json

    return json.loads(text)
