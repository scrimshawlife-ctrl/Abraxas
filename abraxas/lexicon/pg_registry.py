"""PostgreSQL-backed lexicon registry implementation."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from abraxas.db.pg import pg_conn
from abraxas.lexicon.engine import LexiconEntry, LexiconPack, LexiconRegistry


class PostgresLexiconRegistry(LexiconRegistry):
    """
    Postgres-backed lexicon registry.

    Requires:
    - psycopg[binary] package
    - DATABASE_URL environment variable
    - Table schema: lexicons (id uuid, domain text, version text, entries jsonb, created_at timestamp)
    """

    def __init__(self, *, dsn: Optional[str] = None) -> None:
        """
        Initialize registry.

        Args:
            dsn: Optional Postgres connection string (defaults to DATABASE_URL env var)
        """
        self._dsn = dsn

    def register(self, pack: LexiconPack) -> None:
        """Register a lexicon pack in Postgres."""
        payload = {
            "domain": pack.domain,
            "version": pack.version,
            "created_at_utc": pack.created_at_utc,
            "entries": [
                {"token": e.token, "weight": float(e.weight), "meta": dict(e.meta)} for e in pack.entries
            ],
        }
        with pg_conn(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO lexicons (id, domain, version, entries, created_at)
                    VALUES (gen_random_uuid(), %s, %s, %s::jsonb, now())
                    """,
                    (pack.domain, pack.version, json.dumps(payload)),
                )
            conn.commit()

    def get(self, domain: str, version: Optional[str]) -> Optional[LexiconPack]:
        """Retrieve a lexicon pack by domain and version (None = latest)."""
        if version is None:
            return self.latest(domain)
        with pg_conn(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT entries
                    FROM lexicons
                    WHERE domain=%s AND version=%s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (domain, version),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _pack_from_json(row[0])

    def latest(self, domain: str) -> Optional[LexiconPack]:
        """Retrieve the latest version for a domain."""
        with pg_conn(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT entries
                    FROM lexicons
                    WHERE domain=%s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (domain,),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _pack_from_json(row[0])

    def list_versions(self, domain: str) -> List[str]:
        """List all versions for a domain."""
        with pg_conn(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT version
                    FROM lexicons
                    WHERE domain=%s
                    ORDER BY version ASC
                    """,
                    (domain,),
                )
                rows = cur.fetchall()
        return [r[0] for r in rows]


def _pack_from_json(j: Dict) -> LexiconPack:
    """Reconstruct LexiconPack from JSON representation."""
    entries = tuple(LexiconEntry(e["token"], float(e["weight"]), dict(e.get("meta", {}))) for e in j["entries"])
    return LexiconPack(
        domain=j["domain"],
        version=j["version"],
        entries=entries,
        created_at_utc=j.get("created_at_utc", "1970-01-01T00:00:00Z"),
    )
