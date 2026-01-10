from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import sqlite3
import time
from typing import Any, Dict, Iterable, Optional


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS ars_meta (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ars_candidate (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  term TEXT NOT NULL,
  score REAL NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ars_review (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT "",
  merge_into_id TEXT,
  reviewer TEXT NOT NULL DEFAULT "admin",
  created_at_utc INTEGER NOT NULL,
  FOREIGN KEY(candidate_id) REFERENCES ars_candidate(id)
);

CREATE INDEX IF NOT EXISTS idx_ars_review_candidate ON ars_review(candidate_id);
"""


@dataclass(frozen=True)
class StorePaths:
    db_path: Path


def _now_utc_epoch() -> int:
    return int(time.time())


def _stable_hash(obj: Dict[str, Any]) -> str:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def open_store(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR IGNORE INTO ars_meta(k, v) VALUES(?, ?)",
        ("schema_version", "0.1.0"),
    )
    conn.commit()
    return conn


def upsert_candidates_from_jsonl(conn: sqlite3.Connection, jsonl_path: Path) -> Dict[str, Any]:
    if not jsonl_path.exists():
        raise FileNotFoundError(str(jsonl_path))

    inserted = 0
    skipped = 0
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            cid = obj.get("id") or _stable_hash(obj)
            kind = str(obj.get("kind", "unknown"))
            term = str(obj.get("term", ""))
            score = float(obj.get("score", 0.0))
            payload_json = json.dumps(obj, sort_keys=True, ensure_ascii=False)
            created = int(obj.get("created_at_utc") or _now_utc_epoch())

            cur = conn.execute("SELECT 1 FROM ars_candidate WHERE id = ?", (cid,))
            if cur.fetchone():
                skipped += 1
                continue

            conn.execute(
                """
                INSERT INTO ars_candidate(id, kind, term, score, payload_json, created_at_utc)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (cid, kind, term, score, payload_json, created),
            )
            inserted += 1

    conn.commit()
    return {"inserted": inserted, "skipped": skipped, "source": str(jsonl_path)}


def list_candidates(conn: sqlite3.Connection, limit: int = 50, min_score: float = 0.0) -> Iterable[sqlite3.Row]:
    return conn.execute(
        """
        SELECT c.*
        FROM ars_candidate c
        WHERE c.score >= ?
        ORDER BY c.score DESC, c.created_at_utc DESC, c.term ASC
        LIMIT ?
        """,
        (min_score, limit),
    )


def latest_decision(conn: sqlite3.Connection, candidate_id: str) -> Optional[sqlite3.Row]:
    cur = conn.execute(
        """
        SELECT r.*
        FROM ars_review r
        WHERE r.candidate_id = ?
        ORDER BY r.created_at_utc DESC, r.id DESC
        LIMIT 1
        """,
        (candidate_id,),
    )
    return cur.fetchone()


def set_decision(
    conn: sqlite3.Connection,
    candidate_id: str,
    decision: str,
    note: str = "",
    merge_into_id: Optional[str] = None,
    reviewer: str = "admin",
) -> Dict[str, Any]:
    if decision not in {"approve", "deny", "merge"}:
        raise ValueError(f"invalid decision: {decision}")

    cur = conn.execute("SELECT 1 FROM ars_candidate WHERE id = ?", (candidate_id,))
    if not cur.fetchone():
        raise ValueError(f"unknown candidate id: {candidate_id}")

    if decision == "merge":
        if not merge_into_id:
            raise ValueError("merge requires merge_into_id")
        cur2 = conn.execute("SELECT 1 FROM ars_candidate WHERE id = ?", (merge_into_id,))
        if not cur2.fetchone():
            raise ValueError(f"unknown merge target id: {merge_into_id}")

    conn.execute(
        """
        INSERT INTO ars_review(candidate_id, decision, note, merge_into_id, reviewer, created_at_utc)
        VALUES(?, ?, ?, ?, ?, ?)
        """,
        (candidate_id, decision, note or "", merge_into_id, reviewer, _now_utc_epoch()),
    )
    conn.commit()
    return {
        "candidate_id": candidate_id,
        "decision": decision,
        "note": note,
        "merge_into_id": merge_into_id,
    }


def export_approved_proposals(conn: sqlite3.Connection, out_jsonl: Path) -> Dict[str, Any]:
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    rows = conn.execute(
        """
        SELECT c.id, c.kind, c.term, c.score, c.payload_json
        FROM ars_candidate c
        """
    ).fetchall()

    approved = []
    for row in rows:
        dec = latest_decision(conn, row["id"])
        if not dec or dec["decision"] != "approve":
            continue
        payload = json.loads(row["payload_json"])
        approved.append(
            {
                "proposal_id": row["id"],
                "kind": row["kind"],
                "term": row["term"],
                "score": row["score"],
                "payload": payload,
                "review": {
                    "decision": dec["decision"],
                    "note": dec["note"],
                    "reviewer": dec["reviewer"],
                    "created_at_utc": dec["created_at_utc"],
                },
                "exported_at_utc": _now_utc_epoch(),
            }
        )

    approved.sort(key=lambda x: (-float(x["score"]), x["term"], x["proposal_id"]))

    with out_jsonl.open("w", encoding="utf-8") as handle:
        for obj in approved:
            handle.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")

    return {"approved_exported": len(approved), "out": str(out_jsonl)}
