from __future__ import annotations

import json
from pathlib import Path

from abraxas.policy.utp import load_active_utp
from abraxas.storage.compaction import plan_compaction
from abraxas.storage.index import StorageIndex, StorageIndexEntry
from abraxas.storage.lifecycle_ir import default_lifecycle_ir
from abraxas.storage.lifecycle_run import execute_lifecycle, plan_lifecycle


def test_execute_respects_max_files(tmp_path: Path) -> None:
    lifecycle_ir = default_lifecycle_ir("2026-02-01T00:00:00Z", load_active_utp())
    files = []
    entries = []
    for idx in range(2):
        path = tmp_path / f"parsed_{idx}.json"
        payload = {"idx": idx, "data": list(range(100))}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        files.append(path)
        entries.append(
            StorageIndexEntry(
                artifact_type="parsed",
                source_id="TEST",
                created_at_utc="2026-01-01T00:00:00Z",
                size_bytes=path.stat().st_size,
                codec="lz4",
                tier="cold",
                path=str(path),
                content_hash=str(idx),
            )
        )
    index = StorageIndex(entries)
    plan = plan_lifecycle(index, "2026-02-01T00:00:00Z", lifecycle_ir)
    result = execute_lifecycle(plan, lifecycle_ir, max_files=1, max_cpu_ms=10000, max_bytes_written=1_000_000)
    assert len(result.compaction_events) <= 1
