"""Policy-driven eviction planning."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from abraxas.storage.index import StorageIndex, StorageIndexEntry
from abraxas.storage.lifecycle_schema import LifecycleIR


@dataclass(frozen=True)
class EvictionStep:
    action: str
    path: str
    artifact_type: str
    reason: str
    bytes_expected: int


@dataclass(frozen=True)
class EvictionPlan:
    steps: List[EvictionStep]


def plan_eviction(
    index: StorageIndex,
    lifecycle_ir: LifecycleIR,
    now_utc: str,
    allow_raw_delete: bool = False,
) -> EvictionPlan:
    steps: List[EvictionStep] = []
    order = lifecycle_ir.eviction.order

    entries = sorted(
        index.entries,
        key=lambda entry: (
            order.index(entry.artifact_type) if entry.artifact_type in order else len(order),
            entry.created_at_utc,
            entry.path,
        ),
    )

    for entry in entries:
        policy = lifecycle_ir.artifacts.get(entry.artifact_type)
        if not policy or not policy.retain:
            continue
        if entry.artifact_type == "raw" and not policy.allow_delete:
            continue
        if entry.artifact_type == "raw" and not allow_raw_delete:
            continue
        if policy.delete_after_days is None:
            continue
        age_days = _age_days(entry.created_at_utc, now_utc)
        if age_days < policy.delete_after_days:
            continue
        steps.append(
            EvictionStep(
                action="DELETE",
                path=entry.path,
                artifact_type=entry.artifact_type,
                reason=f"age_days:{age_days}",
                bytes_expected=entry.size_bytes,
            )
        )

    return EvictionPlan(steps=steps)


def _age_days(created_at_utc: str, now_utc: str) -> int:
    created = _parse_utc(created_at_utc)
    now = _parse_utc(now_utc)
    delta = now - created
    return max(0, int(delta.days))


def _parse_utc(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value).replace(tzinfo=None)
