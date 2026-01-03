"""Content-Addressed Storage (CAS) - Unified implementation.

Combines:
- Performance Drop v1.0: Function-based API with SQLite index and temporal partitioning
- Acquisition CAS: Class-based CASStore with URL tracking
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.storage.hashes import stable_hash_bytes, stable_hash_json
from abraxas.storage.layout import (
    CASNamespace,
    ensure_cas_dirs,
    get_cas_path,
    get_cas_root,
    parse_timestamp_components,
)


# ============================================================================
# Acquisition CAS (Class-based, URL tracking)
# ============================================================================


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
    """Class-based CAS for acquisition with URL tracking."""

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
                payload = json.loads(line)
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


# ============================================================================
# Performance CAS (Function-based, SQLite index, temporal partitioning)
# ============================================================================

CASIndexMode = Literal["sqlite", "json"]
INDEX_MODE: CASIndexMode = "sqlite"


def _get_index_path() -> Path:
    """Get CAS index database path."""
    return get_cas_root() / "index" / "cas_index.db"


def _init_index() -> None:
    """Initialize CAS index database."""
    index_path = _get_index_path()
    ensure_cas_dirs(index_path)

    conn = sqlite3.connect(str(index_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cas_entries (
            hash TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            source_id TEXT NOT NULL,
            year INTEGER,
            month INTEGER,
            ext TEXT,
            created_at_utc TEXT NOT NULL,
            size_bytes INTEGER,
            metadata TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source_id ON cas_entries(source_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_namespace ON cas_entries(namespace)")
    conn.commit()
    conn.close()


def _add_to_index(
    file_hash: str,
    namespace: CASNamespace,
    source_id: str,
    year: int | None,
    month: int | None,
    ext: str,
    size_bytes: int,
    metadata: dict[str, Any],
) -> None:
    """Add entry to CAS index."""
    index_path = _get_index_path()
    conn = sqlite3.connect(str(index_path))

    created_at_utc = metadata.get("created_at_utc") or datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT OR REPLACE INTO cas_entries
        (hash, namespace, source_id, year, month, ext, created_at_utc, size_bytes, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            file_hash,
            namespace,
            source_id,
            year,
            month,
            ext,
            created_at_utc,
            size_bytes,
            json.dumps(metadata),
        ),
    )
    conn.commit()
    conn.close()


def cas_put_bytes(
    namespace: CASNamespace,
    raw_bytes: bytes,
    source_id: str,
    *,
    meta: dict[str, Any] | None = None,
    timestamp_utc: str | None = None,
) -> Path:
    """Store raw bytes in CAS with temporal partitioning."""
    meta = meta or {}
    file_hash = stable_hash_bytes(raw_bytes)

    year, month = None, None
    if timestamp_utc:
        year, month = parse_timestamp_components(timestamp_utc)

    path = get_cas_path(namespace, source_id, file_hash, year=year, month=month, ext="bin")
    ensure_cas_dirs(path)

    with open(path, "wb") as f:
        f.write(raw_bytes)

    _init_index()
    _add_to_index(
        file_hash=file_hash,
        namespace=namespace,
        source_id=source_id,
        year=year,
        month=month,
        ext="bin",
        size_bytes=len(raw_bytes),
        metadata=meta,
    )

    return path


def cas_get_bytes(file_hash: str) -> bytes | None:
    """Retrieve bytes from CAS by hash."""
    index_path = _get_index_path()
    if not index_path.exists():
        return None

    conn = sqlite3.connect(str(index_path))
    cursor = conn.execute(
        "SELECT namespace, source_id, year, month, ext FROM cas_entries WHERE hash = ?",
        (file_hash,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    namespace, source_id, year, month, ext = row
    path = get_cas_path(namespace, source_id, file_hash, year=year, month=month, ext=ext)

    if not path.exists():
        return None

    with open(path, "rb") as f:
        return f.read()


def cas_put_json(
    namespace: CASNamespace,
    obj: dict[str, Any],
    source_id: str,
    *,
    meta: dict[str, Any] | None = None,
    timestamp_utc: str | None = None,
) -> Path:
    """Store JSON object in CAS."""
    json_bytes = stable_hash_json(obj).encode("utf-8")
    return cas_put_bytes(namespace, json_bytes, source_id, meta=meta, timestamp_utc=timestamp_utc)


def cas_get_json(file_hash: str) -> dict[str, Any] | None:
    """Retrieve JSON object from CAS by hash."""
    raw_bytes = cas_get_bytes(file_hash)
    if not raw_bytes:
        return None
    return json.loads(raw_bytes.decode("utf-8"))


def cas_exists(file_hash: str) -> bool:
    """Check if hash exists in CAS."""
    index_path = _get_index_path()
    if not index_path.exists():
        return False

    conn = sqlite3.connect(str(index_path))
    cursor = conn.execute("SELECT 1 FROM cas_entries WHERE hash = ? LIMIT 1", (file_hash,))
    exists = cursor.fetchone() is not None
    conn.close()

    return exists
