"""CLI helpers for temporal suite."""

from __future__ import annotations

from abraxas.temporal.timezones import tzdb_version


def tzdb_version_cmd() -> int:
    print(tzdb_version())
    return 0
