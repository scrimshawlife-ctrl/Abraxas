from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import json
import os
import sqlite3
import time
from pathlib import Path

from abx.util.jsonutil import dumps_stable

def default_db_path() -> Path:
    return Path(os.environ.get("ABX_DB", "/opt/aal/abraxas/.aal/state/abx.sqlite")).resolve()

def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    p = db_path or default_db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    return con

def init_db(con: sqlite3.Connection) -> None:
    con.execute("""
    CREATE TABLE IF NOT EXISTS documents (
      id TEXT PRIMARY KEY,
      source TEXT NOT NULL,
      url TEXT NOT NULL,
      fetched_ts INTEGER NOT NULL,
      content_type TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      sha256 TEXT NOT NULL
    );
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_docs_source_ts ON documents(source, fetched_ts);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_docs_url_ts ON documents(url, fetched_ts);")
    con.commit()

def upsert_document(con: sqlite3.Connection, *, doc_id: str, source: str, url: str, content_type: str, payload: Dict[str, Any], sha256: str) -> None:
    ts = int(time.time())
    con.execute("""
    INSERT INTO documents(id, source, url, fetched_ts, content_type, payload_json, sha256)
    VALUES(?,?,?,?,?,?,?)
    ON CONFLICT(id) DO UPDATE SET
      source=excluded.source,
      url=excluded.url,
      fetched_ts=excluded.fetched_ts,
      content_type=excluded.content_type,
      payload_json=excluded.payload_json,
      sha256=excluded.sha256;
    """, (doc_id, source, url, ts, content_type, dumps_stable(payload), sha256))
    con.commit()

def latest_by_source(con: sqlite3.Connection, source: str, limit: int = 50) -> List[Dict[str, Any]]:
    cur = con.execute("SELECT id, url, fetched_ts, content_type, payload_json, sha256 FROM documents WHERE source=? ORDER BY fetched_ts DESC LIMIT ?;", (source, limit))
    out = []
    for row in cur.fetchall():
        out.append({
            "id": row[0],
            "url": row[1],
            "fetched_ts": row[2],
            "content_type": row[3],
            "payload": json.loads(row[4]),
            "sha256": row[5],
        })
    return out
