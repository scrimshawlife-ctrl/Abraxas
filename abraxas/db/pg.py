"""Postgres connection utilities with optional dependency handling."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional

if TYPE_CHECKING:
    import psycopg

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None  # type: ignore


def pg_dsn(env_key: str = "DATABASE_URL") -> str:
    """
    Retrieve Postgres DSN from environment.

    Args:
        env_key: Environment variable name

    Returns:
        Database connection string

    Raises:
        RuntimeError: If environment variable is missing
    """
    dsn = os.getenv(env_key, "").strip()
    if not dsn:
        raise RuntimeError(f"Missing {env_key}")
    return dsn


@contextmanager
def pg_conn(dsn: Optional[str] = None) -> Iterator[psycopg.Connection]:  # type: ignore
    """
    Context manager for Postgres connections.

    Args:
        dsn: Optional connection string (defaults to DATABASE_URL env var)

    Yields:
        psycopg.Connection

    Raises:
        RuntimeError: If psycopg is not installed
    """
    if psycopg is None:
        raise RuntimeError("psycopg not installed; install psycopg[binary] to enable Postgres registries")
    dsn = dsn or pg_dsn()
    with psycopg.connect(dsn) as conn:
        yield conn
