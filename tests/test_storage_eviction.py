from __future__ import annotations

import pytest

from abraxas.policy.utp import load_active_utp
from abraxas.runes.operators.raw_no_delete import apply_raw_no_delete
from abraxas.storage.eviction import plan_eviction
from abraxas.storage.index import StorageIndex, StorageIndexEntry
from abraxas.storage.lifecycle_ir import default_lifecycle_ir


def test_eviction_planning_stable_order() -> None:
    lifecycle_ir = default_lifecycle_ir("2026-02-01T00:00:00Z", load_active_utp())
    entries = [
        StorageIndexEntry(
            artifact_type="packets",
            source_id="S1",
            created_at_utc="2026-01-01T00:00:00Z",
            size_bytes=100,
            codec="zstd",
            tier="cold",
            path="/tmp/packets1",
            content_hash="h1",
        ),
        StorageIndexEntry(
            artifact_type="parsed",
            source_id="S1",
            created_at_utc="2026-01-02T00:00:00Z",
            size_bytes=100,
            codec="zstd",
            tier="cold",
            path="/tmp/parsed1",
            content_hash="h2",
        ),
    ]
    index = StorageIndex(entries)
    plan = plan_eviction(index, lifecycle_ir, "2026-02-01T00:00:00Z", allow_raw_delete=False)
    assert [step.path for step in plan.steps] == ["/tmp/parsed1", "/tmp/packets1"]


def test_raw_delete_guard_enforced() -> None:
    steps = [
        {
            "action": "DELETE",
            "path": "/tmp/raw",
            "artifact_type": "raw",
            "reason": "age_days:40",
            "bytes_expected": 10,
        }
    ]
    with pytest.raises(ValueError):
        apply_raw_no_delete(steps=steps, allow_raw_delete=False)
