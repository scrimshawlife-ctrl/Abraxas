"""Deterministic tier assignment based on age."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from abraxas.storage.lifecycle_schema import LifecycleIR
from abraxas.storage.index import StorageIndexEntry


def assign_tier(entry: StorageIndexEntry, lifecycle_ir: LifecycleIR, now_utc: str) -> str:
    age_days = _age_days(entry.created_at_utc, now_utc)
    tiers = lifecycle_ir.tiers

    deep = tiers.get("deep_archive")
    if deep and deep.min_age_days is not None and age_days >= deep.min_age_days:
        return "deep_archive"

    cold = tiers.get("cold")
    if cold and cold.min_age_days is not None and age_days >= cold.min_age_days:
        return "cold"

    return "hot"


def _age_days(created_at_utc: str, now_utc: str) -> int:
    created = _parse_utc(created_at_utc)
    now = _parse_utc(now_utc)
    delta = now - created
    return max(0, int(delta.days))


def _parse_utc(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value).replace(tzinfo=None)
