"""PostgreSQL registry for lexicon packs."""

from __future__ import annotations

import json
import os
from typing import List, Optional

from abraxas.lexicon.engine import LexiconEntry, LexiconPack


class PostgresLexiconRegistry:
    """PostgreSQL registry for lexicon packs (optional, requires psycopg2)."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        """
        Initialize registry with database URL.

        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        self._db_url = database_url or os.getenv("DATABASE_URL")
        if not self._db_url:
            raise ValueError("DATABASE_URL not set")
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create lexicon_packs table if it doesn't exist."""
        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS lexicon_packs (
                        domain TEXT NOT NULL,
                        version TEXT NOT NULL,
                        entries JSONB NOT NULL,
                        created_at_utc TEXT NOT NULL,
                        registered_at TIMESTAMP DEFAULT NOW(),
                        PRIMARY KEY (domain, version)
                    )
                    """
                )
                # Index for latest version lookups
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_lexicon_packs_domain_created
                    ON lexicon_packs(domain, created_at_utc DESC)
                    """
                )
            conn.commit()

    def register(self, pack: LexiconPack) -> None:
        """
        Register a lexicon pack.

        Args:
            pack: Lexicon pack to register
        """
        try:
            import psycopg2
            from psycopg2.extras import Json
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        # Serialize entries
        entries_json = [
            {"token": e.token, "weight": float(e.weight), "meta": dict(e.meta)} for e in pack.entries
        ]

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO lexicon_packs (domain, version, entries, created_at_utc)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (domain, version) DO UPDATE SET
                        entries = EXCLUDED.entries,
                        created_at_utc = EXCLUDED.created_at_utc
                    """,
                    (pack.domain, pack.version, Json(entries_json), pack.created_at_utc),
                )
            conn.commit()

    def get(self, domain: str, version: Optional[str]) -> Optional[LexiconPack]:
        """
        Retrieve a lexicon pack by domain and version.

        Args:
            domain: Domain identifier
            version: Version string (None for latest)

        Returns:
            LexiconPack if found, None otherwise
        """
        if version is None:
            return self.latest(domain)

        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT domain, version, entries, created_at_utc
                    FROM lexicon_packs
                    WHERE domain = %s AND version = %s
                    """,
                    (domain, version),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                return self._row_to_pack(row)

    def latest(self, domain: str) -> Optional[LexiconPack]:
        """
        Retrieve the latest version for a domain.

        Args:
            domain: Domain identifier

        Returns:
            Latest LexiconPack if found, None otherwise
        """
        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT domain, version, entries, created_at_utc
                    FROM lexicon_packs
                    WHERE domain = %s
                    ORDER BY created_at_utc DESC
                    LIMIT 1
                    """,
                    (domain,),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                return self._row_to_pack(row)

    def list_versions(self, domain: str) -> List[str]:
        """
        List all versions for a domain.

        Args:
            domain: Domain identifier

        Returns:
            List of version strings
        """
        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT version
                    FROM lexicon_packs
                    WHERE domain = %s
                    ORDER BY created_at_utc DESC
                    """,
                    (domain,),
                )
                rows = cur.fetchall()
                return [row[0] for row in rows]

    @staticmethod
    def _row_to_pack(row: tuple) -> LexiconPack:
        """Convert database row to LexiconPack."""
        domain, version, entries_json, created_at_utc = row
        entries = tuple(
            LexiconEntry(token=e["token"], weight=float(e["weight"]), meta=dict(e.get("meta", {})))
            for e in entries_json
        )
        return LexiconPack(domain=domain, version=version, entries=entries, created_at_utc=created_at_utc)
