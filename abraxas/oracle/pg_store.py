"""PostgreSQL-backed oracle artifact storage."""

from __future__ import annotations

import json
from typing import Optional

from abraxas.db.pg import pg_conn
from abraxas.oracle.runner import OracleArtifact


class PostgresOracleStore:
    """
    Postgres-backed oracle artifact store.

    Requires:
    - psycopg[binary] package
    - DATABASE_URL environment variable
    - Table schema: oracles (id uuid, date date, inputs jsonb, output jsonb, signature text, created_at timestamp)
    """

    def __init__(self, *, dsn: Optional[str] = None) -> None:
        """
        Initialize store.

        Args:
            dsn: Optional Postgres connection string (defaults to DATABASE_URL env var)
        """
        self._dsn = dsn

    def upsert(self, art: OracleArtifact) -> None:
        """
        Upsert oracle artifact to Postgres.

        Uses ON CONFLICT to update existing artifacts for the same date.

        Args:
            art: OracleArtifact to store
        """
        with pg_conn(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO oracles (id, date, inputs, output, signature, created_at)
                    VALUES (%s::uuid, %s::date, %s::jsonb, %s::jsonb, %s, now())
                    ON CONFLICT (date)
                    DO UPDATE SET
                        inputs=EXCLUDED.inputs,
                        output=EXCLUDED.output,
                        signature=EXCLUDED.signature
                    """,
                    (
                        art.id,
                        art.date,
                        json.dumps(art.inputs),
                        json.dumps(art.output),
                        art.signature,
                    ),
                )
            conn.commit()
