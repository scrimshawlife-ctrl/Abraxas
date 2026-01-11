from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(os.environ.get("KITE_ROOT", ".aal/kite")).resolve()
DB_PATH = ROOT_DIR / "kite.sqlite3"
FILES_DIR = ROOT_DIR / "files"
EXPORT_DIR = ROOT_DIR / "exports"


def ensure_dirs() -> None:
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    override = os.environ.get("KITE_NOW")
    if override:
        return override
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonicalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\x00", "")
    lines = [" ".join(line.split()).rstrip() for line in normalized.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def normalize_tags(tags: Iterable[str]) -> list[str]:
    cleaned = {tag.strip().lower() for tag in tags if tag.strip()}
    return sorted(cleaned)


def init_db() -> None:
    ensure_dirs()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                content_sha TEXT NOT NULL,
                file_path TEXT,
                text_content TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(items)").fetchall()}
        if "text_content" not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN text_content TEXT")


def insert_item(
    *,
    title: str,
    source_type: str,
    tags: list[str],
    content_sha: str,
    file_path: str | None,
    text_content: str | None,
) -> str:
    init_db()
    item_id = sha256_hex(f"{content_sha}:{source_type}:{title}")
    created_at = now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO items
            (item_id, title, source_type, tags_json, content_sha, file_path, text_content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                title,
                source_type,
                json.dumps(tags, sort_keys=True),
                content_sha,
                file_path,
                text_content,
                created_at,
            ),
        )
    return item_id


def list_items(limit: int = 20) -> list[dict]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT item_id, title, source_type, tags_json, content_sha, file_path, text_content, created_at
            FROM items
            ORDER BY created_at DESC, item_id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "item_id": row[0],
            "title": row[1],
            "source_type": row[2],
            "tags": json.loads(row[3]),
            "content_sha": row[4],
            "file_path": row[5],
            "text_content": row[6],
            "created_at": row[7],
        }
        for row in rows
    ]


def store_file(path: Path, content_sha: str) -> str:
    ensure_dirs()
    dest = FILES_DIR / f"{content_sha}{path.suffix}"
    if not dest.exists():
        dest.write_bytes(path.read_bytes())
    return str(dest)


def export_items(out_dir: Path) -> Path:
    ensure_dirs()
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = list_items(limit=100000)
    items_path = out_dir / "items.jsonl"
    manifest_path = out_dir / "manifest.json"

    with items_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            content = {
                "text": row["text_content"] if row["source_type"] == "text" else None,
                "file_ref": row["file_path"] if row["source_type"] == "file" else None,
            }
            item = {
                "item_id": f"sha256:{row['item_id']}",
                "type": row["source_type"],
                "title": row["title"],
                "tags": row["tags"],
                "created_utc": row["created_at"],
                "content": content,
                "provenance": {
                    "ingested_by": "kite",
                    "raw_sha256": f"sha256:{row['content_sha']}",
                },
            }
            handle.write(json.dumps(item, sort_keys=True) + "\n")

    manifest = {
        "schema": "kite.export.v0",
        "export_id": f"sha256:{sha256_hex(items_path.read_text(encoding='utf-8'))}",
        "created_utc": now_iso(),
        "source": {
            "system": "abraxas",
            "module": "kite",
            "version": "0.1.0",
        },
        "counts": {
            "items": len(rows),
            "files": len([row for row in rows if row["file_path"]]),
        },
        "hashes": {
            "items.jsonl": f"sha256:{sha256_hex(items_path.read_text(encoding='utf-8'))}",
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return items_path
