from __future__ import annotations

import json
import zlib
from pathlib import Path

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.policy.utp import load_active_utp
from abraxas.storage.compaction import execute_compaction, plan_compaction
from abraxas.storage.index import StorageIndex, StorageIndexEntry
from abraxas.storage.lifecycle_ir import default_lifecycle_ir


def test_compaction_preserves_canonical_hash(tmp_path: Path) -> None:
    payload = {"alpha": 1, "beta": [3, 2, 1]}
    raw = json.dumps(payload, indent=2).encode("utf-8")
    source_path = tmp_path / "parsed.json"
    source_path.write_bytes(raw)

    entry = StorageIndexEntry(
        artifact_type="parsed",
        source_id="TEST",
        created_at_utc="2026-01-01T00:00:00Z",
        size_bytes=source_path.stat().st_size,
        codec="lz4",
        tier="cold",
        path=str(source_path),
        content_hash=sha256_hex(raw),
    )
    index = StorageIndex([entry])
    lifecycle_ir = default_lifecycle_ir("2026-01-10T00:00:00Z", load_active_utp())
    plan = plan_compaction(index, lifecycle_ir, "2026-01-10T00:00:00Z")
    _, events = execute_compaction(plan, lifecycle_ir, max_files=10, max_cpu_ms=1000, max_bytes_written=1_000_000)

    assert events
    compressed_path = Path(events[0]["new_path"])
    decompressed = zlib.decompress(compressed_path.read_bytes())
    assert sha256_hex(decompressed) == sha256_hex(canonical_json(payload).encode("utf-8"))


def test_ledger_rollup_deterministic(tmp_path: Path) -> None:
    lines = [
        {"event": "a", "value": 1},
        {"event": "b", "value": 2},
    ]
    ledger_path = tmp_path / "ledger.jsonl"
    ledger_path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")

    entry = StorageIndexEntry(
        artifact_type="ledger",
        source_id="TEST",
        created_at_utc="2026-01-01T00:00:00Z",
        size_bytes=ledger_path.stat().st_size,
        codec="lz4",
        tier="cold",
        path=str(ledger_path),
        content_hash="hash",
    )
    index = StorageIndex([entry])
    lifecycle_ir = default_lifecycle_ir("2026-01-10T00:00:00Z", load_active_utp())
    plan = plan_compaction(index, lifecycle_ir, "2026-01-10T00:00:00Z")
    _, events = execute_compaction(plan, lifecycle_ir, max_files=10, max_cpu_ms=1000, max_bytes_written=1_000_000)

    compressed_path = Path(events[0]["new_path"])
    decompressed = zlib.decompress(compressed_path.read_bytes())
    canonical = canonical_json(lines).encode("utf-8")
    assert sha256_hex(decompressed) == sha256_hex(canonical)
