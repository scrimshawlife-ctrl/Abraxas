"""PostgreSQL storage for oracle artifacts."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Optional

from abraxas.oracle.runner import OracleArtifact


class PostgresOracleStore:
    """PostgreSQL store for oracle artifacts (optional, requires psycopg2)."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        """
        Initialize store with database URL.

        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        self._db_url = database_url or os.getenv("DATABASE_URL")
        if not self._db_url:
            raise ValueError("DATABASE_URL not set")
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create oracle_artifacts table if it doesn't exist."""
        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS oracle_artifacts (
                        id TEXT PRIMARY KEY,
                        date TEXT NOT NULL,
                        inputs JSONB NOT NULL,
                        output JSONB NOT NULL,
                        signature TEXT NOT NULL,
                        provenance JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                    """
                )
                # Index on date for efficient queries
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_oracle_artifacts_date
                    ON oracle_artifacts(date)
                    """
                )
            conn.commit()

    def upsert(self, artifact: OracleArtifact) -> None:
        """
        Insert or update oracle artifact.

        Args:
            artifact: Oracle artifact to store
        """
        try:
            import psycopg2
            from psycopg2.extras import Json
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO oracle_artifacts (id, date, inputs, output, signature, provenance)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        date = EXCLUDED.date,
                        inputs = EXCLUDED.inputs,
                        output = EXCLUDED.output,
                        signature = EXCLUDED.signature,
                        provenance = EXCLUDED.provenance
                    """,
                    (
                        artifact.id,
                        artifact.date,
                        Json(artifact.inputs),
                        Json(artifact.output),
                        artifact.signature,
                        Json(asdict(artifact.provenance)),
                    ),
                )
            conn.commit()

    def get(self, artifact_id: str) -> Optional[OracleArtifact]:
        """
        Retrieve oracle artifact by ID.

        Args:
            artifact_id: Artifact ID to retrieve

        Returns:
            OracleArtifact if found, None otherwise
        """
        try:
            import psycopg2
            from abraxas.core.provenance import Provenance
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, date, inputs, output, signature, provenance
                    FROM oracle_artifacts
                    WHERE id = %s
                    """,
                    (artifact_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                prov_dict = row[5]
                return OracleArtifact(
                    id=row[0],
                    date=row[1],
                    inputs=row[2],
                    output=row[3],
                    signature=row[4],
                    provenance=Provenance(**prov_dict),
                )

    def get_by_date(self, date: str) -> list[OracleArtifact]:
        """
        Retrieve all oracle artifacts for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            List of OracleArtifacts for the date
        """
        try:
            import psycopg2
            from abraxas.core.provenance import Provenance
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")

        with psycopg2.connect(self._db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, date, inputs, output, signature, provenance
                    FROM oracle_artifacts
                    WHERE date = %s
                    ORDER BY created_at DESC
                    """,
                    (date,),
                )
                rows = cur.fetchall()
                results = []
                for row in rows:
                    prov_dict = row[5]
                    results.append(
                        OracleArtifact(
                            id=row[0],
                            date=row[1],
                            inputs=row[2],
                            output=row[3],
                            signature=row[4],
                            provenance=Provenance(**prov_dict),
                        )
                    )
                return results
